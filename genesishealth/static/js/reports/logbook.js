updateCallbackQueue.push(function(div) {

    var logbook4 = div.find('#logbook4').dataTable({
        'sPaginationType': 'full_numbers',
        'aaSorting': [[0, 'desc']],
        'aoColumns': [
           { 'sType': 'us_date' },
           null,
           null,
           null,
           null
        ],
        'sAjaxSource': window.logbook4AjaxStr,
        'oLanguage': {'sEmptyTable': 'Loading...'},
        'bLengthChange': false,
        'bPaginate': false
    });

    var logbook8 = div.find('#logbook8').dataTable({
        'sPaginationType': 'full_numbers',
        'aaSorting': [[0, 'desc']],
        'aoColumns': [
           { 'sType': 'us_date' },
           null,
           null,
           null,
           null,
           null,
           null,
           null,
           null
        ],
        'sAjaxSource': window.logbook8AjaxStr,
        'oLanguage': {'sEmptyTable': 'Loading...'},
        'bLengthChange': false,
        'bPaginate': false
    });

    function updateNutrition(element) {
        var servings = parseFloat(element.find('.numServings').val());
        var weightRatio = parseFloat(element.find('select.servingTypeSelect option:selected').attr('weight')) / 100;
        element.find('.carbField').val(parseInt(element.find('.carbField').attr('baseAmount') * servings * weightRatio));
        element.find('.calField').val(parseInt(element.find('.calField').attr('baseAmount') * servings * weightRatio));
    }

    var autocompleteSettings = {
        source: function(request, response) {
            $.ajax({
                url: window.foodSearchLocation,
                dataType: 'json',
                data: {
                    name_startsWith: request.term
                },
                success: function(data) {
                    response($.map(data, function(item) {
                        return {
                            label: item.name,
                            value: item.name,
                            id: item.id,
                            carbohydrates: item.carbohydrates,
                            calories: item.calories,
                            serving_types: item.serving_types
                        };
                    }));
                }
            });
        },
        minLength: 3,
        select: function(event, ui) {
            var div = $(this).parents('div.foodItem');
            $(this).next('input.hiddenObjectId').val(ui.item.id);
            div.find('.carbField').attr('baseAmount', ui.item.carbohydrates).attr('readonly', 'readonly');
            div.find('.calField').attr('baseAmount', ui.item.calories).attr('readonly', 'readonly');
            var select = div.find('.servingTypeSelect').removeAttr('disabled');
            if (ui.item.serving_types.length === 0) {
                select.append('<option value="" weight="100">100 grams</option>');
            }
            for (var i = 0; i < ui.item.serving_types.length; i++) {
                select.append('<option value="' + ui.item.serving_types[i][0] + '" weight="' + ui.item.serving_types[i][2] + '">' + ui.item.serving_types[i][1] + '</option>');
            }
            $.uniform.update(select);
            div.find('.numServings').val(1);
            updateNutrition(div);
            div.find('.numServings').attr('required', 'required');
            div.find('.dependsOnName').parents('p').show();
        },
        open: function() {
            $(this).removeClass('ui-corner-all').addClass('ui-corner-top');
        },
        close: function() {
            $(this).removeClass('ui-corner-top').addClass('ui-corner-all');
        }
    };

    function removeValidation(element) {
        element.find('ul.errorlist').remove();
        element.find('p.invalid').removeClass('invalid');
    }

    function resetForm(element) {
        removeValidation(element);
        element.find(':input:visible').not('[type="submit"]').not('[name="csrfmiddlewaretoken"]').not('[name$="-patient"]').val('');
        element.find('div.foodItem').not(':first').remove();
        element.find('select.servingTypeSelect option').each(function() {
            $(this).remove();
        });
        element.find('.dependsOnName').removeAttr('required').parents('p').hide();
        element.find('.carbField, .calField').removeAttr('baseAmount').removeAttr('readonly');
        element.find('.inError').removeClass('.inError');
    }

    function reloadTable() {
        logbook4.fnClearTable();
        logbook8.fnClearTable();
        logbook4.fnReloadAjax(window.logbook4AjaxStr);
        logbook8.fnReloadAjax(window.logbook8AjaxStr);
    }

    function setupElement(element) {
        resetForm(element);

        element.find('input.foodSelector').keydown(function(e) {
            if (element.find('.hiddenObjectId').val() !== '') {
                var fields = ['.hiddenObjectId', '.carbField', '.calField'];
                for (var i = 0; i < fields.length; i++) {
                    element.find(fields[i]).val('');
                }
                resetForm(element);
            }
        });

        element.find('input.numServings').keydown(function(event) {
            // Allow: backspace, delete, tab, escape, enter, and period
            if (event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode == 27 || event.keyCode == 13 || event.keyCode == 190 ||
                 // Allow: Ctrl+A
                (event.keyCode == 65 && event.ctrlKey === true) ||
                 // Allow: home, end, left, right
                (event.keyCode >= 35 && event.keyCode <= 39)) {
                     // let it happen, don't do anything
                     return;
            }
            else {
                // Ensure that it is a number and stop the keypress
                if (event.shiftKey || (event.keyCode < 48 || event.keyCode > 57) && (event.keyCode < 96 || event.keyCode > 105)) {
                    event.preventDefault();
                }
            }
        });

        element.find('input.numServings, select.servingTypeSelect').change(function(e) {
            updateNutrition($(this).parents('div.foodItem'));
        });

        element.find('input.foodSelector').autocomplete(autocompleteSettings);
        resetForm(element);

    }

    div.find('a.foodItemAddAnother').click(function(e) {
        e.preventDefault();
        var oldDiv = $('div[id^="id_food-food_items_"]:last');
        var newDiv = oldDiv.clone();
        var oldId = parseInt(newDiv.attr('id').replace(/.+?_(\d+)$/, '$1'));
        var newId = oldId + 1;
        newDiv.attr('id', newDiv.attr('id').replace(/(.+?)_\d+$/, '$1_' + newId));
        var replaceRegex = /^(.+?)_\d+_(.+?)$/;
        var replace = '$1_' + newId + '_$2';
        // Update all of the for's, id's, and name's with the new number.
        newDiv.find('label, input, select').each(function() {
            var attrs = ['for', 'id', 'name'];
            for (var i = 0; i < attrs.length; i++) {
                if ($(this).attr(attrs[i]) !== undefined)
                    $(this).attr(attrs[i], $(this).attr(attrs[i]).replace(replaceRegex, replace));
            }
        });
        // Get rid of old validation
        setupElement(newDiv);
        // Add a border on top to distinguish the food items.
        newDiv.find('p:first').css('border-top', '1px dotted black');
        newDiv.insertAfter(oldDiv);
    });

    div.find('.fancybox').fancybox({
        beforeLoad: function() {
            if (this.element.data('fancybox-width'))
                this.width = parseInt(this.element.data('fancybox-width'));
            if (this.element.data('fancybox-height'))
                this.height = parseInt(this.element.data('fancybox-height'));
        },
        beforeClose: function() {
            resetForm($('.fancybox-outer:visible').find('form'));
        }
    });

    var $container = div.find('#growlcontainer').notify();

    div.find('.growlButton').click(function(e) {
        e.preventDefault();
        var form = $(this).parents('form');
        var form_type = form.attr('formType');
        removeValidation(form);
        var valid = true;
        form.find(':input[required="required"]').filter(function() {
            return $(this).val() === '';
        }).each(function() {
            valid = false;
            var errorList = $('<ul class="errorlist"><li>This field is required.</li></ul>');
            $(this).parents('p').before(errorList);
            $(this).parents('p').addClass('invalid');
        });
        if (!valid) { return; }
        $.ajax({
            url: '/reports/ajax/logbook/form/' + form_type + '/',
            type: 'POST',
            data: form.serialize(),
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                    $.fancybox.close();
                    reloadTable();
                    $container.notify('create', 'growl-container', {
                        title: form.attr('growlTitle'),
                        text: form.attr('growlText')
                    });
                    resetForm(form);
                } else {
                    for (var i in data.errors) {
                        var errorList = $('<ul class="errorlist"></ul>');
                        for (var j = 0; j < data.errors[i].length; j++) {
                            errorList.append('<li>' + data.errors[i][j] + '</li>');
                        }
                        var element = form.find('#id_' + form_type + '-' + i);
                        element.parents('p').before(errorList);
                        element.parents('p').addClass('invalid');
                    }
                    $('.fancybox-inner').get(0).scrollTop = 0;
                }
            },
            error: function(jqXHR, textStatus, errorThrown) {
                console.log('ajax request failed: ' + jqXHR + ',' + textStatus + ', ' + errorThrown);
            }
        });
    });

    div.find('#printForm').submit(function(e) {
        e.preventDefault();
        var url = $(this).attr('action');
        var formData = $(this).serialize();
        var fullURL = url + '?' + formData;
        window.open(fullURL);
        $.fancybox.close();
    });

    div.find('.logbookForm').each(function() {
        setupElement($(this));
    });

    $(document).on('click', 'div.entry-wrapper', function(e) {
        e.preventDefault();
        var showNotes = false;
        // Detect clicks that are on the orange vs on the body.
        if ($(this).is('.hasNotes')) {
            var borderWidth = $(this).css('border-right-width').replace(/px/, '') * 1;
            if (e.offsetX > ($(this).outerWidth() - borderWidth)) {
                showNotes = true;
            }
        }
        if (showNotes) {
            $.ajax({
                url: window.logbookNotesLocation,
                type: 'POST',
                dataType: 'html',
                data: {
                    start_time: $(this).parent('td').find('.startTime').val(),
                    end_time: $(this).parent('td').find('.endTime').val(),
                    patient_id: window.patient_id,
                    csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
                },
                success: function(data) {
                    $.fancybox({
                        autoSize: false,
                        width: 400,
                        content: data
                    });
                }
            });
        } else {
            var newURL = '/reports/ajax/logbook_entry/' + $(this).attr('entry-id') + '/';
            $.ajax({
                url: newURL,
                dataType: 'html',
                success: function(data) {
                    $.fancybox({
                        'autoScale': true,
                        'autoDimensions': true,
                        'content' : data
                    });
                }
            });
        }
    });

    $(document).on('click', '.entryFormSubmit', function(e) {
        e.preventDefault();
        var form = $(this).parent('form');
        $()
        $.ajax({
            url: form.attr('action'),
            type: 'POST',
            dataType: 'json',
            data: form.serialize(),
            success: function(data) {
                if (data.success) {
                    $.fancybox.close();
                    reloadTable();
                } else {
                    form.find('#id_note').addClass('inError');
                }
            }
        });
        return false;
    });

    $().selectDays(function(startDate, endDate) {
        var startDate = startDate.getFullYear() + '-' + (startDate.getMonth() + 1) + '-' + startDate.getDate(),
            endDate = endDate.getFullYear() + '-' + (endDate.getMonth() + 1) + '-' + endDate.getDate();
        setLogbookAjaxStr(startDate, endDate);
        reloadTable();
    });
});
