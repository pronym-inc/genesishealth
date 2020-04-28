$(document).on('ghtupdate', function(e, $div) {
    function updateReportDateFields() {
        var filterVal = $div.find('[name=account_filter]:checked').val(),
            dateWidgets = $div.find('#id_report_start, #id_report_end').parents('p');
        if (filterVal == "custom")
            dateWidgets.show();
        else dateWidgets.hide();
    }
    $div.on('click', '[name=account_filter]', updateReportDateFields);
    updateReportDateFields();
});