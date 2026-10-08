"""Validated vocabulary loading from package resources and user-owned books."""

import json
import unicodedata
from importlib.resources import files
from pathlib import Path
from typing import NotRequired, TypedDict


class Example(TypedDict):
    en: str
    zh: str
    phrase: str


class Word(TypedDict):
    name: str
    key: str
    trans: list[str]
    ukphone: NotRequired[str]
    usphone: NotRequired[str]
    example: Example | None


class VocabularyError(ValueError):
    """A word book cannot be loaded; the message identifies the offending row."""


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().replace("’", "'").split())


def parse_words(rows: object, source: str) -> dict[str, Word]:
    if not isinstance(rows, list) or not rows:
        raise VocabularyError(f"{source}: 词库必须是非空 JSON 数组")
    result: dict[str, Word] = {}
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise VocabularyError(f"{source}: 第 {index} 条必须是对象")
        name, meanings = row.get("name"), row.get("trans")
        if not isinstance(name, str) or not name.strip():
            raise VocabularyError(f"{source}: 第 {index} 条缺少单词 name")
        if (
            not isinstance(meanings, list)
            or not meanings
            or any(not isinstance(item, str) or not item.strip() for item in meanings)
        ):
            raise VocabularyError(f"{source}: 第 {index} 条 trans 必须是非空字符串列表")
        key = normalize(name)
        example = row.get("example")
        if example is not None and (
            not isinstance(example, dict)
            or any(not isinstance(example.get(field), str) for field in ("en", "zh", "phrase"))
        ):
            raise VocabularyError(f"{source}: 第 {index} 条 example 需要 en / zh / phrase 字符串")
        word: Word = {"name": name.strip(), "key": key, "trans": meanings, "example": example}
        for field in ("ukphone", "usphone"):
            value = row.get(field, "")
            if not isinstance(value, str):
                raise VocabularyError(f"{source}: 第 {index} 条 {field} 必须是字符串")
            word[field] = value
        if key in result:
            result[key]["trans"] = list(dict.fromkeys(result[key]["trans"] + meanings))
        else:
            result[key] = word
    return result


class Library:
    """Discover optional books without writing into the installed application."""

    def __init__(self, directory: Path | None = None):
        self.catalog = {"sample": ("学习样本 · 30 词", None)}
        if directory and directory.is_dir():
            for path in sorted(directory.glob("*.json")):
                key = {"IELTS_3_T": "ielts", "IELTSVocabularyBible": "bible"}.get(
                    path.stem, path.stem
                )
                if key in self.catalog:
                    raise VocabularyError(f"词库名称重复或保留: {key}")
                label = {"ielts": "雅思词库", "bible": "雅思词汇真经"}.get(key, key)
                self.catalog[key] = (label, path)

    def load(self, book: str) -> dict[str, Word]:
        if book not in self.catalog:
            raise VocabularyError(f"未找到词库 {book}；可用 --list-books 查看")
        _, path = self.catalog[book]
        resource = files("sideword").joinpath("data/sample.json") if path is None else path
        try:
            rows = json.loads(resource.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise VocabularyError(f"无法读取词库 {book}: {exc}") from exc
        result = parse_words(rows, book)
        examples = json.loads(
            files("sideword").joinpath("data/examples.json").read_text(encoding="utf-8")
        )
        for key, word in result.items():
            if word["example"] is None:
                word["example"] = examples.get(key)
        return result
