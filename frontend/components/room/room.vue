<template>
    <div class="room-page" v-if="user.logged_in">
        <section class="content">
            <div class="row">
                <div class="flex-column col-sm-9 col-lg-10">
                    <qi-room-logs :room_id="$route.params.room_id"></qi-room-logs>
                </div>
                <div class="flex-column col-sm-3 col-lg-2">
                    <qi-room-users :room_id="$route.params.room_id"></qi-room-users>
                </div>
            </div>
        </section>
    </div>
</template>

<script>
    export default {
        mixins: [require('./../../mixins/title.vue')],

        vuex: {
            getters: {
                rooms: function(state) { return state.rooms }
            }
        },

        route: {
            canReuse: false
        },

        computed: {
            window_title() {
                return this.room.name;
            },

            room() {
                return this.rooms.find(room => { return room.id == this.$route.params.room_id; }) || {};
            }
        }
    }
</script>