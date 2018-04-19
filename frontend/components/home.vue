<template>
    <h1>Tea House</h1>

    <div class="row">
        <div class="col-sm-4 col-sm-push-8">
            <div class="panel panel-default">
                <div class="panel-heading">{{$t('dashboard.stats.heading')}}</div>
                <table class="table">
                    <tr>
                        <td>{{$t('dashboard.stats.users')}}</td>
                        <td>{{stats.users}}</td>
                    </tr>
                    <tr>
                        <td>{{$t('dashboard.stats.online')}}</td>
                        <td>{{stats.online}}</td>
                    </tr>
                    <tr>
                        <td>{{$t('dashboard.stats.games')}}</td>
                        <td>{{stats.games}}</td>
                    </tr>
                </table>
            </div>
        </div>
        <div class="col-sm-8 col-sm-pull-4">
            <div class="panel panel-default" v-if="user.logged_in">
                <div class="panel-heading">{{$t('dashboard.popular_games')}}</div>
                <div class="panel-body">
                    <div v-for="game in popular_games">
                        <div class="row">
                            <template v-if="game.is_demo">
                                <div class="col-xs-4 text-center">
                                    <img :src="'/api/users/'+game.demo_owner_id+'/avatar'" class="avatar">
                                    <h4>
                                        <qi-username-rank :display="game.demo_owner_display" :rating="game.demo_owner_rating"></qi-username-rank>
                                    </h4>
                                </div>
                                <div class="col-xs-8">
                                    <p class="small">{{moment(game.created_at).local().format('YYYY-MM-DD HH:mm')}}</p>
                                    <p class="lead">
                                        <span v-if="game.title">{{game.title}}</span>
                                        <span v-else>{{$t('game.demo')}}</span>
                                    </p>
                                    <a v-link="{name: 'game', params:{game_id: game.id}}" class="btn btn-default">
                                        {{$t('game.open')}}
                                    </a>
                                </div>
                            </template>
                            <template v-else>
                                <div class="col-xs-4 text-center">
                                    <img :src="'/api/users/'+game.white_user_id+'/avatar'" class="avatar">
                                    <h4>
                                        <qi-username-rank :display="game.white_display" :rating="game.white_rating"></qi-username-rank>
                                    </h4>
                                </div>
                                <div class="col-xs-4 text-center">
                                    <p class="small">{{moment(game.created_at).local().format('YYYY-MM-DD HH:mm')}}</p>
                                    <p class="lead"><br>VS</p>
                                    <br>
                                    <a v-link="{name: 'game', params:{game_id: game.id}}" class="btn btn-default">
                                        {{$t('game.open')}}
                                    </a>
                                </div>
                                <div class="col-xs-4 text-center">
                                    <img :src="'/api/users/'+game.black_user_id+'/avatar'" class="avatar">
                                    <h4>
                                        <qi-username-rank :display="game.black_display" :rating="game.black_rating"></qi-username-rank>
                                    </h4>
                                </div>
                            </template>
                        </div>
                        <hr>
                    </div>
                </div>
            </div>
            <div class="panel panel-default" v-else>
	    	<div class="panel-heading">Welcome!</div>
                <div class="panel-body">
		     <p>
		         This is a private server whose purpose is to provide a pleasant place to play go. For more project details, see the README on github or the FAQ on the same page. 
		    </p>
		    <p>
		         The source code for <i>Tea House</i> is a fork of Michael Bitzi's weiqi.gs. Though access to this particular serve is limited, the code is open source and copyleft under AGPLv3. 
	            </p>
		</div>
	    </div>
        </div>
    </div>
</template>

<script>
    import moment from 'moment';
    import * as socket from '../socket';

    export default {
        mixins: [require('./../mixins/title.vue')],

        data () {
            return {
                popular_games: [],
                stats: {}
            }
        },

	vuex: {
            getters: {
                user: function(state) { return state.auth.user; }
            },
	},

        ready() {
            socket.send('dashboard/popular_games', {}, function(games) {
                this.popular_games = games;
            }.bind(this));

            socket.send('dashboard/stats', {}, function(stats) {
                this.stats = stats;
            }.bind(this));
        },

        methods: {
            'moment': moment.utc
        }
    }
</script>
