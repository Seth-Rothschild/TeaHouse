from tornado.autoreload import add_reload_hook
from tornado.options import define, options
from weiqi import settings
from weiqi.application import run_app
from weiqi.db import create_db, session
from weiqi.prepare_startup import prepare_startup
from weiqi.services import RoomService


def main():
    define_options()
    options.parse_command_line()

    settings.LISTEN_PORT += options.port_offset

    create_db()

    if options.prepare_startup:
        prepare_startup()
    elif options.create_room:
        with session() as db:
            RoomService(db).create_default_room(options.create_room)
    else:
        if settings.DEBUG:
            add_reload_hook(prepare_startup)
        run_app()


def define_options():
    define("prepare_startup", type=bool, default=None,
           help="Prepare for startup instead of running the application.")
    define("create_room", type=str, default=None,
           help="Create a new default chat room")

    define("port_offset", type=int, default=0,
           help="Offset to add to the port number")
