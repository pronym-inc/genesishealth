SessionTimer.init({logoutURL: '/dashboard/#/accounts/logout/?timeout'});

updateCallbackQueue = new CallbackQueue('ghtupdate');
postCallbackQueue = new CallbackQueue('ghtpostupdate');

function removeContent(target) {
    $('> div:last', target).siblings().each(function() {
        /* */
    }).remove();
}

function pageDownloaded(data, id, callback) {
    SessionTimer.reset();

    var target = '#main-content',
    div = $('<div style="left: 100%" id="' + id + '">' + data + '</div>');
    div.appendTo($(target));
    title = $(div).find('h1.page-title').html();
    $('#wrapper > section > section > header h1').html(title);

    updateCallbackQueue.process(div);
    styleForms(div);

    if (location.href.match(/setup\_security\/$/i)) {
        $('.drilldownMenu').hide();
    } else {
        $('.drilldownMenu').show();
    }

    if ($('#wrapper > section > section').css('position') == 'absolute') {
        $('> div:last', target).css({left: 0, position: 'relative'});
        removeContent(target);
        $('#wrapper > section > section').show().animate({left: 0}, 300, 'easeInOutQuart', function() {
            $(this).css('left', 0);
            callback();
            postCallbackQueue.process(div);
        });
    } else {
        $('> div', target).animate({left: '-=100%'}, 'slow', 'easeInOutQuart', function() {
            $(this).css('left', 0);
            $('#freeze-clicks').fadeOut('fast');
            $('> div:last', target).css({position: 'relative'});
            removeContent(target);
            //fix radio buttons on page load
            $('#customradio, #devicestateradio').buttonset();
            $('#view8').click(function() {
                 $('#logbook4_wrapper').hide();
                 $('#logbook8_wrapper').show();
            });
            $('#view4').click(function() {
                $('#logbook8_wrapper').hide();
                $('#logbook4_wrapper').show();
            });
            callback();
            postCallbackQueue.process(div);
         });

         // Reinitialize tipTip on pageload due to ajax
         $('.tipTip').tipTip();

         // Change form inputs that are for email to type email
         if ($('#id_email').length) {
              document.getElementById('id_email').setAttribute('type', 'email');
         }

         if ($('#id_confirm_email').length) {
              document.getElementById('id_confirm_email').setAttribute('type', 'email');
         }
    }

    $(window).trigger('drilldown');
}

// Format date time fields
// This sets time picker - if there's an error, it tries unsetting it and trying again.
function setAnyTimePicker(objset, options, second_try) {
    try {
        objset.AnyTime_picker(options);
    } catch (e) {
        if (!second_try) {
            objset.AnyTime_noPicker();
            // Try, try again
            setAnyTimePicker(objset, options, true);
        }
    }
}

function styleForms(div) {
    // Append asterisks to required fields on forms.
    div.find('form.form p.required label').each(function() {
        var html = $(this).html();
        if (html && !html.match(/\<em\>\*\<\/em\>/)) {
            $(this).append(' <em>*</em>');
        }
    });

    div.find('form.form p label').each(function() {
        var for_t = $(this).attr('for');
        var thisParent = $(this).parent();
        if (thisParent.find('#' + for_t).length === 0 && thisParent.next('ul').find('#' + for_t).length > 0) {
            $(this).after(thisParent.next('ul').find('#' + for_t).parents('ul'));
        }
    });

    // For some reason Django is inserting empty p's which are messing up layout.
    div.find('form.form p').each(function() {
        if ($(this).html() == '') {
            $(this).remove();
        }
    });

    setAnyTimePicker(div.find('form.form').find('.dateField:input').not('.DOBField'), {
        format: '%m/%d/%Y',
        earliest: new Date((new Date().getTime() - 365 * 2 * 24 * 60 * 60 * 1000))
    });

    setAnyTimePicker(div.find('form.form').find('.DOBField:input'), {
        format: '%m/%d/%Y',
        earliest: new Date(1900, 1, 1),
        latest: new Date()
    });

    setAnyTimePicker(div.find('form.form').find('.dateTimeField:input'), {
        format: '%m/%d/%Y %h:%i %p',
        earliest: new Date((new Date().getTime() - 365 * 24 * 60 * 60 * 1000)),
        askSecond: false
    });

    setAnyTimePicker(div.find('form.form').find('.timeField:input'), {
        format: '%h:%i %p'
    });

    div.find('input[type="submit"].deleteButton').click(function(e) {
        e.preventDefault();
        goToLink($(this).attr('target'));
    });

    div.find('input[type="submit"].include').click(function(e) {
        $(this).parents('form').append('<input type="hidden" name="' + $(this).attr('name') + '" value="' + $(this).attr('value') + '" />');
    });

    div.find('input:checkbox,input:radio,select,input:file').not('select[multiple]').not('.noUniform').each(function() {
        $(this).uniform();
    });

    div.find('input:hidden').removeAttr('required');

    div.find(':input.hiddenInput').each(function() {
        $(this).parents('p').hide();
    });

    // Add masks
    $(':input.phone').mask('(999) 999-9999');
    $(':input.zip').mask('99999');

    PhoneWidget.init();
}

function getReportQueryStr() {
    var query = [];
    var startDate = new Date($('#startDate').val());
    var endDate = new Date($('#endDate').val());
    query.push('start_date=' + encodeURIComponent($.datepicker.formatDate('mm/dd/yy', startDate)));
    query.push('end_date=' + encodeURIComponent($.datepicker.formatDate('mm/dd/yy', endDate)));
    return query.join('&');
};
