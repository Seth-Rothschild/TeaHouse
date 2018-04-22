import os.path
from datetime import timedelta

BASE_DIR = os.path.normpath(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir, os.path.pardir)))
BASE_URL = 'http://localhost:8000'

DEBUG = True

# Secret key is used for signing. Change this in production.
SECRET = b'j$\x1eM\xe2K\xda\xc0zndD\x80\x10\xc0\x8c\xba\xa1\xaeC\x01y\xe7\xe1'

COOKIE_NAME = 'weiqi'

TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates')
STATIC_PATH = os.path.join(BASE_DIR, 'static')

LISTEN_PORT = 8000

# Use this URL if you want to use vagrant and PostgreSQL
# DB_URL = 'postgresql://weiqi:6ff6zzHxLmuLMpyuRyMC@localhost/weiqi'
DB_URL = 'sqlite:///weiqi.db'

# Set the message broker to 'ampq' if you want to use vagrant and RabbitMQ
# MESSAGE_BROKER = 'ampq'
# AMPQ_URL = 'amqp://guest:guest@127.0.0.1:5672/'
MESSAGE_BROKER = 'dummy'

RECAPTCHA = {
    'backend': 'dummy',
    'secret': '',

    # For development we still need a valid recaptcha public key.
    'public': '6LdrkiATAAAAAGL1iWz14Nu7-VigpAtqpYWmpD0y',
}

MAILER = {
    'backend': 'console',
    'from': 'no-reply@weiqi.gs',
    'smtp_host': '',
    'smtp_port': 587,
    'smtp_user': '',
    'smtp_password': '',
}

# The number of threads to use for services
SERVICE_THREADS = 10

# The number of messages to load from the room history after connecting.
ROOM_MESSAGES_LIMIT = 30

# The rating-period duration for the rating system (Glicko2).
# In production this should be a value of several days or even weeks.
RATING_PERIOD_DURATION = timedelta(days=1)

# The time before a game starts. This can be seen as the countdown before a game.
GAME_START_DELAY = timedelta(seconds=10)

DEFAULT_KOMI = 7.5
HANDICAP_KOMI = 0.5

AUTOMATCH_SIZE = 19
AUTOMATCH_PRESETS = {
    'fast': {
        'capped': False,
        'main': timedelta(minutes=5),
        'overtime': timedelta(seconds=10),
    },
    'medium': {
        'capped': False,
        'main': timedelta(minutes=10),
        'overtime': timedelta(seconds=20),
    },
    'slow': {
        'capped': False,
        'main': timedelta(minutes=15),
        'overtime': timedelta(seconds=30),
    },
    'correspondence': {
        'capped': True,
        'main': timedelta(days=3),
        'overtime': timedelta(hours=24),
    }
}

# The duration after which a correspondence automatch entry expires if the user hasn't been online.
AUTOMATCH_EXPIRE_CORRESPONDENCE = timedelta(days=3)

DASHBOARD_POPULAR_GAMES = 5
DASHBOARD_POPULAR_GAMES_MAX_AGE = timedelta(days=7)

CHALLENGE_EXPIRATION = timedelta(minutes=5)
CORRESPONDENCE_CHALLENGE_EXPIRATION = timedelta(days=3)

# Maintime to add to each player's clock after server downtime.
RESUME_TIMING_ADD_TIME = timedelta(minutes=1)

METRICS_COLLECTION_INTERVAL = timedelta(seconds=10)

MAX_USER_INFO_TEXT_LENGTH = 10000

# When timings are capped the cap will be calculated as the initial main time * this value.
TIMING_MAIN_CAP_MULTIPLIER = 2

SEARCH_RESULTS_PER_PAGE = 10
