$(document).on('.queryDropdownAction', 'change', function() {
   const queryType = $('.queryDropdownAction').val();
   if (queryType === 'recent_reading_count') {
       $('[for=recent_reading_count]').show();
       $('[for=high_reading_count]').hide();
       $('[for=low_reading_count]').hide();
   } else if (queryType === 'high_reading_count') {
       $('[for=recent_reading_count]').hide();
       $('[for=high_reading_count]').show();
       $('[for=low_reading_count]').hide();
   } else {
       $('[for=recent_reading_count]').hide();
       $('[for=high_reading_count]').hide();
       $('[for=low_reading_count]').show();
   }
});

$(document).on('.queryDropdownSubmitter', 'click', function() {
    const baseUrl = window.location.pathname;
    const baseHash = window.location.hash.split('?')[0];
    const queryType = $('.queryDropdownAction').val();
    let queryString;
    if (queryType === 'recent_reading_count') {
        queryString = "queryType=recent_reading_count&count=" + $('#recent_reading_reading_count').val() + "&for_days=" + $('#recent_reading_for_days').val();
    } else if (queryType === 'high_reading_count') {
        queryString = "queryType=high_reading_count&count=" + $('#high_reading_reading_count').val() + "&for_days=" + $('#high_reading_for_days').val() + "&threshold=" + $('#high_reading_glucose_value');
    } else {
       queryString = "queryType=high_reading_count&count=" + $('#low_reading_reading_count').val() + "&for_days=" + $('#low_reading_for_days').val() + "&threshold=" + $('#low_reading_glucose_value');
    }
    window.location = baseUrl + baseHash + "?" + queryString;
});

console.log(1);
