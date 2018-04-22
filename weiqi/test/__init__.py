import os

from sqlalchemy.orm import scoped_session
from weiqi import settings
from weiqi.db import Session, create_db, create_schema

settings.DEBUG = False
settings.DB_URL = os.environ.get('WEIQI_TEST_DB', 'sqlite://')
settings.RECAPTCHA['backend'] = 'dummy'
settings.MAILER['backend'] = 'console'

create_db()
create_schema()

session = scoped_session(Session)

# Patch the `weiqi.db.sessions` contextmanager to use the same session as other parts of the testing framework, such as
# in factory boy.
# This is mainly used to test tornado request handlers.
from contextlib import contextmanager


@contextmanager
def _patched_session():
    yield session


from weiqi import db
db.session = _patched_session
