<template>
    <div class="main-header">
        <nav class="navbar navbar-default navbar-fixed-top">
            <div class="container-fluid">
                <div class="navbar-header pull-left">
                    <a class="navbar-brand" v-link="'/'">Tea House</a>

                    <a href="javascript:void(0)" @click="toggle_sidebar()" class="sidebar-toggle">
                        <span class="divider"></span>
                        <span class="toggle"></span>
                        <span class="divider"></span>
                    </a>
                </div>

                <ul class="nav navbar-dropdown pull-right">
                    <li class="dropdown">
                        <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                            <i class="fa fa-cog fa-fw"></i>
                        </a>
                        <ul class="dropdown-menu dropdown-menu-right">
                            <template v-if="user.logged_in">
                                <li>
                                    <a v-link="{name:'user', params:{user_id:user.user_id}}">
                                       <i class="fa fa-user fa-fw"></i> {{$t('header.profile')}}
                                    </a>
                                </li>

                                <li>
                                    <a v-link="'/settings'">
                                        <i class="fa fa-cog fa-fw"></i> {{$t('header.settings')}}
                                    </a>
                                </li>

                                <li class="divider"></li>
                            </template>

                            <!-- TODO: not implemented yet
                            <li><a href="#"><i class="fa fa-users fa-fw"></i> Rooms</a></li>
                            <li><a href="#"><i class="fa fa-user-plus fa-fw"></i> Friends</a></li>

                            <li class="divider"></li>
                            -->

                            <li>
                                <a v-link="'/faq'">
                                    <i class="fa fa-question-circle fa-fw"></i> {{$t('header.help')}}
                                </a>
                            </li>

                            <template v-if="user.logged_in">
                                <li class="divider"></li>

                                <li>
                                    <a href="/api/auth/logout">
                                        <i class="fa fa-sign-out"></i> {{$t('header.logout')}}
                                    </a>
                                </li>
                            </template>
                        </ul>
                    </li>
                </ul>

                <ul class="nav navbar-nav navbar-right pull-right">
                    <li class="search-toggle visible-xs">
                        <a href="javascript:void(0)" @click="toggle_search"><i class="fa fa-search"></i></a>
                    </li>
                </ul>

                <p class="navbar-text navbar-right pull-right">
                    <qi-connectivity></qi-connectivity>
                </p>

                <form class="navbar-form navbar-right main-search pull-right" @submit.prevent="submit_search">
                    <div class="input-group">
                        <input type="text" class="form-control" placeholder="{{$t('header.search')}}" autocomplete="off"
                               v-model="search_query">
                        <div class="input-group-btn">
                            <button class="btn btn-default"><i class="fa fa-search"></i></button>
                        </div>
                    </div>
                </form>
            </div>
        </nav>
    </div>
</template>

<script>
    import { toggle_sidebar } from './../vuex/actions';

    export default {
        data() {
            return {
                search_query: ''
            }
        },

        vuex: {
            getters: {
                user: function(state) { return state.auth.user; }
            },
            actions: {
                toggle_sidebar
            }
        },

        components: {
            'qi-connectivity': require('./connectivity.vue')
        },

        methods: {
            toggle_search() {
                jQuery('.main-search').slideToggle(300);
            },

            submit_search() {
                if(this.search_query != '') {
                    this.$router.go({name: 'search', params: {query: this.search_query}});
                    this.search_query = '';

                    if(jQuery('.search-toggle').is(':visible')) {
                        jQuery('.main-search').slideUp(300);
                    }
                }
            }
        }
    }
</script>