"""Non-blocking macOS speech with local cache and immediate cancellation."""

import hashlib
import shutil
import struct
import subprocess
import threading
import uuid
from pathlib import Path


def has_audio(path):
    """An empty AIFF can be produced even when say exits zero."""
    try:
        with open(path, "rb") as file:
            header = file.read(12)
            if header[:4] != b"FORM" or header[8:] not in (b"AIFF", b"AIFC"):
                return False
            while True:
                chunk = file.read(8)
                if len(chunk) < 8:
                    return False
                size = struct.unpack(">I", chunk[4:])[0]
                if chunk[:4] == b"SSND":
                    return size > 8 and len(file.read(size)) == size
                file.seek(size + size % 2, 1)
    except OSError:
        return False


class Speaker:
    def __init__(self, cache):
        self.cache = Path(cache)
        self.lock = threading.Lock()
        self.process = None
        self.generation = 0
        self.status = ""
        self.detail = ""
        self.available = bool(shutil.which("say") and shutil.which("afplay"))
        self.voices = {"uk": "Daniel", "us": "Samantha"}
        if self.available:
            try:
                listing = subprocess.run(
                    ["say", "-v", "?"], capture_output=True, text=True, timeout=5
                )
                for accent, name, region in [
                    ("uk", "Daniel", "en_GB"),
                    ("us", "Samantha", "en_US"),
                ]:
                    for line in listing.stdout.splitlines():
                        if line.startswith(name) and region in line:
                            self.voices[accent] = line.split(region)[0].strip()
                            break
            except (OSError, subprocess.TimeoutExpired):
                pass

    def stop(self):
        with self.lock:
            self.generation += 1
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
            self.status = ""

    def play(self, text, accent="uk", slow=False):
        self.stop()
        self.detail = ""
        if not self.available:
            self.status = "本机未找到语音服务（需 macOS say / afplay）"
            return
        with self.lock:
            token = self.generation
            self.status = "正在准备发音…"
        threading.Thread(
            target=self._speak, args=(text, accent, slow, token), daemon=True
        ).start()

    def _run(self, args, token, text=None):
        with self.lock:
            if token != self.generation:
                return None
            process = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self.process = process
        try:
            _, error = process.communicate(text.encode() if text else None, timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            _, error = process.communicate()
            raise RuntimeError("语音服务超时")
        with self.lock:
            if self.process is process:
                self.process = None
            if token != self.generation:
                return None
        if process.returncode or error:
            raise RuntimeError(
                error.decode(errors="replace").strip() or "语音服务未完成"
            )
        return True

    def _speak(self, text, accent, slow, token):
        partial = None
        try:
            self.cache.mkdir(parents=True, exist_ok=True)
            voice = self.voices[accent]
            rate = "110" if slow else "155"
            digest = hashlib.sha256((voice + rate + text).encode()).hexdigest()
            path = self.cache / (digest + ".aiff")
            if not has_audio(path):
                partial = self.cache / (digest + f".{uuid.uuid4().hex}.partial.aiff")
                if not self._run(
                    ["say", "-v", voice, "-r", rate, "-o", str(partial)], token, text
                ):
                    return
                if not has_audio(partial):
                    raise RuntimeError(
                        "语音服务返回了空音频，请检查系统英语声音是否可用"
                    )
                partial.replace(path)
            with self.lock:
                if token != self.generation:
                    return
                self.status = "正在播放…（X 停止）"
            if self._run(["afplay", str(path)], token):
                with self.lock:
                    if token == self.generation:
                        self.status = ""
        except (OSError, RuntimeError) as exc:
            with self.lock:
                if token == self.generation:
                    self.status = "发音未成功；可用 sideword --audio-check 查看原因"
                    self.detail = str(exc)
        finally:
            if partial is not None:
                partial.unlink(missing_ok=True)

    def check(self):
        if not self.available:
            return False, "需要 macOS 的 say 和 afplay"
        with self.lock:
            token = self.generation
        # Diagnostic deliberately uses the same complete path as normal playback.
        self._speak("Hello. Welcome to Sideword.", "uk", False, token)
        return not bool(self.detail), self.detail or "语音合成和播放进程已完成"
