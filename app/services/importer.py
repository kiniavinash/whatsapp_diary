import hashlib
from pathlib import Path
from typing import Dict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Message
from .parser import parse_export_file


def _compute_content_hash(timestamp_iso: str, sender: str, text: str) -> str:
    base = f"{timestamp_iso}|{sender or ''}|{text}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def import_export_file(path: Path, session: Session) -> Dict[str, int]:
    parsed = parse_export_file(path)
    imported = 0
    skipped = 0
    for pm in parsed:
        content_hash = _compute_content_hash(pm.timestamp.isoformat(), pm.sender or "", pm.text)
        msg = Message(timestamp=pm.timestamp, sender=pm.sender, text=pm.text, content_hash=content_hash)
        session.add(msg)
        try:
            session.flush()
            imported += 1
        except IntegrityError:
            session.rollback()
            skipped += 1
    return {"imported": imported, "skipped": skipped}


