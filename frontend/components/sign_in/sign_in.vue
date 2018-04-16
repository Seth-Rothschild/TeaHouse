<template>
    <div id="qi-sign-in" class="modal fade">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h4 class="modal-title">
                        {{(stage=='sign_in' ? $t('sign_in.header') :
                            ))}}
                    </h4>
                </div>

                <div class="modal-body signin-dialog">
                    <template v-if="stage=='sign_in'">
                        <p v-if="loginFailed" class="text-danger">
                            {{$t('sign_in.error')}}
                        </p>

                        <form @submit.prevent="sign_in" novalidate>
                            <div class="form-group has-feedback" :class="{'has-error': loginFailed}">
                                <input class="form-control input-lg" type="text" v-model="email" required autofocus
                                    placeholder="{{$t('sign_in.email')}}">
                                <span class="fa fa-user form-control-feedback"></span>
                            </div>

                            <div class="form-group has-feedback" :class="{'has-error': loginFailed}">
                                <input class="form-control input-lg" type="password" v-model="password" required
                                    placeholder="{{$t('sign_in.password')}}">
                                <span class="fa fa-lock form-control-feedback"></span>
                            </div>

                            <button type="submit" class="btn btn-lg btn-block btn-success" :disabled="signingIn">
                                <i v-if="signingIn" class="fa fa-spinner fa-spin"></i>
                                <span v-else>{{$t('sign_in.sign_in')}}</span>
                            </button>

                            <br/>
                        </form>
                    </template>

                    <template v-if="stage=='sign_up'">
                        <qi-sign-up></qi-sign-up>
                    </template>

                    <template v-if="stage=='forgot_password'">
                        <qi-forgot-password></qi-forgot-password>
                    </template>

                    <template v-if="stage=='password_reset'">
                        <qi-pasword-reset></qi-pasword-reset>
                    </template>
                </div>

                <div class="modal-footer">
                    <button class="btn btn-default" data-dismiss="modal">
                        {{$t('sign_in.close')}}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    export default {
        data() {
            return {
                stage: 'sign_in',
                email: '',
                password: '',
                loginFailed: false
            }
        },

        ready() {
            jQuery('#qi-sign-in').on('hidden.bs.modal', () => {
                this.stage = 'sign_in';
            });
        },

        methods: {
            sign_in() {
                this.loginFailed = false;

                this.$http.post('/api/auth/sign-in', {email: this.email, password: this.password}).then(function() {
                    document.location.reload();
                }, function() {
                    this.loginFailed = true;
                });
            }
        },

        components: {
            'qi-sign-up': require('./sign_up.vue'),
            'qi-forgot-password': require('./forgot_password.vue')
        }
    }
</script>
