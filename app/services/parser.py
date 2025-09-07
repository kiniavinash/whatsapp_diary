import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Optional


HEADER_RE = re.compile(r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}(?: [AP]M)?) - (.+)$")


DATETIME_FORMATS = [
    "%d/%m/%y, %H:%M",
    "%d/%m/%Y, %H:%M",
    "%d/%m/%y, %I:%M %p",
    "%d/%m/%Y, %I:%M %p",
    "%m/%d/%y, %H:%M",
    "%m/%d/%Y, %H:%M",
    "%m/%d/%y, %I:%M %p",
    "%m/%d/%Y, %I:%M %p",
]


@dataclass
class ParsedMessage:
    timestamp: datetime
    sender: Optional[str]
    text: str


def _try_parse_datetime(header: str) -> Optional[datetime]:
    for fmt in DATETIME_FORMATS:
        try:
            return datetime.strptime(header, fmt)
        except ValueError:
            continue
    return None


def parse_export_lines(lines: Iterable[str]) -> List[ParsedMessage]:
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

    for raw_line in lines:
        line = raw_line.rstrip("\n\r")
        m = HEADER_RE.match(line)
        if m:
            # Start of a new message
            flush_current()
            header = f"{m.group(1)}, {m.group(2)}"
            rest = m.group(3)
            dt = _try_parse_datetime(header)
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


