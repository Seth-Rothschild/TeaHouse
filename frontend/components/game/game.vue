<template>
    <div class="row" v-if="timer_started && user.logged_in" v-el:game>
        <div class="col-sm-9 game-detail-left">
            <template v-if="!has_started">
                <h1 class="text-center">{{$t('game.will_start_in')}}</h1>
                <h1 class="text-center">{{seconds_to_start}}</h1>
            </template>
            <template v-else>
                <template v-if="game.is_demo">
                    <p class="text-center">
                        <span v-if="game.title">{{game.title}}</span>
                        <select v-if="has_control" v-model="demo_tool" class="pull-right form-control game-demo-tools">
                            <option value="move">{{$t('demo.tool.move')}}</option>
                            <option value="edit">{{$t('demo.tool.edit')}}</option>
                            <option value="triangle">{{$t('demo.tool.triangle')}}</option>
                            <option value="square">{{$t('demo.tool.square')}}</option>
                            <option value="circle">{{$t('demo.tool.circle')}}</option>
                            <option value="label">{{$t('demo.tool.label')}}</option>
                            <option value="number">{{$t('demo.tool.number')}}</option>
                        </select>
                        <div class="clearfix"></div>
                    </p>
                </template>
                <qi-board v-if="game.board"
                          :board="game.board"
                          :current_node_id="current_node_id"
                          :current_color="current"
                          :coordinates="coordinates"
                          :can_click="true"
                          :mouse_shadow="show_mouse_shadow"
                          :allow_shadow_move="demo_tool == 'edit'"
                          :current="current"
                          :highlight_coord="highlight_coord"></qi-board>
            </template>
        </div>

        <div class="col-sm-3 game-detail-right">
            <div class="panel panel-default flex-fixed game-detail-players">
                <div class="panel-body">
                    <div class="game-player-wrapper">
                        <qi-game-player :demo="game.is_demo" :stage="game.stage" :color="'white'"
                                        :display="game.white_display || 'White'" :user_id="game.white_user_id"
                                        :rating="game.white_rating" :points="0" :main_time="white_time"
                                        :is_current="white_is_current"></qi-game-player>
                        <qi-game-player :demo="game.is_demo" :stage="game.stage" :color="'black'"
                                        :display="game.black_display || 'Black'" :user_id="game.black_user_id"
                                        :rating="game.black_rating" :points="0" :main_time="black_time"
                                        :is_current="black_is_current"></qi-game-player>
                        <div class="clearfix"></div>
                    </div>

                    <p class="text-center" v-if="game.stage!='playing' && game.result">
                        {{game.result}}
                    </p>

                    <template v-if="is_player && has_started">
                        <button class="btn btn-default btn-block" v-if="game.stage=='playing'" @click="pass()">
                            {{$t('game.pass')}}
                        </button>

                        <button class="btn btn-default btn-block" v-if="game.stage=='counting'" @click="resume_from_counting()">
                            {{$t('game.resume_from_counting')}}
                        </button>

                        <button class="btn btn-default btn-block" v-if="game.stage=='counting'" @click="confirm_score()">
                            {{$t('game.confirm_score')}}
                        </button>

                        <button class="btn btn-default btn-block" v-if="game.stage!='finished'" @click="resign()">
                            {{$t('game.resign')}}
                        </button>
                    </template>

                    <button v-if="game.is_demo && has_control" class="btn btn-default btn-xs btn-block" @click="pass()">
                        {{$t('game.pass')}}
                    </button>

                    <qi-game-options :game="game" :is_player="is_player" :has_control="has_control"></qi-game-options>
                    <qi-game-navigation :game="game" :is_player="is_player" :has_control="has_control" :force_node_id.sync="force_node_id"></qi-game-navigation>
                </div>
            </div>

            <qi-room-logs :room_id="game.room_id"
                          :show_only_user_ids="room_logs_show_only"
                          layout="narrow"
                          :format_coords="true"
                          :board_size="game.board.size"
                          :message.sync="room_message"
                          :embed_users="true"></qi-room-logs>
        </div>
    </div>
    <div v-else>
        <qi-page-load-spinner></qi-page-load-spinner>
    </div>
</template>

