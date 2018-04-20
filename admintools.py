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


def make_user(name='', password='', email='', rank=100):
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


def get_user_object(name='', email=''):
    """ Get user object from name or info.
        Input:
            name (str, optional): The display attribute of a user.
            email (str, optional): The email of a user.
        Output:
            user (models.User): A user object from models.
            session (sqlalchemy.session): A connected sesion to the db.
    """

    session = _makesession()
    assert (name == '' or email == '')
    if name != '':
        for user in session.query(User):
            if user.display == name:
                out = (user, session)
    elif email != '':
        for user in session.query(User):
            if user.email == email:
                out = (user, session)
    else:
        print('Please provide a name or an email')
        return None

    print('Returned (user, session)')
    print('Commit any changes when done with session.commit()')
    return out


def update_name(name='', newname=''):
    """ Update the display attribute of a user.
        Input:
            name (str): The display attribute of a user.
            newname (str): The new display attribute to assign the user.
    """

    assert newname != ''
    session = _makesession()
    for user in session.query(User):
        if user.display == name:
            user.display = newname
    session.commit()


def update_email(name='', newemail=''):
    """ Update the email attribute of a user.
        Input:
            name (str): The display attribute of a user.
            newemail (str): The new email attribute to assign the user.
    """

    assert newemail != ''
    session = _makesession()
    for user in session.query(User):
        if user.display == name:
            user.email = newemail
    session.commit()


def update_password(name='', newpass=''):
    """ Update the password of a user.
        Input:
            name (str): The display attribute of a user.
            newpass (str): The new password to assign the user.

    """

    assert newpass != ''
    session = _makesession()
    for user in session.query(User):
        if user.display == name:
            user.set_password(newpass)
    session.commit()


def update_rank(name='', newrank=100):
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


def drop_user(name=''):
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
