"""Exercise a frozen executable in a real PTY, without speech or user records."""

import fcntl
import os
import pty
import select
import struct
import subprocess
import sys
import tempfile
import termios
import time
from pathlib import Path


def smoke(executable: Path) -> None:
    executable = executable.resolve()
    with tempfile.TemporaryDirectory(prefix="sideword-smoke-") as temp:
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 32, 110, 0, 0))
        env = {
            **os.environ,
            "TERM": "xterm-256color",
            "PATH": "/usr/bin:/bin",
            "LANG": "en_US.UTF-8",
        }
        process = subprocess.Popen(
            [str(executable), "--quiet", "--data-dir", temp],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            cwd=temp,
        )
        os.close(slave)
        output = bytearray()
        try:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if select.select([master], [], [], 0.2)[0]:
                    try:
                        output.extend(os.read(master, 65536))
                    except OSError:
                        break
                    if b"sideword" in output.lower():
                        break
                if process.poll() is not None:
                    break
            assert b"sideword" in output.lower(), output.decode(errors="replace")
            os.write(master, b"\x1b")
            # Keep draining: curses may still be writing the first frame when
            # the title arrives, and a full PTY buffer would block before get_wch.
            deadline = time.monotonic() + 8
            while process.poll() is None and time.monotonic() < deadline:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        output.extend(os.read(master, 65536))
                    except OSError:
                        break
            assert process.wait(timeout=1) == 0, output.decode(errors="replace")
            assert (Path(temp) / "progress.sqlite3").exists()
            print("Frozen terminal startup, rendering, SQLite and clean exit: OK")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)


if __name__ == "__main__":
    smoke(Path(sys.argv[1]))
