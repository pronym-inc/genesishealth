var SessionTimer = (function($) {
    var timerStart,
        optionDefaults = {
            maxSessionSeconds: 60 * 15,
            logoutURL: '/accounts/logout/'
        };

    function resetTimer() {
        timerStart = (new Date).getTime();
    }

    function initTimer(options) {
        var options = $.extend(optionDefaults, options);
        var maxSession = options.maxSessionSeconds * 1000;

        setInterval(function() {
            if ((new Date).getTime() - timerStart > maxSession) {
                window.location = options.logoutURL;
            }
        }, 1000);

        resetTimer();
    }

    return {
        'reset': resetTimer,
        'init': initTimer,
    }
}(jQuery));
