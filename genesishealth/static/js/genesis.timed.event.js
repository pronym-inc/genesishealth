updateCallbackQueue.push(function(div) {
    function updateScheduledReportForm() {
        var interval = $('#id_interval').val();
        var time_obj = $('#id_delivery_time').parents('p');
        var day_of_week_obj = $('#id_delivery_day_of_week').parents('p');
        var day_of_month_obj = $('#id_delivery_day_of_month').parents('p');
        var datetime_obj = $('#id_delivery_datetime').parents('p');

        if (interval == 'daily') {
            time_obj.show();
            day_of_week_obj.hide();
            day_of_month_obj.hide();
            datetime_obj.hide();
        } else if (interval == 'weekly') {
            time_obj.show();
            day_of_week_obj.show();
            day_of_month_obj.hide();
            datetime_obj.hide();
        } else if (interval == 'monthly') {
            time_obj.show();
            day_of_week_obj.hide();
            day_of_month_obj.show();
            datetime_obj.hide();
        } else if (interval == 'once') {
            time_obj.hide();
            day_of_week_obj.hide();
            day_of_month_obj.hide();
            datetime_obj.show();
        } else {
            time_obj.hide();
            day_of_week_obj.hide();
            day_of_month_obj.hide();
            datetime_obj.hide();
        }
    }
    $('#id_interval').change(function() {
        updateScheduledReportForm();
    });
    updateScheduledReportForm();
});
