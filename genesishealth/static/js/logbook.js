$(document).ready(function() {
    $('.glucose_value').click(function() {
        $this = $(this);
        var reading_id = $this.attr('data-id');
        var $reading_notes = $('#reading-' + reading_id + '-notes');
        $('#id_notes').val($reading_notes.text());
        $('#note_form').dialog({
            modal: true,
            width: 430,
            buttons: {
                'Add Note': function() {
                    $.ajax({
                        type: 'POST',
                        url: '/readings/edit/'+ reading_id + '/',
                        data: {
                            notes: $('#id_notes').val(),
                            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
                        },
                        success: function(data) {
                            $reading_notes.text($('#id_notes').val());
                        }
                    });
                    $(this).dialog('close');
                }
            }
        });

        return false;
    });
});