<script>
    import bootbox from 'bootbox';
    import moment from 'moment';
    import { open_game, update_game_time, clear_game_update } from './../../vuex/actions';
    import * as socket from '../../socket';
    import { play_sound } from '../../sounds';
    import { current_color, parse_coord, coord_to_str } from '../../board';
    import { is_current_player } from '../../game';

    export default {
        mixins: [require('./../../mixins/title.vue')],

        components: {
            'qi-game-player': require('./game_player.vue'),
            'qi-game-options': require('./game_options.vue'),
            'qi-game-navigation': require('./game_navigation.vue')
        },

        vuex: {
            getters: {
                open_games: function(state) { return state.open_games },
                user: function(state) { return state.auth.user },
                game_has_update: function(state) { return state.game_has_update; }
            },
            actions: {
                open_game,
                update_game_time,
                clear_game_update
            }
        },

        route: {
            canReuse: false
        },

        data() {
            return {
                force_node_id: false,
                seconds_to_start: null,
                timer_started: false,
                demo_tool: 'move',
                shift_down: false,
                ctrl_down: false,
                highlight_coord: null,
                room_message: '',
            }
        },

        computed: {
            window_title() {
                if(this.game.is_demo) {
                    return this.game.title;
                }
                return this.game.white_display + ' - ' + this.game.black_display;
            },

            game_id() {
                return this.$route.params.game_id;
            },

            game() {
                var empty = {
                    id: false,
                    timing: {
                        black_main: 0,
                        black_overtime: 0,
                        white_main: 0,
                        white_overtime: 0
                    },
                    board: {
                        tree: [],
                        current: 'x'
                    }
                };

                return this.open_games[this.game_id] || empty;
            },

            is_player() {
                return this.user.user_id == this.game.black_user_id || this.user.user_id == this.game.white_user_id;
            },

            current_node_id() {
                if(this.force_node_id !== false) {
                    return this.force_node_id;
                }
                return this.game.board.current_node_id;
            },

            current() {
                var color = current_color(this.game.board, this.current_node_id);

                if(this.game.is_demo && this.demo_tool == 'edit') {
                    color = 'x';

                    if(this.shift_down) {
                        color = 'o';
                    } else if(this.ctrl_down) {
                        color = 'x';
                    }
                }

                return color;
            },

            white_is_current() {
                return this.current == 'o';
            },

            black_is_current() {
                return this.current == 'x';
            },

            has_control() {
                return this.game.is_demo && this.user.user_id == this.game.demo_control_id;
            },

            black_time() {
                if(this.game.timing) {
                    return this.game.timing.black_main;
                }
            },

            white_time() {
                if(this.game.timing) {
                    return this.game.timing.white_main;
                }
            },

            has_started() {
                return !this.seconds_to_start || this.seconds_to_start <= 0;
            },

            room_logs_show_only() {
                if(this.is_player && this.game.stage != 'finished') {
                    return [this.game.black_user_id, this.game.white_user_id];
                }
                return [];
            },

            coordinates() {
                return !this.is_player || this.game.stage == 'finished' || this.game.stage != 'finished';
            },

            can_edit_board() {
                var has_control = this.has_control;
		if(this.game.stage == 'counting') {
		    return 'x' || 'o';
		}
                var is_current = is_current_player(this.game, this.current_node_id, this.user.user_id);

                return has_control || is_current;
            },

            show_mouse_shadow() {
                if(!this.can_edit_board) {
                    return false;
                }

                if(this.game.is_demo && (this.demo_tool != 'move' && this.demo_tool != 'edit')) {
                    return false;
                }

                return true;
            }
        },

        watch: {
            'game.board.last_inserted_node_id': function(node_id) {
                if(this.game.board.current_node_id != node_id) {
                    return;
                }

                var node = this.game.board.tree[node_id];

                // if(node.move < 0) {
                //     play_sound('beep');
                // } else if(node.action == 'B') {
                //     play_sound('black_stone');
                // } else if(node.action == 'W') {
                //     play_sound('white_stone');
                // }
            },

            'game_has_update[game_id]': function() {
                this.clear_update();
            },

            'timer_started': function(started) {
                if(started) {
                    jQuery(this.$els.game).on('mouseover', '.room-logs .coord', function(ev) {
                        this.highlight_coord = parse_coord(jQuery(ev.target).text(), this.game.board.size);
                    }.bind(this)).on('mouseout', '.room-logs .coord', function() {
                        this.highlight_coord = null;
                    }.bind(this));
                }
            }
        },

        ready() {
            this.open_game(this.game_id);
            this.clear_update();
            this.timer = setInterval(this.update_timer, 200);
            this.update_timer();

            jQuery(window).on('keydown', this.keydown_handler);
            jQuery(window).on('keyup', this.keyup_handler);
        },

        destroyed() {
            clearInterval(this.timer);
            jQuery(window).off('keydown', this.keydown_handler);
            jQuery(window).off('keyup', this.keyup_handler);
        },

        events: {
            'board-click': function(coord, event, is_touch) {
                this.handle_board_click(coord, event, is_touch);
            },

            'board-scroll': function(scroll) {
                if(this.is_player && this.game.stage != 'finished') {
                    return;
                }

                if(scroll < 0) {
                    this.$broadcast("game-navigate", -1);
                } else {
                    this.$broadcast("game-navigate", +1);
                }
            }
        },

        methods: {
            clear_update() {
                this.clear_game_update(this.game_id);
            },

            update_timer() {
                if(this.game.id === false) {
                    return;
                }

                if(this.game.timing && this.game.stage == 'playing') {
                    var starting = (this.seconds_to_start === null);
                    this.seconds_to_start = Math.ceil(moment.utc(this.game.timing.start_at).diff(moment.utc()) / 1000);

                    if(this.has_started) {
                        this.update_game_time(this.game.id);
                    } else if(starting) {
                        for(var i=0; i<this.seconds_to_start; i++) {
                            setTimeout(function () {
                                // play_sound('beep');
                            }, 1000 * i);
                        }
                    }
                }

                this.timer_started = true;
            },

            pass() {
                if(this.game.is_demo) {
                    socket.send('games/move', {'game_id': this.game_id, 'move': -1});
                } else {
                    bootbox.confirm({
                        buttons: {
                            confirm: {
                                label: this.$t('game.pass')
                            }
                        },
                        message: this.$t('game.confirm_pass'),
                        callback: function (res) {
                            if (res) {
                                socket.send('games/move', {'game_id': this.game_id, 'move': -1});
                            }
                        }.bind(this)
                    });
                }
            },

            resign() {
                bootbox.confirm({
                    buttons: {
                        confirm: {
                            label: this.$t('game.resign'),
                            className: 'btn-danger'
                        }
                    },
                    message: this.$t('game.confirm_resign'),
                    callback: function(res) {
                        if(res) {
                            socket.send('games/move', {'game_id': this.game_id, 'move': -2});
                        }
                    }.bind(this)
                });
            },

            resume_from_counting() {
                socket.send('games/resume_from_counting', {'game_id': this.game_id});
            },

            confirm_score() {
                socket.send('games/confirm_score', {'game_id': this.game_id, 'result': this.game.result});
            },

            keydown_handler(ev) {
                this.shift_down = ev.shiftKey;
                this.ctrl_down = ev.ctrlKey;
            },

            keyup_handler(ev) {
                this.handle_hotkey(ev);

                this.shift_down = ev.shiftKey;
                this.ctrl_down = ev.ctrlKey;
            },

            handle_hotkey(ev) {
                if(ev.shiftKey || ev.ctrlKey || ev.metaKey) {
                    return;
                }

                var target = jQuery(ev.target);

                if(target.is('input') || target.is('textarea') || target.is('select')) {
                    return;
                }

                switch(String.fromCharCode(ev.which).toLowerCase()) {
                    case 'v': this.demo_tool = 'move'; break;
                    case 'e': this.demo_tool = 'edit'; break;
                    case 't': this.demo_tool = 'triangle'; break;
                    case 's': this.demo_tool = 'square'; break;
                    case 'c': this.demo_tool = 'circle'; break;
                    case 'a': this.demo_tool = 'label'; break;
                    case '1': this.demo_tool = 'number'; break;
                }
            },

            handle_board_click(coord, event, is_touch) {
                if (event.ctrlKey) {
                    this.share_coord(coord);
                } else if(this.can_edit_board) {
                    if (this.game.is_demo && this.has_control) {
                        this.handle_demo_click(coord, event, is_touch);
                    } else if (!this.game.is_demo && this.is_player) {
                        this.handle_player_click(coord, event, is_touch);
                    }
                }
            },

            handle_demo_click(coord, event, is_touch) {
                switch(this.demo_tool) {
                    case 'move':
                        socket.send('games/move', {game_id: this.game_id, move: coord});
                        break;
                    case 'edit':
                        if(is_touch){
                            socket.send('games/demo_tool_edit_cycle', {game_id: this.game_id, coord: coord});
                        } else {
                            if(event.shiftKey) {
                                socket.send('games/demo_tool_edit', {game_id: this.game_id, coord: coord, color: 'o'});
                            } else {
                                socket.send('games/demo_tool_edit', {game_id: this.game_id, coord: coord, color: 'x'});
                            }
                        }
                        break;
                    case 'triangle':
                        socket.send('games/demo_tool_triangle', {game_id: this.game_id, coord: coord});
                        break;
                    case 'square':
                        socket.send('games/demo_tool_square', {game_id: this.game_id, coord: coord});
                        break;
                    case 'circle':
                        socket.send('games/demo_tool_circle', {game_id: this.game_id, coord: coord});
                        break;
                    case 'label':
                        socket.send('games/demo_tool_label', {game_id: this.game_id, coord: coord});
                        break;
                    case 'number':
                        socket.send('games/demo_tool_number', {game_id: this.game_id, coord: coord});
                        break;
                }
            },

            handle_player_click(coord, event, is_touch) {
                if (this.game.stage == 'counting') {
                    socket.send('games/toggle_marked_dead', {'game_id': this.game_id, 'coord': coord});
                } else if (this.game.stage != 'finished') {
                    socket.send('games/move', {'game_id': this.game_id, 'move': coord});
                }
            },

            share_coord(coord) {
                var coord_str = coord_to_str(coord, this.game.board.size);

                if(this.room_message.length > 0 && this.room_message[this.room_message.length-1] != ' ') {
                    this.room_message += ' ';
                }

                this.room_message += coord_str + ' ';

                jQuery(this.$els.game).find('.room-logs input[name=message]').focus();
            }
        }
    }
</script>
