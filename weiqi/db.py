import uuid
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgres import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator, CHAR
from weiqi import settings

Base = declarative_base()
_engine = None
Session = sessionmaker()


def create_db():
    global _engine
    _engine = create_engine(settings.DB_URL)
    Session.configure(bind=_engine)


def create_schema():
    from weiqi import models
    Base.metadata.create_all(_engine)


@contextmanager
def session():
    sess = Session()

    try:
        with transaction(sess):
            yield sess
    finally:
        sess.close()


@contextmanager
def transaction(sess):
    try:
        yield
        sess.commit()
    except:
        sess.rollback()
        raise


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)
