from sqlalchemy import JSON, ForeignKey, Integer
from db import db
from sqlalchemy.orm import mapped_column, Mapped


class LevelStat(db.Model):
    LevelId: Mapped[int] = mapped_column(
        Integer, ForeignKey('level.Id', ondelete='CASCADE'), primary_key=True)
    TotalCompleted: Mapped[JSON] = mapped_column(JSON)
    Averages: Mapped[JSON] = mapped_column(JSON)
    CountStars: Mapped[JSON] = mapped_column(JSON)

    @staticmethod
    def default(id: int):
        return LevelStat(
            LevelId=id,
            TotalCompleted=[[0, 0], [0, 0]],
            Averages=[[0, 0], [0, 0]],
            CountStars=[
                [[0, 0, 0, 0], [0, 0, 0, 0]],
                [[0, 0, 0, 0], [0, 0, 0, 0]],
            ],
        )
