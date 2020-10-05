updateCallbackQueue.push(function(div) {
    function updateDisplay() {
        const queryType = $(div).find('.queryDropdownAction').val();
        if (queryType === 'recent_reading_count') {
           $(div).find('[for=recent_reading_count]').show();
           $(div).find('[for=high_reading_count]').hide();
           $(div).find('[for=low_reading_count]').hide();
        } else if (queryType === 'high_reading_count') {
           $(div).find('[for=recent_reading_count]').hide();
           $(div).find('[for=high_reading_count]').show();
           $(div).find('[for=low_reading_count]').hide();
        } else if (queryType === 'low_reading_count') {
           $(div).find('[for=recent_reading_count]').hide();
           $(div).find('[for=high_reading_count]').hide();
           $(div).find('[for=low_reading_count]').show();
        } else {
           $(div).find('[for=recent_reading_count]').hide();
           $(div).find('[for=high_reading_count]').hide();
           $(div).find('[for=low_reading_count]').hide();
        }
    }

   $(div).find('.queryDropdownAction').change(function() {
       updateDisplay();
    });

    $(div).find('.queryDropdownSubmitter').click(function() {
        const baseUrl = window.location.pathname;
        const baseHash = window.location.hash.split('?')[0];
        const queryType = $(div).find('.queryDropdownAction').val();
        let queryString;
        if (queryType === 'recent_reading_count') {
            queryString = "queryType=recent_reading_count&count=" + $(div).find('#recent_reading_reading_count').val() + "&for_days=" + $(div).find('#recent_reading_for_days').val();
        } else if (queryType === 'high_reading_count') {
            queryString = "queryType=high_reading_count&count=" + $(div).find('#high_reading_reading_count').val() + "&for_days=" + $(div).find('#high_reading_for_days').val() + "&threshold=" + $(div).find('#high_reading_glucose_value').val();
        } else if (queryType === 'low_reading_count') {
           queryString = "queryType=low_reading_count&count=" + $(div).find('#low_reading_reading_count').val() + "&for_days=" + $(div).find('#low_reading_for_days').val() + "&threshold=" + $(div).find('#low_reading_glucose_value').val();
        }
        window.location.href = baseUrl + baseHash + "?" + queryString;
    });

    function loadExistingQuery() {
        if (!window.location.hash || window.location.hash.indexOf('?') === -1) return;
        const qs = window.location.hash.split('?')[1].split('&');
        let queryOutput = {};
        $.each(qs, function(idx, entry) {
           const split = entry.split('=');
           const key = split[0];
           const value = split[1];
           queryOutput[key] = value;
        });
        $(div).find('.queryDropdownAction').val(queryOutput.queryType);
        updateDisplay();
        if (queryOutput.queryType === 'recent_reading_count') {
            $(div).find('#recent_reading_reading_count').val(queryOutput.count);
            $(div).find('#recent_reading_for_days').val(queryOutput.for_days);
        } else if (queryOutput.queryType === 'high_reading_count') {
            $(div).find('#high_reading_reading_count').val(queryOutput.count);
            $(div).find('#high_reading_glucose_value').val(queryOutput.threshold);
            $(div).find('#high_reading_for_days').val(queryOutput.for_days);
        } else if (queryOutput.queryType === 'low_reading_count') {
           $(div).find('#low_reading_reading_count').val(queryOutput.count);
           $(div).find('#low_reading_glucose_value').val(queryOutput.threshold);
           $(div).find('#low_reading_for_days').val(queryOutput.for_days);
        }
    }

    loadExistingQuery();
});
