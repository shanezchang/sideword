import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from speech import Speaker, has_audio


class SpeechTests(unittest.TestCase):
    def test_empty_audio_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.aiff"
            path.write_bytes(
                b"FORM"
                + struct.pack(">I", 20)
                + b"AIFFSSND"
                + struct.pack(">I", 8)
                + b"\0" * 8
            )
            self.assertFalse(has_audio(path))
            path.write_bytes(
                b"FORM"
                + struct.pack(">I", 24)
                + b"AIFFSSND"
                + struct.pack(">I", 12)
                + b"\0" * 12
            )
            self.assertTrue(has_audio(path))

    def test_cancelled_request_never_starts_process(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("speech.shutil.which", return_value=None),
        ):
            speaker = Speaker(tmp)
            token = speaker.generation
            speaker.stop()
            with patch("speech.subprocess.Popen") as popen:
                self.assertIsNone(speaker._run(["say", "hello"], token))
                popen.assert_not_called()

    def test_unavailable_audio_has_visible_message(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("speech.shutil.which", return_value=None),
        ):
            speaker = Speaker(tmp)
            speaker.play("hello")
            self.assertIn("未找到", speaker.status)


if __name__ == "__main__":
    unittest.main()
