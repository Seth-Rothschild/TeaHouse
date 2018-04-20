<template>
    <div v-if="user.id && auth_user.logged_in" class="qi-profile">
        <div class="row">
            <div class="col-sm-4">
                <p class="text-center">
                    <img height="256" width="256" class="avatar" :src="'/api/users/'+user.id+'/avatar?size=large'">
                </p>
            </div>

            <div class="col-sm-8">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h1 class="panel-title pull-left">#{{user.id}} &mdash; {{user.display}}</h1>

                        <span class="pull-right" v-if="!is_self">
                            <a v-link="{name: 'user_message', params: {user_id: user.id}}" class="btn btn-default btn-xs">
                                <i class="fa fa-fw fa-envelope"></i> {{$t('user.send_message')}}
                            </a>
                        </span>
                        <div class="clearfix"></div>
                    </div>

                    <div class="panel-body">
                        <div class="row">
                            <div class="col-xs-6">{{$t('user.member_since')}}</div>
                            <div class="col-xs-6">{{format_datetime(user.created_at)}}</div>
                        </div>

                        <div class="row">
                            <div class="col-xs-6">{{$t('user.last_activity')}}</div>
                            <div class="col-xs-6"> <qi-user-last-activity :user="user"></qi-user-last-activity></div>
                        </div>

                        <div class="row">
                            <div class="col-xs-6">{{$t('user_detail.rank')}}</div>
                            <div class="col-xs-6">
                                <qi-rating-rank :rating="user.rating"></qi-rating-rank>
                                ({{user.rating.toFixed(2)}})
                            </div>
                        </div>

                        <template v-if="user.info_text_html">
                            <hr>
                            {{{user.info_text_html}}}
                        </template>
                    </div>
                </div>
            </div>
        </div>

        <div class="panel panel-default fixed-dropdowns">
            <div class="panel-heading">
                <h3 class="panel-title">{{$t('user_detail.games')}}</h3>
            </div>

            <div class="table-responsive">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th>{{$t('game.white')}}</th>
                            <th>{{$t('game.black')}}</th>
                            <th>{{$t('game.result')}}</th>
                            <th>{{$t('game.type')}}</th>
                            <th>{{$t('game.speed')}}</th>
                            <th>{{$t('game.date')}}</th>
                            <th>&nbsp;</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="game in games">
                            <template v-if="game.is_demo">
                                <td>{{$t('game.demo')}}</td>
                                <td>{{game.demo_title}}</td>
                            </template>
                            <template v-else>
                                <td :class="{winner: game.result.startsWith('W+')}">
                                    <qi-user-context :user_id="game.white_user_id" :display="game.white_display" :rating="game.white_rating"></qi-user-context>
                                </td>
                                <td :class="{winner: game.result.startsWith('B+')}">
                                    <qi-user-context :user_id="game.black_user_id" :display="game.black_display" :rating="game.black_rating"></qi-user-context>
                                </td>
                            </template>
                            <td>{{game.result || '-'}}</td>
                            <td>
                                <qi-game-type :game="game"></qi-game-type>
                            </td>
                            <td>
                                <qi-game-speed :game="game"></qi-game-speed>
                            </td>
                            <td>{{format_datetime(game.created_at)}}</td>
                            <td class="text-right">
                                <div class="btn-group">
                                    <a v-link="{name:'game', params:{game_id:game.id}}" class="btn btn-default btn-xs">
                                        <i class="fa fa-fw fa-file"></i>
                                        {{$t('game.open')}}
                                    </a>

                                    <button type="button" class="btn btn-default btn-xs dropdown-toggle" data-toggle="dropdown">
                                        <span class="caret"></span>
                                    </button>
                                    <ul class="dropdown-menu dropdown-menu-right">
                                        <li v-if="!is_self || !game.is_demo">
                                            <a href="javascript:void(0)" @click="create_demo(game.id)">
                                                <i class="fa fa-fw fa-desktop"></i>
                                                {{$t('game.clone_demo')}}
                                            </a>
                                        </li>
                                        <li>
                                            <a :href="'/api/games/'+game.id+'/sgf'" target="_blank">
                                                <i class="fa fa-fw fa-download"></i>
                                                {{$t('game.download_sgf')}}
                                            </a>
                                        </li>
                                    </ul>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</template>

<script>
    import { create_demo } from '../../vuex/actions';
    import { format_datetime } from '../../format';
    import * as socket from '../../socket';

    export default {
        mixins: [require('./../../mixins/title.vue')],

        data() {
            return {
                user: {},
                games: []
            }
        },

        vuex: {
            getters: {
                auth_user: function (state) {
                    return state.auth.user
                },
            },

            actions: {
                create_demo
            }
        },

        route: {
            canReuse: false
        },

        ready() {
            socket.send('users/profile', {'user_id': this.user_id}, function(data) {
                this.user = data;
            }.bind(this));

            socket.send('users/games', {'user_id': this.user_id}, function(data) {
                this.games = data;
            }.bind(this));
        },

        computed: {
            window_title() {
                return this.user.user_id;
            },

            user_id() {
                return this.$route.params.user_id;
            },

            is_self() {
                return this.user_id == this.auth_user.user_id;
            }
        },

        methods: {
            format_datetime: format_datetime
        }
    }
</script>