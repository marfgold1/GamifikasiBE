from sqlalchemy import JSON, ForeignKey, Integer
from db import db
from sqlalchemy.orm import mapped_column, Mapped


class Leaderboard(db.Model):
    LevelId: Mapped[int] = mapped_column(Integer,
                                         ForeignKey('level.Id',
                                                    ondelete='CASCADE'),
                                         primary_key=True)
    Boards: Mapped[JSON] = mapped_column(JSON)

    @staticmethod
    def default(id: int):
        return Leaderboard(
            LevelId=id,
            Boards=[[[] for _ in range(2)] for _ in range(2)],
        )
