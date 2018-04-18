<template>
    <h1>{{$t('search.header')}}</h1>

    <template v-if="loading">
        <qi-page-load-spinner></qi-page-load-spinner>
    </template>
    <template v-else>
        <template v-if="users.total_results == 0 && games.total_results == 0 && user.logged_in">
            <p class="text-center">
                <em>{{$t('search.no_results', {query: $route.params.query})}}</em>
            </p>
        </template>

        <div class="panel panel-default fixed-dropdowns" v-if="users.total_results > 0 && user.logged_in">
            <div class="panel-heading">
                <h3 class="panel-title">
                    <i class="fa fa-fw fa-users"></i>
                    {{$t('search.users')}} <small>({{users.total_results}})</small>
                </h3>
            </div>

            <div class="table-responsive">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th>{{$t('user.display')}}</th>
                            <th>{{$t('user.rank')}}</th>
                            <th>{{$t('user.member_since')}}</th>
                            <th>{{$t('user.last_activity')}}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="user in users.results">
                            <td><qi-user-context :user_id="user.id" :display="user.display"></qi-user-context></td>
                            <td><qi-rating-rank :rating="user.rating"></qi-rating-rank> ({{user.rating.toFixed(2)}})</td>
                            <td>{{format_datetime(user.created_at)}}</td>
                            <td><qi-user-last-activity :user="user"></qi-user-last-activity></td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="panel-footer text-center">
                <button @click="users_page(users.page-1)" class="btn btn-default btn-xs" :disabled="users.page <= 1">&laquo; {{$t('search.prev')}}</button>
                <button @click="users_page(users.page+1)" class="btn btn-default btn-xs" :disabled="users.page >= users.total_pages">{{$t('search.next')}} &raquo;</button>
            </div>
        </div>

        <div class="panel panel-default fixed-dropdowns search-games" v-if="games.total_results > 0 && user.logged_in">
            <div class="panel-heading">
                <h3 class="panel-title">
                    <i class="fa fa-fw fa-globe"></i>
                    {{$t('search.games')}} <small>({{games.total_results}})</small>
                </h3>
            </div>

            <div class="table-responsive">
                <table class="table table-hover table-striped">
                    <thead>
                        <tr>
                            <th>{{$t('game.white')}}</th>
                            <th>{{$t('game.black')}}</th>
                            <th>{{$t('game.type')}}</th>
                            <th>{{$t('game.speed')}}</th>
                            <th>{{$t('game.started')}}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="game in games.results" v-link="{name:'game', params:{game_id: game.id}}">
                            <template v-if="game.is_demo">
                                <td colspan="2">
                                    <qi-username-rank :display="game.demo_owner_display" :rating="game.demo_owner_rating"></qi-username-rank>
                                    <span v-if="game.demo_title">&mdash; {{game.demo_title}}</span>
                                </td>
                            </template>
                            <template v-else>
                                <td>
                                    <qi-username-rank :display="game.white_display" :rating="game.white_rating"></qi-username-rank>
                                </td>
                                <td>
                                    <qi-username-rank :display="game.black_display" :rating="game.black_rating"></qi-username-rank>
                                </td>
                            </template>
                            <td>
                                <qi-game-type :game="game"></qi-game-type>
                            </td>
                            <td>
                                <qi-game-speed :game="game"></qi-game-speed>
                            </td>
                            <td>{{format_datetime(game.created_at)}}</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="panel-footer text-center">
                <button @click="games_page(games.page-1)" class="btn btn-default btn-xs" :disabled="games.page <= 1">&laquo; {{$t('search.prev')}}</button>
                <button @click="games_page(games.page+1)" class="btn btn-default btn-xs" :disabled="games.page >= games.total_pages">{{$t('search.next')}} &raquo;</button>
            </div>
        </div>
    </template>
</template>
<script>
    import { format_datetime } from '../format';
    import * as socket from '../socket';

    export default {
        data() {
            return {
                loading: false,
                users: {},
                games: {}
            }
        },

        route: {
            data: function(transition) {
                this.loading = true;
                socket.send('search/all', {query: transition.to.params.query}, function(data) {
                    this.loading = false;
                    transition.next({users: data.users, games: data.games});
                }.bind(this));
            }
        },

        methods: {
            format_datetime: format_datetime,

            users_page(page) {
                socket.send('search/users', {query: this.$route.params.query, page: page}, function(data) {
                    this.$set('users', data);
                }.bind(this));
            },

            games_page(page) {
                socket.send('search/games', {query: this.$route.params.query, page: page}, function(data) {
                    this.$set('games', data);
                }.bind(this));
            }
        }
    }
</script>