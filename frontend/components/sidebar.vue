<template>
    <aside class="main-sidebar sidebar">
        <div class="user-panel">
            <template v-if="user.logged_in">
                <div class="pull-left image">
                    <a v-link="{name:'user', params:{user_id:user.user_id}}">
                        <img :src="'/api/users/'+user.user_id+'/avatar'" class="avatar">
                    </a>
                </div>
                <div class="pull-left info">
                    <p>
                        <a v-link="{name:'user', params:{user_id:user.user_id}}">{{user.user_display}}</a>
                    </p>

                    <span>
                        <i class="fa fa-trophy"></i>
                        {{user.wins}}
                        &mdash;
                        <qi-rating-rank v-if="user.rating != null" :rating="user.rating"></qi-rating-rank>
                    </span>
                </div>

                <div class="clearfix"></div>
            </template>

            <div class="user-buttons">
                <button type="button" class="btn btn-success btn-block" data-toggle="modal" data-target="#qi-sign-in" v-if="!user.logged_in">
                    {{$t('sidebar.sign_in')}}
                </button>

                <div class="btn-group btn-block" v-if="user.logged_in">
                    <template v-if="user.logged_in">
                        <button type="button" class="btn btn-primary dropdown-toggle col-xs-10" data-toggle="dropdown">
      		            {{$t('sidebar.play')}}
                        </button>
                        <ul class="dropdown-menu col-xs-12">
                            <li>
                                <a href="#" data-toggle="modal" data-target="#qi-challenge">
                                    <i class="fa fa-fw fa-trophy"></i>
                                    {{$t('sidebar.challenge')}}
                                </a>
                            </li>
                            <li>
                                <a href="#" data-toggle="modal" data-target="#qi-create-demo">
                                    <i class="fa fa-fw fa-desktop"></i>
                                    {{$t('sidebar.create_demo')}}
                                </a>
                            </li>
                            <li>
                                <a href="#" data-toggle="modal" data-target="#qi-upload-sgf">
                                    <i class="fa fa-fw fa-upload"></i>
                                    {{$t('sidebar.upload_sgf')}}
                                </a>
                            </li>

                        </ul>


                    </template>
		    

                    <template v-if="user.automatch">
                        <button type="button" class="btn btn-primary col-xs-2" data-toggle="modal" @click="cancel_automatch">
                            <i class="fa fa-spinner fa-spin"></i>&nbsp;&nbsp;
                            {{$t('sidebar.searching_automatch')}}
                        </button>
                    </template>
		    <template v-else>
		        <button type="button" class="btn btn-primary col-xs-2" data-toggle="modal" data-target="#qi-play-dialog">
		            <span class="caret"></span>
                        </button>
		    </template>
                </div>
            </div>
        </div>

        <ul class="sidebar-menu" v-if="user.logged_in>
            <li v-link-active>
                <a v-link="{name:'active_games', exact: true}">
                    <i class="fa fa-globe"></i>
                    {{$t('sidebar.active_games')}}
                    <span class="sidebar-item-extra pull-right">({{active_games.length}})</span>
                    <div class="clearfix"></div>
                </a>
            </li>
        </ul>

        <ul class="sidebar-menu" v-if="challenges.length > 0">
            <li class="header">{{$t('sidebar.challenges')}}</li>

            <template v-for="challenge in challenges">
                <li v-link-active>
                    <a v-link="{name: 'challenge', params: {'challenge_id': challenge.id}}">
                        <i class="fa fa-trophy"></i>

                        <span v-if="challenge.owner_id == user.user_id">{{challenge.challengee_display}}</span>
                        <span v-else>{{challenge.owner_display}}</span>

                        <!--<span class="sidebar-item-action pull-right" @click.prevent="close_challenge(challenge.id)">
                            <i class="fa fa-times-circle"></i>
                        </span>-->
                    </a>
                </li>
            </template>
        </ul>

        <ul class="sidebar-menu" v-if="user.logged_in">
            <li class="header">{{$t('sidebar.games')}}</li>

            <template v-for="game in sorted_games">
                <li v-link-active>
                    <a v-link="{name: 'game', params:{game_id: game.id}}">
                        <i :class="{'text-info': game.is_demo || (game.stage!='finished' && !game_has_warning[game.id]),
                            'text-warning': game.stage!='finished' && game_has_warning[game.id]}"
                            class="fa fa-circle"></i>

                        <span v-if="game.is_demo" class="sidebar-item-text">{{game.demo_owner_display}}</span>
                        <span v-else class="sidebar-item-text">{{game.white_display}} &mdash; {{game.black_display}}</span>

                        <span class="sidebar-item-action pull-right" v-if="can_close_game(game.id)" @click.prevent="close_game(game.id)">
                            <i class="fa fa-times-circle"></i>
                        </span>

                        <div class="clearfix"></div>
                    </a>
                </li>
            </template>

            <li v-if="open_games_list.length == 0">
                <span class="sidebar-text">{{$t('sidebar.no_games')}}</span>
            </li>
        </ul>

        <ul class="sidebar-menu" v-if="user.logged_in">
            <li class="header">{{$t('sidebar.rooms')}}</li>
            <template v-for="room in main_rooms">
                <li v-if="room.type=='main'" v-link-active :class="{highlight: room_has_update[room.id]}">
                    <a v-link="{name:'room', params:{room_id: room.id}}">
                        <i :class="{'text-info': room_has_update[room.id]}" class="fa fa-users"></i>
                        <span class="sidebar-item-text">{{room.name}}</span>
                        <div class="clearfix"></div>
                    </a>
                </li>
            </template>
        </ul>

        <ul class="sidebar-menu" v-if="user.logged_in">
            <li class="header">{{$t('sidebar.people')}}</li>

            <template v-for="room in sorted_direct_rooms">
                <li v-link-active :class="{highlight: room_has_update[room.room_id]}">
                    <a v-link="{name:'user_message', params:{user_id:room.other_user_id}}">
                        <i :class="{'text-success': room.is_online, 'text-info': room_has_update[room.room_id]}" class="fa fa-user"></i>
                        <span class="sidebar-item-text">{{room.other_display}}</span>

                        <span class="sidebar-item-action pull-right" @click.prevent="close_direct_room(room.other_user_id)">
                            <i class="fa fa-times-circle"></i>
                        </span>

                        <div class="clearfix"></div>
                    </a>
                </li>
            </template>

            <li v-if="no_direct_rooms">
                <span class="sidebar-text">{{$t('sidebar.no_direct_rooms')}}</span>
            </li>
        </ul>

        <hr>

        <ul class="list-inline list-unstyled text-center">
            <li>
                <a href="https://github.com/Seth-Rothschild/TeaHouse" target="_blank"><i class="fa fa-github"></i></a>
            </li>
        </ul>

        <p class="text-center">
            <small>&copy; Copyright 2018 Seth Rothschild</small>
            <br><br>
        </p>
    </aside>
