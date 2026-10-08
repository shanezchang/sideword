"""Terminal rendering. Navigation and persistence belong to the app controller."""

import curses
import time
from datetime import datetime, timedelta

from sideword.ui.brand import WORDMARK
from sideword.ui.text import wrap


def learning_lines(desk, word, columns):
    lines = []
    for label, key in [("英", "ukphone"), ("美", "usphone")]:
        phone = word.get(key, "").strip(" /[]")
        if phone:
            lines.extend(wrap(f"{label} /{phone}/", columns))
    if not lines:
        lines.append("音标暂缺")
    lines.append("")
    for meaning in word["trans"]:
        lines.extend(wrap(meaning, columns))
    example = word.get("example")
    lines.append("")
    if example:
        lines.extend(wrap(example["en"], columns))
        if desk.translation:
            lines.extend(wrap(example["zh"], columns))
        lines.append("")
        lines.extend(wrap(example["phrase"], columns))
    else:
        lines.append("这词暂未配例句；可切换到 30 词样本体验")
    return lines


def render_word_page(desk, size):
    h, _ = desk.s.getmaxyx()
    queue, selected = desk.study_state["queue"], desk.study_state["index"]
    start = selected // size * size
    capacity = max(1, (h - 9) // 3)
    end = min(start + size, len(queue))
    visible_start = max(start, min(selected - capacity + 1, end - capacity))
    learned, progress = (
        desk.store.learned(desk.book),
        desk.store.progress(desk.book),
    )
    for offset, key in enumerate(queue[visible_start : min(end, visible_start + capacity)]):
        word = desk.words[key]
        active = visible_start + offset == selected
        phone = word.get("ukphone") or word.get("usphone") or ""
        phone = f" /{phone.strip(' /[]')}/" if phone else ""
        star = " *" if progress.get(key, {}).get("starred") else ""
        status = {"familiar": " · 熟悉", "unfamiliar": " · 还不熟"}.get(
            learned.get(key, {}).get("familiarity"), ""
        )
        desk.put(
            4 + offset * 3,
            ("› " if active else "  ") + word["name"] + phone + star,
            desk.accent if active else 0,
        )
        desk.put(5 + offset * 3, "  " + "；".join(word["trans"]) + status)
    accent = "英音" if desk.accent_name == "uk" else "美音"
    playback = "自动" if desk.autoplay else "手动"
    desk.put(
        h - 5,
        f"{selected + 1}/{len(queue)}  每页 {size}  {accent} · {playback}  M 设置",
    )
    desk.put(h - 4, "↑↓ 选词  ←→ 翻页  Enter 详情  空格 发音")
    desk.footer("1 还不熟  2 记住了  F 收藏  ? 帮助")


def render_learning(desk):
    h, w = desk.s.getmaxyx()
    word = desk.study_word()
    if word is None:
        review = desk.study_state["mode"] == "review"
        desk.put(
            5,
            "本轮到期词已复习完"
            if review and desk.study_state["queue"]
            else "暂时没有到期词"
            if review
            else "这些词都已记住；到期后仍会提醒复习"
            if desk.study_state["mode"] == "all"
            else "还没有这些词",
            desk.accent,
        )
        desk.put(
            7,
            "记住的词仍会安排复习；P 查看计划" if review else "在学习卡片按 1 标记还不熟，F 收藏",
        )
        desk.footer("Tab 首页   P 复习计划")
        return
    size = desk.effective_page_size()
    if size > 1:
        render_word_page(desk, size)
        return
    learned = desk.store.learned(desk.book).get(word["key"], {})
    familiarity = {"familiar": "熟悉", "unfamiliar": "还不熟"}.get(learned.get("familiarity"), "")
    starred = desk.store.progress(desk.book).get(word["key"], {}).get("starred")
    desk.put(4, word["name"] + ("  *" if starred else ""), desk.accent)
    lines = learning_lines(desk, word, w - 5)
    reviewing = desk.study_state["mode"] == "review"
    if reviewing and not desk.review_revealed:
        lines = [
            "先回忆这个词的意思。",
            "",
            "Enter 查看释义和例句",
            "空格可以听发音",
        ]
    visible = max(1, h - 12)
    desk.card_scroll = min(desk.card_scroll, max(0, len(lines) - visible))
    for i, line in enumerate(lines[desk.card_scroll : desk.card_scroll + visible]):
        desk.put(6 + i, line)
    progress = f"{desk.study_state['index'] + 1}/{len(desk.study_state['queue'])}  {familiarity}"
    if len(lines) > visible:
        progress += "  ↑↓ 滚动全文"
    desk.put(h - 6, progress)
    sound = ("英音" if desk.accent_name == "uk" else "美音") + (" · 慢速" if desk.slow else "")
    sound += " · 自动播放" if desk.autoplay else " · 手动播放"
    next_due = desk.due_label(learned.get("due"))
    desk.put(h - 5, "下次复习 " + next_due if next_due else sound)
    desk.put(h - 4, "空格 读单词  S 读例句  ? 更多按键")
    desk.footer(
        "Enter 揭晓   1 忘了   2 记得"
        if reviewing
        else "Enter 返回列表  ↑↓ 滚动全文"
        if getattr(desk, "word_detail", False)
        else "←→ 翻词  1 不熟  2 记住  M 每页词数"
    )


def render(desk):
    desk.s.erase()
    h, w = desk.s.getmaxyx()
    if w < 42 or h < 15:
        desk.put(1, "请把终端放大至 42 列 × 15 行", x=0)
        desk.put(3, "Esc 保存退出", x=0)
        desk.s.refresh()
        return
    desk.put(1, WORDMARK, desk.accent)
    due_count = len(desk.store.due_words(desk.book, desk.words))
    desk.put(2, desk.books[desk.book][0] + (f"  待复习 {due_count} · R" if due_count else ""))
    if desk.page == "home":
        stats = desk.store.stats(desk.book, desk.words)
        learned = desk.store.learned(desk.book)
        desk.put(
            4,
            f"已浏览 {len(learned)} / {stats['total']}   还不熟 {sum(r['familiarity'] == 'unfamiliar' for r in learned.values())}",
        )
        choices = [
            "看词学习 / 继续",
            f"到期复习 · {due_count} 词",
            "收藏词卡片",
            "拼写测验（可选）",
            "查词 / 浏览",
            "切换词本",
            f"每组 {desk.limit} 词",
        ]
        for i, label in enumerate(choices):
            desk.put(
                (5 if h < 18 else 6) + i,
                f"{'›' if desk.selected == i else ' '} {i + 1}  {label}",
                desk.accent if desk.selected == i else 0,
            )
        desk.footer("Enter 打开  P 计划  U 不熟的词")
    elif desk.page == "books":
        visible = max(1, h - 9)
        start = desk.book_cursor // visible * visible
        for i, (key, (label, _)) in enumerate(
            list(desk.books.items())[start : start + visible], start
        ):
            desk.put(
                5 + i - start,
                f"{'›' if i == desk.book_cursor else ' '} {i + 1}  {label}"
                + ("  当前" if key == desk.book else ""),
                desk.accent if i == desk.book_cursor else 0,
            )
        desk.footer("↑↓ 选择   Enter 打开   1–9 快选")
    elif desk.page == "browse":
        render_browse(desk)
    elif desk.page == "practice":
        render_practice(desk)
    elif desk.page == "learn":
        render_learning(desk)
    elif desk.page == "help":
        render_help(desk)
    elif desk.page == "schedule":
        render_schedule(desk)
    if desk.message:
        desk.put(h - 3, desk.message)
    if desk.speaker.status:
        desk.put(h - 3, desk.speaker.status)
    desk.s.refresh()


def render_help(desk):
    entries = [
        "空格 朗读单词    S 朗读英文例句",
        "V 切换英/美音   - 切换慢速",
        "A 自动播放开关  X 立即停止声音",
        "T 译文开关；单词页 ←→ 翻词 ↑↓ 滚动",
        "M 输入每页词数；多词页 ↑↓ 选词 ←→ 翻页",
        "多词页 Enter 查看/返回详情；操作仅作用于选中词",
        "1 还不熟  2 记住了  F 收藏",
        "R 到期复习  P 计划  U 不熟词",
    ]
    for i, text in enumerate(entries):
        desk.put(4 + i, text)
    desk.footer("? / Enter 返回词卡")


def render_schedule(desk):
    rows = desk.store.learned(desk.book)
    now = time.time()
    planned = [r["due"] for r in rows.values() if r.get("due") is not None]
    desk.put(
        4,
        f"到期 {sum(d <= now for d in planned)}  待复习总计 {len(planned)}",
        desk.accent,
    )
    today = datetime.now().date()
    for i in range(7):
        day = today + timedelta(days=i)
        count = sum(datetime.fromtimestamp(d).date() == day and d > now for d in planned)
        label = "今天稍后" if i == 0 else day.strftime("%m/%d")
        desk.put(5 + i, f"{label}   {count} 词")
    desk.footer("R 开始到期复习   Enter 返回")


def render_browse(desk):
    h, w = desk.s.getmaxyx()
    desk.put(4, "/ " + desk.query, desk.accent)
    items = desk.matches()
    desk.scroll = min(desk.scroll, max(0, len(items) - 1))
    visible = max(1, h - 11)
    start = desk.scroll // visible * visible
    rows = desk.store.progress(desk.book)
    for i, v in enumerate(items[start : start + visible]):
        mark = "*" if rows.get(v["key"], {}).get("starred") else " "
        desk.put(
            6 + i,
            f"{mark} {v['name']}  {' / '.join(v['trans'])}",
            desk.accent if start + i == desk.scroll else 0,
        )
    if not items:
        desk.put(6, "没有匹配项，试试中文释义或英文词干")
    desk.put(h - 4, f"{len(items)} 个匹配   英文 / 中文搜索")
    desk.footer("↑↓ 翻词   Enter 详情   ^F 收藏")


def render_practice(desk):
    h, w = desk.s.getmaxyx()
    if not desk.active():
        total = len(desk.state["queue"])
        desk.put(5, "这一组完成了" if total else "目前没有需要练习的词", desk.accent)
        if total:
            desk.put(7, f"独立拼对 {desk.state['correct']} / {total}")
            desk.put(9, "错词已安排复习；记住的词会逐步延长间隔")
        else:
            desk.put(7, "回首页开始混合练习，或先在查词里收藏")
        desk.footer("Enter 回首页")
        return
    word = desk.current()
    desk.put(
        4,
        f"{desk.state['index'] + 1} / {len(desk.state['queue'])}   写出英文",
        desk.accent,
    )
    definitions = wrap("；".join(word["trans"]), w - 5)
    # Leave space for answer, correction and controls even in a tmux split.
    count = max(1, min(len(definitions), h - 13))
    for i, line in enumerate(definitions[:count]):
        desk.put(
            6 + i,
            line + (" …" if i == count - 1 and len(definitions) > count else ""),
        )
    y = 7 + count
    if desk.state["phase"] == "answer":
        desk.put(y, "> " + desk.state["typed"] + "▏", curses.A_BOLD)
        if desk.state["assisted"]:
            desk.put(y + 2, word["name"][0] + " _" * (len(word["name"]) - 1))
        desk.footer("Enter 检查  ^H 提示  ^N 不会")
    else:
        good = desk.state["feedback"] == "correct"
        desk.put(y, ("正确  " if good else "答案  ") + word["name"], desk.accent)
        phone = word.get("ukphone") or word.get("usphone") or ""
        desk.put(y + 1, f"/{phone}/" if phone else "")
        if not good:
            desk.put(y + 2, "> " + desk.state["typed"] + "▏")
            desk.footer("订正后 Enter   ^F 收藏")
        else:
            desk.footer("Enter 下一个   ^F 收藏")
