# weiqi.gs
# Copyright (C) 2016 Michael Bitzi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import tornado.web
from weiqi import settings
from weiqi.db import create_db
from weiqi.handler import auth, socket, main as main_handler, room


def main():
    create_db()

    handlers = [
        (r'/api/ping', main_handler.PingHandler),
        (r'/api/socket', socket.SocketHandler),
        (r'/api/auth/email-exists', auth.EmailExistsHandler),
        (r'/api/auth/sign-up', auth.SignUpHandler),
        (r'/api/auth/sign-in', auth.SignInHandler),
        (r'/api/auth/logout', auth.LogoutHandler),

        (r'/api/rooms/(.*?)/message', room.MessageHandler),
        (r'/api/rooms/(.*?)/users', room.UsersHandler),
        (r'/api/rooms/(.*?)/mark-read', room.MarkReadHandler),

        (r'.*', main_handler.MainHandler),
    ]

    app = tornado.web.Application(
        handlers,
        debug=settings.DEBUG,
        autoreload=settings.DEBUG,
        cookie_secret=settings.SECRET,
        template_path=settings.TEMPLATE_PATH,
        static_path=settings.STATIC_PATH)

    app.listen(settings.LISTEN_PORT)
    tornado.ioloop.IOLoop.current().start()
