
from .base import BaseService, ServiceError
from .rating import RatingService
from .rooms import RoomService
from .users import UserService
from .correspondence import CorrespondenceService
from .games import GameService
from .connection import ConnectionService
from .play import PlayService
from .settings import SettingsService
from .dashboard import DashboardService
from .search import SearchService

from .executor import execute_service