</template>

<script>
    import { close_game, close_direct_room } from '../vuex/actions';
    import { is_current_player } from '../game';
    import * as socket from '../socket';

    export default {
        vuex: {
            getters: {
                user: function(state) { return state.auth.user; },
                active_games: function(state) { return state.active_games; },
                rooms: function(state) { return state.rooms; },
                direct_rooms: function(state) { return state.direct_rooms; },
                open_games: function(state) { return state.open_games; },
                room_has_update: function(state) { return state.room_has_update; },
                game_has_update: function(state) { return state.game_has_update; },
                challenges: function(state) { return state.challenges; }
            },

            actions: {
                close_game,
                close_direct_room
            }
        },

        computed: {
            main_rooms() {
                return this.rooms.filter(function(room) {
                    return room.type == 'main';
                });
            },

            open_games_list() {
                return Object.keys(this.open_games).map(function(key) {
                    return this.open_games[key];
                }.bind(this));
            },

            sorted_games() {
                return this.open_games_list.sort(function(g1, g2) {
                    var g1_active = (g1.is_demo ? true : g1.stage == 'playing');
                    var g2_active = (g2.is_demo ? true : g2.stage == 'playing');
                    if(g1_active != g2_active) {
                        return g2_active - g1_active;
                    }

                    var g1_player = this.is_player(g1) || this.is_owner(g1);
                    var g2_player = this.is_player(g2) || this.is_owner(g2);
                    if(g1_player != g2_player) {
                        return g2_player - g1_player;
                    }

                    return g2.id - g1.id;
                }.bind(this));
            },

            sorted_direct_rooms() {
                var direct = Object.keys(this.direct_rooms).map(function(key) {
                    return this.direct_rooms[key];
                }.bind(this));

                return direct.sort(function(d1, d2) {
                    if(d1.is_online != d2.is_online) {
                        return d2.is_online - d1.is_online;
                    }

                    return (''+d1.other_display).localeCompare(d2.other_display);
                });
            },

            no_direct_rooms() {
                return !this.direct_rooms || Object.keys(this.direct_rooms).length==0
            },

            game_has_warning() {
                var warnings = {};

                this.open_games_list.forEach(function(game) {
                    if (is_current_player(game, game.board.current_node_id, this.user.user_id)) {
                        warnings[game.id] = true;
                    } else {
                        warnings[game.id] = this.game_has_update[game.id];
                    }
                }.bind(this));

                return warnings;
            }
        },

        methods: {
            cancel_automatch() {
                socket.send('play/cancel_automatch');
            },

            can_close_game(game_id) {
                var game = this.open_games[game_id];

                if(!game) {
                    return true;
                }

                if(game.is_demo) {
                    return true;
                }

                return !this.is_player(game) || game.stage == 'finished';
            },

            is_player(game) {
                if(!this.user.logged_in) {
                    return false;
                }

                return (this.user.user_id == game.black_user_id || this.user.user_id == game.white_user_id);
            },

            is_owner(game) {
                return (game.is_demo && game.demo_owner_id == this.user.user_id);
            }
        }
    }
</script>
