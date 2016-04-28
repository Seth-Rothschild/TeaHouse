import Vue from 'vue';
import VueRouter from 'vue-router';

Vue.use(VueRouter);

export default function configRouter() {
    var router = new VueRouter({
        history: true,
        saveScrollPosition: true,
        linkActiveClass: 'active'
    });
    
    router.map({
        '/': {
            name: 'root',
            component: require('./components/home.vue')
        },
        '/settings': {
            name: 'settings',
            component: require('./components/settings/settings.vue')
        },
        '/faq': {
            name: 'faq',
            component: require('./components/faq.vue')
        },
        '/rooms/:room_id': {
            name: 'room',
            component: require('./components/room/room.vue')
        },
        '/users/:user_id': {
            name: 'user',
            component: require('./components/user/profile.vue')
        },
        '/users/:user_id/message': {
            name: 'user_message',
            component: require('./components/user/message.vue')
        },
        '/games': {
            name: 'active_games',
            component: require('./components/active_games.vue')
        },
        '/games/:game_id': {
            name: 'game',
            component: require('./components/game/game.vue')
        },
        '/password-reset-confirm/:status': {
            component: require('./components/password_reset_confirm.vue')
        }
    });

    return router;
}
