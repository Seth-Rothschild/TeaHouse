import { is_tab_visible } from './visibility'

export function request_notify_permission() {
    Notification.requestPermission();
}

export function notify(message, onclick) {
    if(is_tab_visible()) {
        return;
    }
    
    if(!("Notification" in window)) {
        return;
    }
    
    var options = {
        body: message,
        icon: '/static/favicon/apple-touch-icon-precomposed.png'
    };

    var n = new Notification('Tea House', options);

    setTimeout(n.close.bind(n), 10000);

    n.onclick = function(ev) {
        window.focus();
        
        if(onclick) {
            onclick(ev);
        }
    }
}
