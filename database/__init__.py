"""
The database module for ClicksMinutePer projects
Written by Minion3665
"""
import sqlalchemy
from . import guild
from sqlalchemy.ext.declarative import declarative_base

__models__ = (
    guild,
)


def setup(bot):
    """Setup the database and add it to the bot"""
    global __all__
    database = sqlalchemy.create_engine(
        f"{bot.config['database_dialect']}://{bot.config['database_user']}:{bot.config['database_password']}@{bot.config['database_host']}:{bot.config['database_port']}/{bot.config['database_name']}"
        if not bot.config['database_use_sqlite'] else f"sqlite:///{bot.config['database_sqlite_path']}",
        echo=bot.config['database_echo'] and "debug",
        echo_pool=bot.config['database_echo'] and "debug",
    )
    bot.set(
        "database",
        database
    )
    table_base = declarative_base()
    bot.set(
        "database",
        table_base
    )
    tables = []
    for table in __models__:
        tables.append(table.setup(table_base))

    table_base.metadata.create_all(database)
    __all__ = tuple(tables)


__all__ = (
    setup,
)
