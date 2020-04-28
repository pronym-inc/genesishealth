$(function() {
    /**
     * Form Validators
     */
    $.tools.validator.fn('[type=time]', 'Please supply a valid time', function(input, value) {
        return (/^\d\d:\d\d$/).test(value);
    });

    $.tools.validator.fn('[data-equals]', 'Value not equal with the $1 field', function(input) {
        var name = input.attr('data-equals'),
        field = this.getInputs().filter('[name=' + name + ']');
        return input.val() === field.val() ? true : [name];
    });

    $.tools.validator.fn('[minlength]', function(input, value) {
        var min = input.attr('minlength');
        return value.length >= min ? true : {
            en: 'Please provide at least ' + min + ' character' + (min > 1 ? 's' : '')
        };
    });

    $.tools.validator.localizeFn('[type=time]', {
        en: 'Please supply a valid time'
    });

    $().UItoTop({easingType: 'easeOutQuart'});

    $(window).bind('load resize', function() {
        var section = $('#wrapper > section > section');
        if (section.css('position') == 'absolute' && section.css('left') != 0) {
            if (location.hash != '#menu') {
                section.css('left', 0);
            } else {
                section.css('left', '100%');
            }
        } else {
            section.show();
        }
    });

    if (!location.href.match(/login\.html$/i) && (!location.hash || location.hash == '#menu')) {
        location.hash = $('.drilldownMenu .current a').attr('href').replace(/.+?#/, '');
    } else {
        $(window).trigger('hashchange');
    }

    $('#wrapper > section > aside > nav').length && $('#wrapper > section > aside > nav').each(function() {
        $(this).drillDownMenu();
    });

    $('.showmenu').click(function() {
        $('#wrapper > section > section').animate({left: '100%'}, 300, 'easeInOutQuart', function() {
            $(this).hide();
        });
    });

    var target = '.login-box';
    $('input[placeholder]', target).placeholder();
    $('input[type=date]', target).dateinput();

    // Figure out what menu item should be highlighted.
    $('ul.tlm li').each(function() {
        // check to see if the link matches the URL, if so give it "current" class.
        var href = $(this).find('a').attr('href');
        if (href && href.replace('/dashboard/', '') == window.location.hash) {
            $(this).addClass('current');
        }
        else if ($(this).hasClass('current')) {
            $(this).removeClass('current');
        }
    });

    // Temporarily disabled since we're not using notifications.
    // Remember to include /static/js/notifications.js when enabling.
    // setInterval(updateNotifications, 2000);

    $('form[method="post"]').live('submit', ajaxSubmitForm);

    $('.device-unassign-link').live('click', function(e) {
        e.preventDefault();
        var siblingSelect = $(this).siblings('div').children('select:first');
        if (siblingSelect.children('option[value="UNASSIGN"]').length == 0) {
            siblingSelect.prepend('<option value="">Unassigned (Save to commit this change)</option>');
        }
        siblingSelect.val('');
        $.uniform.update('#' + siblingSelect.attr('id'));
        $(this).prev('div.selector').hide().after('<span style="color:red">This device has been unassigned.  You must save for this change to take effect.</span>');
        $(this).hide().next('span').hide();
    });

    $('a').live('click', function(e) {
        var href = $(this).attr('href');
        if (href == '#' || href === undefined) {
            return;
        }
        $(this).parent().children('.innerloader').show();
        if ($(this).parents('aside').length) {
            $('#freeze-clicks').fadeIn('fast');
        }
        if (href.replace(/.+?#/, '') === window.location.hash.replace(/.*?#/, '')) {
            $(window).trigger('hashchange');
        }
    });
    $(document).on('click', '.addNewItem', function(e) {
        e.preventDefault();
        var parentP = $(this).parent('p'),
            clone = parentP.prev('p').find('div:last').find('select').clone(),
            prevP = parentP.prev('p');
        clone.appendTo(prevP);
        clone.uniform();
    });
});

$(window).bind('drilldown', function() {
    var target = '#main-content';

    $('.tabs > ul', target).tabs('section > section');
    $('.accordion', target).tabs('.accordion > section', {tabs: 'header', effect: 'slide', initialIndex: 0});

    $('input[placeholder]', target).placeholder();
    $('input[type=date]', target).dateinput();

    /**
     * fix uniform uploader
     */
    $('.uploader .filename').click(function() {
        $('input:file', $(this).parent()).click();
    });

    /**
     * setup the validators
     */

    $('.form', target).validator({
        position: 'bottom left',
        offset: [5, 0],
        messageClass: 'form-error',
        message: '<div><em/></div>'// em element is the arrow
    }).attr('novalidate', 'novalidate');

    /**
     * setup messages
     */
    $('.message.closeable').each(function() {
        var message = $(this);
        message.prepend('<span class="message-close"></span>');
        $('.message-close', message).click(function() {
            message.fadeOut();
        });
    });

    /**
     * Setup tooltips
     */
    $('.has-tooltip').tooltip({
        effect: 'slide', offset: [-14, 0], position: 'top center', layout: '<div><em/></div>',
        onBeforeShow: function() {
            this.getTip().each(function() {
                if ($.browser.msie) {
                    PIE.attach(this);
                }
            });
        },
        onHide: function() {
            this.getTip().each(function() {
                if ($.browser.msie) {
                    PIE.detach(this);
                }
            });
        }
    }).dynamic({
        bottom: {direction: 'down', bounce: true}
    });

    setResize();
});
