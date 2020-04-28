<script type="text/javascript">
$(document).on('change', '.batchSelectBox', function() {
    var that = this;
    $(this).parents('tbody').find('.batchSelectBox').each(function() {
        if (that !== this) {
            $(this).attr('checked', false);
        }
    });
    var meidEl = $(this).parents('table').find('thead tr th:contains("GHT Account No")');
    var idx = $(this).parents('table').find('thead tr th').index(meidEl) + 1;
    var meid = $(this).parents('tr').find(':nth-child(' + idx + ')').text();
    $('#id_patient_id').val(meid);
});
</script>