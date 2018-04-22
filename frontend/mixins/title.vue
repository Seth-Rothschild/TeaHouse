<script>
    import { add_visibility_event_listener, remove_visibility_event_listener, is_tab_visible } from '../visibility';

    export default {
        vuex: {
            getters: {
                rooms: function(state) { return state.rooms },
                room_has_update: function(state) { return state.room_has_update; }
            }
        },

        ready() {
            this.set_window_title();
            add_visibility_event_listener(this.visibility_change);
        },

        destroyed() {
            remove_visibility_event_listener(this.visibility_change);
        },

        watch: {
            'window_title': function() {
                this.set_window_title();
            },

            'has_updates': function() {
                this.set_window_title();
            }
        },

        computed: {
            has_updates() {
                var room = Object.keys(this.room_has_update).find(function(room_id) {
                    if(!this.room_has_update[room_id]) {
                        return false;
                    }

                    var room = this.rooms.find(function(room) {
                        return room.id == room_id;
                    });

                    return !room || room.type != 'game';
                }.bind(this));

                return !!room;
            }
        },

        methods: {
            set_window_title() {
                if(!is_tab_visible() && this.has_updates) {
                    document.title = 'New message - Tea House';
                } else {
                    if (!this.window_title) {
                        document.title = 'A quiet place to play go';
                    } else {
                        document.title = this.window_title + ' - Tea House';
                    }
                }
            },

            visibility_change() {
                this.set_window_title();
            }
        }
    }
</script>
