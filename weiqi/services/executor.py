from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from weiqi import metrics, settings
from weiqi.db import session
from weiqi.models import User
from weiqi.services import (ConnectionService, RoomService, GameService, PlayService, UserService, SettingsService,
                            DashboardService, SearchService)

_executor = ThreadPoolExecutor(settings.SERVICE_THREADS)
_services = [ConnectionService, RoomService, GameService, PlayService, UserService, SettingsService, DashboardService,
             SearchService]
_service_names = {s.__service_name__: s for s in _services}


def execute_service(socket, user_id, service_name, method, data):
    """Executes the given service method on a ThreadPoolExecutor and returns its `Future` object.

    A ProcessPoolExecutor cannot be used because services generally need to have access to a websocket handler.
    A ThreadPoolExecutor is however still useful to prevent I/O, such as from DB queries or emails, from blocking
    the whole process.
    """
    return _executor.submit(_execute_service, socket, service_name, method, data, user_id)


def _execute_service(socket, service, method, data, user_id):
    with metrics.EXCEPTIONS.labels(service+'/'+method).count_exceptions():
        with session() as db:
            user = db.query(User).get(user_id) if user_id else None
            service_class = _service_names.get(service)

            if not service_class:
                raise ValueError('service "{}" not found'.format(service))

            if user and method != 'ping':
                user.last_activity_at = datetime.utcnow()

            return service_class(db, socket, user).execute(method, data)
