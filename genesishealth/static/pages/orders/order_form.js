(function() {
    $(document).ready(function() {
        if (window.existingUser) {
            $('#patient-display-name').val(window.existingUser);
        }
    });

    $(document).on('click', '[data-patient-id]', function(e) {
        $('#id_patient').val($(this).data('patient-id'));
        var patientName = $(this).parents('tr').find('td:first').html();
        $('#patient-display-name').val(patientName);
        return false;
    });
})();