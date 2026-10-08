import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from sideword.storage import Store
from sideword.ui.app import Desk
from sideword.ui.text import clip, width, wrap
from sideword.vocabulary import Library

BOOKS = Library().catalog
load_book = Library().load


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "progress.sqlite3"
        self.store = Store(self.path)
        self.words = {"cancel": {"name": "cancel", "key": "cancel", "trans": ["取消"]}}

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def test_full_book_defaults_upgrade_only_once(self):
        self.store.set_setting("learning_book", "sample")
        self.store.set_setting("autoplay", "0")
        self.store.apply_full_book_defaults()
        self.assertEqual(
            self.store.setting("learning_book"),
            "ielts" if "ielts" in BOOKS else "sample",
        )
        self.assertEqual(self.store.setting("accent"), "uk")
        self.assertEqual(self.store.setting("autoplay"), "1")
        self.store.set_setting("autoplay", "0")
        self.store.set_setting("learning_book", "bible")
        self.store.apply_full_book_defaults()
        self.assertEqual(self.store.setting("autoplay"), "0")
        self.assertEqual(self.store.setting("learning_book"), "bible")

    def multiword_desk(self):
        desk = Desk.__new__(Desk)
        desk.s = Mock()
        desk.s.getmaxyx.return_value = (24, 80)
        desk.store, desk.book = self.store, "sample"
        desk.words = load_book("sample")
        desk.study_state = self.store.study("sample", desk.words)
        desk.page_size, desk.word_detail = 5, False
        desk.speaker, desk.accent = Mock(), 0
        desk.autoplay, desk.accent_name, desk.slow = True, "uk", False
        desk.message, desk.card_scroll = "", 0
        return desk

    def test_multiword_selection_audio_grading_and_page_boundaries(self):
        desk = self.multiword_desk()
        desk.learning_key("j")
        self.assertEqual(desk.study_state["index"], 1)
        word = desk.study_word()
        desk.speaker.play.assert_called_with(word["name"], "uk", False)
        desk.learning_key("2")
        self.assertEqual(self.store.learned("sample")[word["key"]]["familiarity"], "familiar")
        self.assertNotIn(word["key"], desk.study_state["queue"])
        desk.learning_key("l")
        self.assertEqual(desk.study_state["index"], 5)
        desk.learning_key("h")
        self.assertEqual(desk.study_state["index"], 0)
        desk.learning_key("h")
        self.assertEqual(desk.study_state["index"], 0)
        desk.study_state["index"] = 28
        desk.learning_key("l")
        desk.learning_key("j")
        self.assertEqual(desk.study_state["index"], 28)

    def test_multiword_details_configuration_and_review_isolation(self):
        desk = self.multiword_desk()
        self.assertEqual(desk.effective_page_size(), 5)
        desk.learning_key("\n")
        self.assertTrue(desk.word_detail)
        self.assertEqual(desk.effective_page_size(), 1)
        desk.learning_key("\n")
        self.assertFalse(desk.word_detail)
        self.assertEqual(desk.study_state["index"], 0)
        desk.learning_key("m")
        for key in "10\n":
            desk.learning_key(key)
        self.assertEqual(self.store.setting("page_size"), "10")
        desk.s.getmaxyx.return_value = (15, 42)
        self.assertEqual(desk.effective_page_size(), 10)
        desk.study_state["mode"] = "review"
        self.assertEqual(desk.effective_page_size(), 1)

    def test_remembered_hidden_but_due_and_forgotten_returns(self):
        words = load_book("sample")
        state = self.store.study("sample", words)
        word = state["queue"][0]
        self.store.rate_word("sample", word, True, now=100)
        self.assertNotIn(word, self.store.study("sample", words)["queue"])
        self.assertIn(word, self.store.due_words("sample", words, now=86500))
        self.store.rate_word("sample", word, False, now=86500)
        self.assertIn(word, self.store.study("sample", words)["queue"])

    def test_arbitrary_page_input_and_scroll(self):
        desk = self.multiword_desk()
        desk.page = "learn"
        desk.learning_key("m")
        for key in "0\n":
            desk.key(key)
        self.assertEqual(desk.page_size, 5)
        for key in "10\n":
            desk.key(key)
        self.assertEqual(desk.page_size, 10)
        desk.put = Mock()
        desk.study_state["index"] = 9
        desk.render_learning()
        output = "\n".join(str(call.args[1]) for call in desk.put.call_args_list)
        self.assertIn(desk.study_word()["name"], output)
        desk.learning_key("l")
        self.assertEqual(desk.study_state["index"], 10)
        desk.learning_key("m")
        desk.key("\x1b")
        self.assertIsNone(desk.page_size_input)
        self.assertEqual(desk.page_size, 10)

    def test_multiword_render_shows_five_words_without_marking_them_learned(self):
        desk = self.multiword_desk()
        desk.put = Mock()
        desk.render_learning()
        output = "\n".join(str(call.args[1]) for call in desk.put.call_args_list)
        for key in desk.study_state["queue"][:5]:
            self.assertIn(desk.words[key]["name"], output)
        self.assertEqual(self.store.learned("sample"), {})

    def test_random_learning_is_complete_and_survives_restart(self):
        words = load_book("sample")
        with patch("sideword.storage.random.shuffle", side_effect=lambda q: q.reverse()) as shuffle:
            state = self.store.study("ielts", words)
            shuffle.assert_called_once()
        self.assertEqual(state["queue"], list(reversed(words)))
        self.assertEqual(len(set(state["queue"])), len(words))
        state["index"] = 7
        self.store.save_study("ielts", state)
        self.store.db.close()
        self.store = Store(self.path)
        with patch("sideword.storage.random.shuffle") as shuffle:
            self.assertEqual(self.store.study("ielts", words), state)
            shuffle.assert_not_called()

    def test_legacy_order_upgrade_preserves_position(self):
        words = dict.fromkeys(["a", "b", "c", "d", "e"])
        self.store.save_study("ielts", {"queue": list(words), "index": 1, "mode": "all"})
        with patch("sideword.storage.random.shuffle", side_effect=lambda q: q.reverse()):
            state = self.store.study("ielts", words)
        self.assertEqual(state["index"], 1)
        self.assertEqual(state["queue"], ["a", "b", "e", "d", "c"])
        self.assertEqual(self.store.study("ielts", words), state)

    def test_wrong_answer_survives_restart_and_is_due_in_ten_minutes(self):
        session = self.store.start("ielts", self.words, now=100)
        self.store.grade("ielts", session, self.words["cancel"], "cancle", now=100)
        self.store.db.close()
        self.store = Store(self.path)
        restored = self.store.session("ielts")
        self.assertEqual(restored["phase"], "feedback")
        self.assertEqual(restored["typed"], "cancle")
        self.assertEqual(self.store.stats("ielts", self.words, now=699)["due"], 0)
        self.assertEqual(self.store.stats("ielts", self.words, now=700)["due"], 1)
        self.store.grade("ielts", restored, self.words["cancel"], "cancel", now=800)
        self.assertEqual(self.store.progress("ielts")["cancel"]["attempts"], 1)

    def test_correct_progress_and_hint_never_counts_as_independent_recall(self):
        state = self.store.start("ielts", self.words, now=100)
        self.store.grade("ielts", state, self.words["cancel"], " CANCEL ", now=100)
        self.assertEqual(self.store.progress("ielts")["cancel"]["due"], 86500)
        state = self.store.start("ielts", self.words, now=86501)
        state["assisted"] = True
        self.store.grade("ielts", state, self.words["cancel"], "cancel", now=86501)
        self.assertEqual(state["correct"], 0)
        self.assertEqual(self.store.progress("ielts")["cancel"]["level"], 0)

    def test_star_does_not_consume_new_word_and_books_are_isolated(self):
        self.store.star("ielts", "cancel")
        self.assertEqual(self.store.stats("ielts", self.words)["new"], 1)
        self.assertEqual(self.store.start("ielts", self.words, "starred")["queue"], ["cancel"])
        self.assertEqual(self.store.start("bible", self.words, "starred")["queue"], [])

    def test_typing_and_correction_state_machine(self):
        desk = Desk.__new__(Desk)
        desk.store, desk.words, desk.book = self.store, self.words, "ielts"
        desk.message = ""
        desk.state = self.store.start("ielts", self.words)
        for key in "cancle\n":
            desk.practice_key(key)
        self.assertEqual(desk.state["phase"], "feedback")
        desk.practice_key("\n")
        self.assertEqual(desk.state["index"], 0)
        for key in "cancel\n":
            desk.practice_key(key)
        self.assertFalse(desk.active())
        self.assertEqual(self.store.progress("ielts")["cancel"]["attempts"], 1)

    def test_unicode_clipping(self):
        self.assertEqual(clip("取消 abc", 5), "取消 ")
        self.assertLessEqual(width(clip("中文音标 æŋə", 8)), 8)

    def test_actual_books_have_required_content(self):
        self.assertEqual(len(load_book("sample")), 30)
        if "ielts" in BOOKS:
            self.assertEqual(len(load_book("ielts")), 3575)
        if "bible" in BOOKS:
            self.assertGreater(len(load_book("bible")), 3500)

    def test_learning_does_not_change_spelling_results(self):
        self.store.view_word("ielts", "cancel", "unfamiliar")
        self.assertEqual(self.store.stats("ielts", self.words)["seen"], 0)
        self.assertEqual(self.store.study("ielts", self.words, "unfamiliar")["queue"], ["cancel"])
        self.store.view_word("ielts", "cancel", "familiar")
        self.assertEqual(self.store.study("ielts", self.words, "unfamiliar")["queue"], [])
        self.assertEqual(self.store.learned("ielts")["cancel"]["familiarity"], "familiar")

    def test_remembered_words_remain_scheduled_and_intervals_expand(self):
        first = self.store.rate_word("ielts", "cancel", True, now=1000)
        self.assertEqual(first["due"], 87400)
        self.assertEqual(self.store.due_words("ielts", self.words, now=87399), [])
        self.assertEqual(self.store.due_words("ielts", self.words, now=87400), ["cancel"])
        second = self.store.rate_word("ielts", "cancel", True, now=87400)
        self.assertEqual(second["due"], 87400 + 3 * 86400)
        forgotten = self.store.rate_word("ielts", "cancel", False, now=90000)
        self.assertEqual(forgotten["due"], 90600)
        self.assertEqual(forgotten["stage"], 0)
        self.assertEqual(forgotten["lapses"], 1)

    def test_early_review_does_not_inflate_memory_stage(self):
        self.store.rate_word("ielts", "cancel", True, now=1000)
        early = self.store.rate_word("ielts", "cancel", True, now=1001)
        self.assertEqual(early["stage"], 1)
        self.assertEqual(early["due"], 87400)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM review_log").fetchone()[0], 1)

    def test_due_queue_persists_and_browsing_does_not_delay_it(self):
        self.store.rate_word("ielts", "cancel", False, now=1000)
        self.store.view_word("ielts", "cancel")
        self.store.db.close()
        self.store = Store(self.path)
        self.assertEqual(
            self.store.study("ielts", self.words, "review", now=1600)["queue"],
            ["cancel"],
        )
        self.assertEqual(self.store.study("bible", self.words, "review", now=1600)["queue"], [])

    def test_review_requires_reveal_before_rating_and_then_advances(self):
        self.store.rate_word("ielts", "cancel", False, now=0)
        desk = Desk.__new__(Desk)
        desk.store, desk.book, desk.words = self.store, "ielts", self.words
        desk.speaker = Mock()
        desk.autoplay = False
        desk.open_study("review")
        self.assertFalse(desk.review_revealed)
        before = self.store.learned("ielts")["cancel"]["due"]
        desk.learning_key("2")
        self.assertTrue(desk.review_revealed)
        self.assertEqual(self.store.learned("ielts")["cancel"]["due"], before)
        desk.learning_key("2")
        self.assertIsNone(desk.study_word())
        self.assertEqual(self.store.learned("ielts")["cancel"]["stage"], 1)
        self.assertEqual(self.store.due_words("ielts", self.words), [])

    def test_study_position_survives_restart_and_lookup(self):
        words = load_book("sample")
        state = self.store.study("sample", words)
        state["index"] = 5
        self.store.save_study("sample", state)
        self.store.save_study("sample", {"queue": ["cancel"], "index": 0, "mode": "lookup"})
        self.store.db.close()
        self.store = Store(self.path)
        self.assertEqual(self.store.study("sample", words)["index"], 5)
        self.assertEqual(self.store.study("ielts", self.words)["index"], 0)

    def test_samples_have_bilingual_examples_and_wrapping_preserves_words(self):
        words = load_book("sample")
        self.assertEqual(len(words), 30)
        for word in words.values():
            self.assertTrue(word["example"]["en"])
            self.assertTrue(word["example"]["zh"])
            self.assertTrue(word["example"]["phrase"])
        self.assertEqual(
            wrap("We need to prepare for exams.", 18),
            ["We need to prepare", "for exams."],
        )


if __name__ == "__main__":
    unittest.main()
