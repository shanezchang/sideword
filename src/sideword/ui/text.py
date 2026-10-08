"""Display-width-aware text handling for Chinese and IPA."""

import unicodedata


def width(text):
    return sum(
        0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1
        for c in text
    )


def clip(text, columns):
    result = ""
    for c in str(text).replace("\n", " "):
        if unicodedata.category(c).startswith("C"):
            continue
        if width(result + c) > columns:
            break
        result += c
    return result


def wrap(text, columns):
    columns = max(1, columns)
    lines, line = [], ""
    for c in text:
        if c == "\n":
            lines.append(line.rstrip())
            line = ""
        elif width(line + c) > columns:
            split = line.rfind(" ")
            if split > 0 and c != " ":
                lines.append(line[:split].rstrip())
                line = line[split + 1 :] + c
            else:
                lines.append(line.rstrip())
                line = c.lstrip()
        else:
            line += c
    return lines + [line]
