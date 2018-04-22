import logging

from weiqi.db import session
from weiqi.models import Connection, Automatch, User
from weiqi.services import GameService


def prepare_startup():
    """Prepares the server state for a clean startup.

    This is usually called separately to clean up the database before starting any worker processes.
    """
    logging.info("Preparing for startup ...")
    _prepare_db()


def _prepare_db():
    """Cleans DB state before starting the server."""
    logging.info("Cleaning database ...")
    with session() as db:
        db.query(Connection).delete()
        db.query(Automatch).filter(
            Automatch.preset != 'correspondence').delete()
        db.query(User).update({'is_online': False})
        GameService(db).resume_all_games()
