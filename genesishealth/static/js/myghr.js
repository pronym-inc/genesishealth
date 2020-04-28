$(document).ready(function() {

    // User navigation hover styling
    $('#user-navigation a').hover(function(e) {
        $(this).addClass('ui-state-hover');
    }, function(e) {
        $(this).removeClass('ui-state-hover');
    });
});
