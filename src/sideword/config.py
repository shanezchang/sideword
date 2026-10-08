"""User-owned paths and command-line value validation."""

import argparse
import os
from pathlib import Path


def data_directory() -> Path:
    root = os.environ.get("XDG_DATA_HOME")
    return (Path(root) if root else Path.home() / ".local" / "share") / "sideword"


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError("请输入大于 0 的整数") from None
    if number <= 0:
        raise argparse.ArgumentTypeError("请输入大于 0 的整数")
    return number
