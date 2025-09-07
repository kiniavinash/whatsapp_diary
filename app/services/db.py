from datetime import datetime
from pathlib import Path
from typing import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, String, DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session, Mapped, mapped_column


ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH = ROOT_DIR / "data" / "db.sqlite3"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    sender: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_message_content_hash"),
    )


@contextmanager
def get_session() -> Iterator[Session]:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


