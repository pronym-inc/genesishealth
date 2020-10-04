$(function() {
    function updateDisplay() {
        const queryType = $('.queryDropdownAction').val();
        if (queryType === 'recent_reading_count') {
           $('[for=recent_reading_count]').show();
           $('[for=high_reading_count]').hide();
           $('[for=low_reading_count]').hide();
        } else if (queryType === 'high_reading_count') {
           $('[for=recent_reading_count]').hide();
           $('[for=high_reading_count]').show();
           $('[for=low_reading_count]').hide();
        } else if (queryType === 'low_reading_count') {
           $('[for=recent_reading_count]').hide();
           $('[for=high_reading_count]').hide();
           $('[for=low_reading_count]').show();
        } else {
           $('[for=recent_reading_count]').hide();
           $('[for=high_reading_count]').hide();
           $('[for=low_reading_count]').hide();
        }
    }

   $('.queryDropdownAction').change(function() {
       updateDisplay();
    });

    $('.queryDropdownSubmitter').click(function() {
        const baseUrl = window.location.pathname;
        const baseHash = window.location.hash.split('?')[0];
        const queryType = $('.queryDropdownAction').val();
        let queryString;
        if (queryType === 'recent_reading_count') {
            queryString = "queryType=recent_reading_count&count=" + $('#recent_reading_reading_count').val() + "&for_days=" + $('#recent_reading_for_days').val();
        } else if (queryType === 'high_reading_count') {
            queryString = "queryType=high_reading_count&count=" + $('#high_reading_reading_count').val() + "&for_days=" + $('#high_reading_for_days').val() + "&threshold=" + $('#high_reading_glucose_value').val();
        } else {
           queryString = "queryType=high_reading_count&count=" + $('#low_reading_reading_count').val() + "&for_days=" + $('#low_reading_for_days').val() + "&threshold=" + $('#low_reading_glucose_value').val();
        }
        window.location = baseUrl + baseHash + "?" + queryString;
    });

    function loadExistingQuery() {
        const qs = window.location.hash.split('?')[1].split('&');
        let queryOutput = {};
        $.each(qs, function(idx, entry) {
           const split = entry.split('=');
           const key = split[0];
           const value = split[1];
           queryOutput[key] = value;
        });
        $('.queryDropdownAction').val(queryOutput.queryType);
        updateDisplay();
        if (queryOutput.queryType === 'recent_reading_count') {
            $('#recent_reading_reading_count').val(queryOutput.count);
            $('#recent_reading_for_days').val(queryOutput.for_days);
        } else if (queryOutput.queryType === 'high_reading_count') {
            $('#high_reading_reading_count').val(queryOutput.count);
            $('#high_reading_glucose_value').val(queryOutput.threshold);
            $('#high_reading_for_days').val(queryOutput.for_days);
        } else {
           $('#low_reading_reading_count').val(queryOutput.count);
           $('#low_reading_glucose_value').val(queryOutput.threshold);
           $('#low_reading_for_days').val(queryOutput.for_days);
        }
    }

    loadExistingQuery();
});
