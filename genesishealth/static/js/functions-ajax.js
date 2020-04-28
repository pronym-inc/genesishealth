var changeLock = false;

$(window).bind('hashchange', function(e) {
    if (changeLock) {
        return;
    }
    changeLock = true;
    var h = location.hash;
    if (h && h != '#menu') {
        link = h.replace(/^\#/, '');
        loadPageViaAjax(link);
    }
});

function goToLink(link) {
    window.location.hash = link;
    $(window).trigger('hashchange');
}

function loadPageViaAjax(link) {
    var id = link.replace(/[\/\.]/g, '-').replace(/(^-)|(-$)/g, '');
    ajaxSend(link, id);
}

function ajaxSubmitForm(e) {
    e.preventDefault();
    if (!$(this).get(0).checkValidity()) {
        return false;
    }
    var fileElements = $(':file', this);
    if (fileElements.length) {
        submitViaAjax($(this).attr('action'), $(this).serializeArray(), false, fileElements);
    } else {
        submitViaAjax($(this).attr('action'), $(this).serialize());
    }
    if ($(this).attr('action')) {
        window.location.hash = '#' + $(this).attr('action');
    }
}

function submitViaAjax(target, serializedData, skipRedirect, fileElements) {
    if (changeLock) {
        return;
    }
    changeLock = true;

    var h = window.location.hash;
    var link = h.replace(/^\#/, '');
    var id = link.replace(/[\/\.]/g, '-').replace(/(^-)|(-$)/g, '');
    if (target === '') {
        target = link;
    }
    target = target.replace(/^\/dashboard\/#/, '');
    if (!skipRedirect) {
        window.location.hash = '#' + target;
    }
    ajaxSend(target, id, 'POST', serializedData, fileElements);
}

function ajaxSend(target, id, type, serializedData, fileElements) {
    if (type === undefined) {
        type = 'GET';
    }

    var options = {
        type: type,
        url: target,
        dataType: 'html',
        cache: false,
        data: serializedData,
        success: function(data, textStatus, jqXHR) {
            try {
                var json = JSON.parse(data);
                changeLock = false;
                if (json.then_download) {
                    setTimeout(function() {
                        window.location = json.then_download;
                    });
                }
                if (json.raw_redirect) window.open(json.redirect);
                else {
                    window.location.hash = '#' + json.redirect;
                    $(window).trigger('hashchange');
                }
            }
            catch (e) {
                $('#' + id).length && $('#' + id).remove();
                return pageDownloaded(data, id, function() {
                    changeLock = false;
                });
            }
        },
        complete: function(jqXHR, textStatus) {
            $('.innerloader').hide();
            $('#tiptip_holder').hide();
        },
        statusCode: {
            404: function() {
                changeLock = false;
                if (id != '404') {
                    loadPageViaAjax('/404/');
                }
            },
            500: function() {
                changeLock = false;
                if (id != '500') {
                    loadPageViaAjax('/500/');
                }
            }
        },
        headers: {'dashboardreq': 'true'},
        cache: false
    };

    if (type == 'POST') {
        if (serializedData) {
            options['data'] = serializedData;
        }
        if (typeof fileElements != 'undefined') {
            options['files'] = fileElements;
            options['iframe'] = true;
            options['processData'] = false;
        }
    }

    $.ajax(options);
}
