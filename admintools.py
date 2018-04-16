from weiqi.models import User, RoomUser, DirectRoom
from weiqi.glicko2 import Player
from sqlalchemy.orm import sessionmaker
from weiqi import settings
from sqlalchemy import create_engine


def _makesession():
    Session = sessionmaker()
    _engine = create_engine(settings.DB_URL)
    session = Session(bind=_engine)
    return session


def admin_make_user(name='', password='', email='', rank=100):
    """ Make a new user.
        Input:
            name (str): The display attribute of the user.
            password (str): The password for the user.
            email (str): An email address eg test@test.test.
            rank (float): The rank to assign the user. Default 20k.
    """
    session = _makesession()

    assert name != ''
    assert password != ''
    user = User(display=name,
                email=email,
                is_active=True)
    user.set_password(password)
    user.rating = rank
    user.rating_data = Player(rank)

    session.add(user)
    session.commit()


def admin_update_rank(name='', newrank=100):
    """ Update the rank of a user.
        Input:
            name (str): The display attribute of a user.
            newrank (float): The new ranking to assign the user.
                Takes 100 -> 20k, 1100 -> 10k, 2100 -> 1d
    """

    session = _makesession()
    for user in session.query(User):
        if user.display == name:
            user.rating = newrank
    session.commit()


def admin_drop_user(name=''):
    """ Remove a user.
        Input:
            name (str): The display attribute of a user
    """
    session = _makesession()

    for room in session.query(DirectRoom):
        if room.user_two.display == name or room.user_one.display == name:
            session.delete(room)
    for roomuser in session.query(RoomUser):
        if roomuser.user.display == name:
            session.delete(roomuser)
    for user in session.query(User):
        if user.display == name:
            session.delete(user)
    session.commit()
