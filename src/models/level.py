from sqlalchemy import JSON, TEXT, Integer, String
from db import db
from sqlalchemy.orm import mapped_column, Mapped


class Level(db.Model):
    Id: Mapped[int] = mapped_column(Integer,
                                    autoincrement=True, primary_key=True)
    Name: Mapped[str] = mapped_column(String(50))
    Summary: Mapped[str] = mapped_column(String(100))
    Thresholds: Mapped[JSON] = mapped_column(JSON)
    SystemDescription: Mapped[str] = mapped_column(TEXT)
    LevelSchema: Mapped[str] = mapped_column(TEXT)
