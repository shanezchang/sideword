import json

import pytest

from sideword.vocabulary import Library, VocabularyError, parse_words


def test_bundled_sample_has_complete_content():
    words = Library().load("sample")
    assert len(words) == 30
    assert all(word["ukphone"] and word["example"] for word in words.values())


@pytest.mark.parametrize(
    "rows",
    [
        None,
        {},
        [],
        [None],
        [{"name": ""}],
        [{"name": "word", "trans": "词"}],
        [{"name": "word", "trans": [3]}],
        [{"name": "word", "trans": ["词"], "ukphone": 3}],
        [{"name": "word", "trans": ["词"], "example": {}}],
    ],
)
def test_malformed_books_have_actionable_errors(rows):
    with pytest.raises(VocabularyError, match="bad-book"):
        parse_words(rows, "bad-book")


def test_duplicate_words_merge_and_preserve_original_example():
    example = {"en": "A word.", "zh": "一个词。", "phrase": "a word"}
    words = parse_words(
        [
            {"name": " Word ", "trans": ["词"], "example": example},
            {"name": "word", "trans": ["词", "消息"]},
        ],
        "test",
    )
    assert list(words) == ["word"]
    assert words["word"]["trans"] == ["词", "消息"]
    assert words["word"]["example"] == example


def test_custom_books_are_discovered_outside_installation(tmp_path):
    (tmp_path / "work.json").write_text(json.dumps([{"name": "ship", "trans": ["交付"]}]))
    library = Library(tmp_path)
    assert set(library.catalog) == {"sample", "work"}
    assert library.load("work")["ship"]["example"] is None


def test_legacy_filenames_keep_progress_identifiers(tmp_path):
    (tmp_path / "IELTS_3_T.json").write_text('[{"name":"word","trans":["词"]}]')
    assert "ielts" in Library(tmp_path).catalog


def test_reserved_book_cannot_shadow_bundled_content(tmp_path):
    (tmp_path / "sample.json").write_text("[]")
    with pytest.raises(VocabularyError, match="sample"):
        Library(tmp_path)


def test_bad_json_reports_book_name(tmp_path):
    (tmp_path / "broken.json").write_text("{")
    with pytest.raises(VocabularyError, match="broken"):
        Library(tmp_path).load("broken")


def test_unknown_book_is_explicit():
    with pytest.raises(VocabularyError, match="missing"):
        Library().load("missing")
