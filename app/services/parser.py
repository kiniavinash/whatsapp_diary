import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional, Tuple


HEADER_RE = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}(?: [AP]M)?) - (.+)$")


@dataclass
class ParsedMessage:
    timestamp: datetime
    sender: Optional[str]
    text: str


def _build_preferred_formats(order: str, prefer_12h: bool) -> List[str]:
    # order: "MDY" or "DMY"
    if order == "MDY":
        base = ["%m/%d/%y", "%m/%d/%Y"]
    else:
        base = ["%d/%m/%y", "%d/%m/%Y"]

    # Prefer detected hour style first, but keep fallbacks for robustness
    formats: List[str] = []
    if prefer_12h:
        formats += [f"{b}, %I:%M %p" for b in base]
        formats += [f"{b}, %H:%M" for b in base]
    else:
        formats += [f"{b}, %H:%M" for b in base]
        formats += [f"{b}, %I:%M %p" for b in base]

    # Final safety: try opposite order as last resort
    other_base = ["%d/%m/%y", "%d/%m/%Y"] if order == "MDY" else ["%m/%d/%y", "%m/%d/%Y"]
    if prefer_12h:
        formats += [f"{b}, %I:%M %p" for b in other_base]
        formats += [f"{b}, %H:%M" for b in other_base]
    else:
        formats += [f"{b}, %H:%M" for b in other_base]
        formats += [f"{b}, %I:%M %p" for b in other_base]
    return formats


def _detect_order_and_time(lines: List[str], max_samples: int = 400) -> Tuple[str, bool]:
    """Detect whether dates are MDY or DMY and whether 12h (AM/PM) appears.

    Heuristic:
    - If any header has first number > 12 → DMY
    - If any header has second number > 12 → MDY
    - If both seen, decide by which occurs more.
    - If neither seen, default to MDY (common in exported EN-US chats).
    - prefer_12h is true if any sample contains AM/PM.
    """
    a_gt_12 = 0
    b_gt_12 = 0
    saw_am_pm = False
    checked = 0
    for raw in lines:
        if checked >= max_samples:
            break
        m = HEADER_RE.match(raw.rstrip("\n\r"))
        if not m:
            continue
        checked += 1
        date_part, time_part = m.group(1), m.group(2)
        if "AM" in time_part or "PM" in time_part:
            saw_am_pm = True
        try:
            a_str, b_str, _ = date_part.split("/")
            a = int(a_str)
            b = int(b_str)
            if a > 12:
                a_gt_12 += 1
            if b > 12:
                b_gt_12 += 1
        except Exception:
            continue

    if a_gt_12 > b_gt_12:
        order = "DMY"
    elif b_gt_12 > a_gt_12:
        order = "MDY"
    else:
        order = "MDY"
    return order, saw_am_pm


def _try_parse_datetime(header: str, formats: List[str]) -> Optional[datetime]:
    for fmt in formats:
        try:
            return datetime.strptime(header, fmt)
        except ValueError:
            continue
    return None


def parse_export_lines(lines: Iterable[str]) -> List[ParsedMessage]:
    # Convert to list so we can run detection once
    raw_lines = [l for l in lines]
    order, prefer_12h = _detect_order_and_time(raw_lines)
    preferred_formats = _build_preferred_formats(order, prefer_12h)

    messages: List[ParsedMessage] = []

    current_timestamp: Optional[datetime] = None
    current_sender: Optional[str] = None
    current_text_parts: List[str] = []

    def flush_current():
        nonlocal current_timestamp, current_sender, current_text_parts
        if current_timestamp is None:
            return
        text = "\n".join(current_text_parts).strip()
        messages.append(ParsedMessage(timestamp=current_timestamp, sender=current_sender, text=text))
        current_timestamp = None
        current_sender = None
        current_text_parts = []

    for raw_line in raw_lines:
        line = raw_line.rstrip("\n\r")
        m = HEADER_RE.match(line)
        if m:
            # Start of a new message
            flush_current()
            header = f"{m.group(1)}, {m.group(2)}"
            rest = m.group(3)
            dt = _try_parse_datetime(header, preferred_formats)
            if dt is None:
                # If we cannot parse, treat as a continuation line
                current_text_parts.append(line)
                continue
            # Split sender and text if present
            sender = None
            text = rest
            sender_split = re.match(r"([^:]+):\s(.*)$", rest)
            if sender_split:
                sender = sender_split.group(1).strip()
                text = sender_split.group(2)

            current_timestamp = dt
            current_sender = sender
            current_text_parts = [text]
        else:
            # Continuation of previous message
            if current_timestamp is None:
                # Skip stray lines before the first header
                continue
            current_text_parts.append(line)

    # Flush last
    flush_current()
    return messages


def parse_export_file(path) -> List[ParsedMessage]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return parse_export_lines(f)


