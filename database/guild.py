"""The guild table for GPS"""
from sqlalchemy import Column, BigInteger, JSON, DateTime


def setup(base):
    """
    Create the guild table
    """

    class Guild(base):
        """The guild table 🎉"""
        __tablename__ = "guilds"
        id = Column(
            BigInteger,
            primary_key=True,
            autoincrement=False
        )
        agreed_at = Column(
            DateTime,
            unique=False,
            nullable=False
        )
        agreed_by = Column(
            BigInteger,
            unique=False,
            nullable=False
        )
        default_settings = Column(
            JSON,
            default={
                "rounds": 0,
                "points": 7,
                "anon": False,
                "blanks": 0,
                "shuffles": 0,
                "time": 15,
                "choose_time": 150,
                "judge_choose_time": 300,
                "hand_size": 10,
                "max_players": 25,
                "use_whitelist": False,
                "packs": [],
                "ai": True,
            },
        )
        settings = Column(
            JSON,
            default={}
        )

        def __repr__(self):
            return f"<Guild(id={self.id}, agreed={self.agreed})>"

    return Guild
