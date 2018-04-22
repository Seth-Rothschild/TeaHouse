<template>
    <div class="panel panel-default">
        <div class="panel-heading">
            <h1 class="panel-title">
                {{$t('faq.header')}}
                <small>{{$t('faq.subheader')}}</small>
            </h1>
        </div>

        <ul class="list-group">
            <li class="list-group-item">
                <h4 id="contribute">
                    {{$t('faq.contribute.header')}}
                    <a href="#contribute" class="header-anchor"></a>
                </h4>
                <p>{{{$t('faq.contribute.text.p1')}}}</p>
                <p>{{{$t('faq.contribute.text.p2')}}}</p>
            </li>

            <li class="list-group-item">
                <h4 id="bug">
                    {{$t('faq.bug.header')}}
                    <a href="#bug" class="header-anchor"></a>
                </h4>
                <p>{{{$t('faq.bug.text.p1')}}}</p>
            </li>

            <li class="list-group-item">
                <h4 id="ruleset">
                    {{$t('faq.ruleset.header')}}
                    <a href="#ruleset" class="header-anchor"></a>
                </h4>
                <p>{{{$t('faq.ruleset.text.p1')}}}</p>
            </li>

        </ul>
    </div>
</template>

<script>
    export default {
        mixins: [require('./../mixins/title.vue')],

        computed: {
            window_title() {
                return this.$t('faq.header');
            }
        },

        ready() {

        }
    }
</script>