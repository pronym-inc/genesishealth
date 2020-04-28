var PhoneWidget = (function($) {
    function clearPhoneField(event) {
        event.preventDefault();
        var p = $(this).parent();
        p.find('input[type=text]').val('');
        p.find('input[type=checkbox]').each(function() {
            var ele = $(this).attr('checked', false);
            $.uniform.update(ele);
        });
        if ($('.phone_div:visible').length > 1) {
            p.parent().hide();
        }
    }

    function replaceNUM(ele, attr, num) {
        var val = ele.attr(attr);
        if (typeof val != 'undefined') {
            ele.attr(attr, val.replace('NUM', num));
        }
    }

    function addPhoneNumberField() {
        var num = parseInt($('.phoneNumberAdd').attr('rel'));
        var template = $('#id_phone_NUM').clone();
        replaceNUM(template, 'id', num);
        template.find('*').each(function() {
            var ele = $(this);
            replaceNUM(ele, 'name', num);
            replaceNUM(ele, 'for', num);
            replaceNUM(ele, 'id', num);
        });

        template.find(':input.phone').mask('(999) 999-9999');

        var checkboxes = template.find('input:[type=checkbox]');
        $.uniform.restore(checkboxes);
        checkboxes.uniform();

        $('.phoneNumberAdd').attr('rel', num + 1);
        $('#hold_phone').append(template.show());
        $('.phone_div .rm').click(clearPhoneField);
    }


    function initPhoneWidget() {
        $('.phoneNumberAdd').click(function(event) {
            event.preventDefault();
            addPhoneNumberField();
        });

        if ($('.phoneNumberAdd').length) {
            var blankFields = 0;
            $('.phone_div input[type="text"]:visible').each(function() {
                if ($(this).val() == '') {
                    blankFields++;
                }
            });
            if (blankFields == 0) {
                addPhoneNumberField();
            }
        }

        $('.phone_div .rm').click(clearPhoneField);
        $('label[for=id_phone]').parent().hide();
    }

    return {init: initPhoneWidget}
}(jQuery));
