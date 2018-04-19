import random
from datetime import datetime, timedelta

from weiqi import settings
from weiqi.board import Board
from weiqi.db import transaction
from weiqi.models import Automatch, Room, RoomUser, Game, Timing, User, Challenge
from weiqi.rating import rating_range, rank_diff
from weiqi.services import BaseService, ServiceError, CorrespondenceService
from weiqi.sgf import game_from_sgf


class ChallengeExpiredError(ServiceError):
    pass


class InvalidBoardSizeError(ServiceError):
    pass


class InvalidHandicapError(ServiceError):
    pass


class ChallengePrivateCannotBeRankedError(ServiceError):
    pass


class PlayService(BaseService):
    """Service which handles the creation of games."""
    __service_name__ = 'play'

    @BaseService.authenticated
    @BaseService.register
    def automatch(self, preset, max_hc):
        start, end = rating_range(self.user.rating, max_hc)
        game = None

        with transaction(self.db):
            self.db.query(Automatch).filter_by(user=self.user).delete()

            query = self.db.query(Automatch).with_for_update()

            # We want to avoid matching against a user if there is already a game running between these two.
            sub = self.db.query(Game).filter(
                Game.is_demo.is_(False),
                Game.stage == 'playing',
                ((Game.black_user_id == self.user.id) & (Game.white_user_id == Automatch.user_id)) |
                ((Game.black_user_id == Automatch.user_id) & (Game.white_user_id == self.user.id)))
            query = query.filter(~sub.exists())

            query = query.filter(Automatch.min_rating <= self.user.rating,
                                 Automatch.max_rating >= self.user.rating,
                                 Automatch.user_rating >= start,
                                 Automatch.user_rating <= end,
                                 Automatch.preset == preset)
            query = query.order_by(Automatch.created_at)
            other = query.first()

            if other:
                game = self._create_automatch_game(
                    self.user, other.user, preset)
                self.db.delete(other)
            else:
                item = Automatch(preset=preset,
                                 user=self.user,
                                 user_rating=self.user.rating,
                                 min_rating=start,
                                 max_rating=end)
                self.db.add(item)

        if game:
            self._publish_game_started(game)
            self._publish_automatch(game.black_user, False)
            self._publish_automatch(game.white_user, False)

            if game.is_correspondence:
                CorrespondenceService(
                    self.db, self.socket).notify_automatch_started(game)
        else:
            self._publish_automatch(self.user, True)

    def _create_automatch_game(self, user, other, preset):
        black, white, handicap = self.game_players_handicap(user, other)
        komi = settings.DEFAULT_KOMI if handicap == 0 else settings.HANDICAP_KOMI
        timing_preset = settings.AUTOMATCH_PRESETS[preset]
        correspondence = (preset == 'correspondence')

        return self._create_game(True, correspondence, black, white, handicap, komi, settings.AUTOMATCH_SIZE,
                                 'fischer', timing_preset['capped'], timing_preset['main'], timing_preset['overtime'],
                                 0, False)

    @BaseService.authenticated
    @BaseService.register
    def cancel_automatch(self):
        self.db.query(Automatch).filter_by(user=self.user).delete()
        self._publish_automatch(self.user, False)

    def _publish_automatch(self, user, in_queue):
        self.socket.publish('automatch_status/' +
                            str(user.id), {'in_queue': in_queue})

    @BaseService.authenticated
    @BaseService.register
    def upload_sgf(self, sgf):
        game = game_from_sgf(sgf)

        room = Room(type='game')
        self.db.add(room)

        game.is_demo = True
        game.is_ranked = False
        game.stage = 'finished'
        game.demo_owner = self.user
        game.demo_owner_rating = self.user.rating
        game.demo_owner_display = self.user.display
        game.demo_control = self.user
        game.demo_control_display = self.user.display
        game.room = room
        self.db.add(game)

        self.db.commit()

        return game.id

    @BaseService.authenticated
    @BaseService.register
    def create_demo(self, title, size):
        room = Room(type='game')
        self.db.add(room)

        game = Game(is_demo=True,
                    is_ranked=False,
                    room=room,
                    title=title,
                    board=Board(int(size)),
                    komi=settings.DEFAULT_KOMI,
                    stage='finished',
                    demo_owner=self.user,
                    demo_owner_display=self.user.display,
                    demo_owner_rating=self.user.rating,
                    demo_control=self.user,
                    demo_control_display=self.user.display)

        self.db.add(game)
        self.db.commit()

        return game.id

    @BaseService.authenticated
    @BaseService.register
    def create_demo_from_game(self, game_id):
        game = self.db.query(Game).get(game_id)
        if not game:
            raise ServiceError('game not found')

        room = Room(type='game')
        self.db.add(room)

        demo = Game(is_demo=True,
                    is_ranked=False,
                    room=room,
                    board=game.board,
                    komi=game.komi,
                    stage='finished',
                    black_display=game.black_display,
                    white_display=game.white_display,
                    demo_owner=self.user,
                    demo_owner_display=self.user.display,
                    demo_owner_rating=self.user.rating,
                    demo_control=self.user,
                    demo_control_display=self.user.display)

        self.db.add(demo)
        self.db.commit()

        return demo.id

    @BaseService.authenticated
    @BaseService.register
    def challenge_setup_suggestion(self, user_id):
        other = self.db.query(User).filter_by(id=user_id).one()
        black, white, handicap = self.game_players_handicap(self.user, other)

        if handicap == 0:
            owner_is_black = None
            komi = settings.DEFAULT_KOMI
        else:
            owner_is_black = (self.user == black)
            komi = settings.HANDICAP_KOMI

        return {
            'other_user_id': other.id,
            'other_display': other.display,
            'other_rating': other.rating,
            'handicap': handicap,
            'komi': komi,
            'owner_is_black': owner_is_black,
        }

    @BaseService.authenticated
    @BaseService.register
    def challenge(self, user_id, size, handicap, komi, owner_is_black, speed, timing, maintime, overtime,
                  overtime_count, private=False, ranked=False):
        other = self.db.query(User).filter_by(id=user_id).one()
        correspondence = (speed == 'correspondence')

        if self.user == other:
            raise ServiceError('cannot challenge oneself')

        if (handicap is not None and handicap != 0) and owner_is_black is None:
            raise ServiceError('handicap defined but not black/white')

        if handicap is not None and (handicap < 0 or handicap > 9):
            raise InvalidHandicapError()

        if (ranked and size != 19) or size not in [9, 13, 19]:
            raise InvalidBoardSizeError()

        if correspondence:
            if not 24 <= maintime <= 24*5:
                raise ServiceError('invalid main time')

            if not 4 <= overtime <= 24*3:
                raise ServiceError('invalid overtime')
        else:
            if not 0 <= maintime <= 60:
                raise ServiceError('invalid main time')

            if not 0 <= overtime <= 60:
                raise ServiceError('invalid overtime')

        if private and ranked:
            raise ChallengePrivateCannotBeRankedError()

        if handicap is None or ranked:
            black, white, handicap = self.game_players_handicap(
                self.user, other)
            owner_is_black = (black == self.user)
            komi = (settings.DEFAULT_KOMI if handicap ==
                    0 else settings.HANDICAP_KOMI)

        if owner_is_black is None:
            owner_is_black = (random.choice([0, 1]) == 0)

        self.db.query(Challenge).filter_by(
            owner=self.user, challengee=other).delete()

        if correspondence:
            expire_at = (datetime.utcnow() +
                         settings.CORRESPONDENCE_CHALLENGE_EXPIRATION)
            maintime = timedelta(hours=maintime)
            overtime = timedelta(hours=overtime)
        else:
            expire_at = (datetime.utcnow() + settings.CHALLENGE_EXPIRATION)
            maintime = timedelta(minutes=maintime)
            overtime = timedelta(seconds=overtime)

        challenge = Challenge(expire_at=expire_at,
                              owner=self.user,
                              challengee=other,
                              board_size=size,
                              handicap=handicap,
                              komi=komi,
                              owner_is_black=owner_is_black,
                              is_correspondence=correspondence,
                              timing_system=timing,
                              maintime=maintime,
                              overtime=overtime,
                              overtime_count=overtime_count,
                              is_private=private,
                              is_ranked=ranked)

        self.db.add(challenge)
        self.db.commit()

        self._publish_challenges(challenge)

    @BaseService.authenticated
    @BaseService.register
    def decline_challenge(self, challenge_id):
        challenge = self.db.query(Challenge).filter_by(
            id=challenge_id, challengee=self.user).one()
        self.db.delete(challenge)
        self._publish_challenges(challenge)

    @BaseService.authenticated
    @BaseService.register
    def cancel_challenge(self, challenge_id):
        challenge = self.db.query(Challenge).filter_by(
            id=challenge_id, owner=self.user).one()
        self.db.delete(challenge)
        self._publish_challenges(challenge)

    @BaseService.authenticated
    @BaseService.register
    def accept_challenge(self, challenge_id):
        challenge = self.db.query(Challenge).filter_by(
            id=challenge_id, challengee=self.user).one()

        if challenge.expire_at < datetime.utcnow():
            raise ChallengeExpiredError()

        self.db.delete(challenge)

        if challenge.owner_is_black:
            black, white = challenge.owner, challenge.challengee
        else:
            black, white = challenge.challengee, challenge.owner

        game = self._create_game(challenge.is_ranked, challenge.is_correspondence, black, white, challenge.handicap,
                                 challenge.komi, challenge.board_size, challenge.timing_system,
                                 challenge.is_correspondence, challenge.maintime, challenge.overtime,
                                 challenge.overtime_count, challenge.is_private)

        self.db.commit()

        self._publish_game_started(game)
        self._publish_challenges(challenge)

        if game.is_correspondence:
            CorrespondenceService(
                self.db, self.socket).notify_challenge_started(game)

    def game_players_handicap(self, user: User, other: User):
        handicap = rank_diff(user.rating, other.rating)
        handicap = min(9, handicap)

        if handicap == 0:
            if random.choice([0, 1]) == 0:
                black, white = user, other
            else:
                black, white = other, user
        elif user.rating > other.rating:
            black, white = other, user
        else:
            black, white = user, other

        return black, white, handicap

    def _create_game(self,
                     ranked,
                     correspondence,
                     black, white,
                     handicap, komi, size,
                     timing_system, capped, maintime, overtime, overtime_count,
                     private):
        board = Board(size, handicap)

        room = Room(type='game')
        ru = RoomUser(room=room, user=black)
        ru2 = RoomUser(room=room, user=white)

        game = Game(room=room,
                    is_demo=False,
                    is_ranked=ranked,
                    is_correspondence=correspondence,
                    is_private=private,
                    board=board,
                    stage='playing',
                    komi=komi,
                    black_user=black,
                    black_display=black.display,
                    black_rating=black.rating,
                    white_user=white,
                    white_display=white.display,
                    white_rating=white.rating)

        start_at = datetime.utcnow() + settings.GAME_START_DELAY

        if timing_system == 'fischer':
            overtime_count = 0

        timing = Timing(game=game,
                        system=timing_system,
                        start_at=start_at,
                        timing_updated_at=start_at,
                        next_move_at=start_at,
                        capped=capped,
                        main=maintime,
                        overtime=overtime,
                        overtime_count=overtime_count,
                        black_main=maintime,
                        black_overtime=overtime*overtime_count,
                        white_main=maintime,
                        white_overtime=overtime*overtime_count)

        self.db.add(room)
        self.db.add(ru)
        self.db.add(ru2)
        self.db.add(game)
        self.db.add(timing)

        return game

    def _publish_game_started(self, game):
        self.socket.publish('game_started', game.to_frontend())

    def cleanup_challenges(self):
        """Deletes and publishes expired challenges."""
        challenges = self.db.query(Challenge).with_for_update().filter(
            (Challenge.expire_at < datetime.utcnow()))

        for ch in challenges:
            self.db.delete(ch)
            self._publish_challenges(ch)

    def _publish_challenges(self, challenge):
        for user in [challenge.owner, challenge.challengee]:
            challenges = [c.to_frontend()
                          for c in Challenge.open_challenges(self.db, user)]
            self.socket.publish('challenges/'+str(user.id), challenges)

    def cleanup_automatches(self):
        """Deletes automatch items which have expired or where the user was not online for a long period of time."""
        items = (self.db.query(Automatch)
                 .with_for_update()
                 .join(Automatch.user)
                 .filter(Automatch.preset == 'correspondence')
                 .filter(User.is_online.is_(False))
                 .filter(User.last_activity_at <= (datetime.utcnow() - settings.AUTOMATCH_EXPIRE_CORRESPONDENCE)))

        for item in items:
            self.db.delete(item)
