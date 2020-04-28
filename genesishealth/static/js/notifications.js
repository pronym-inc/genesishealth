function updateNotifications() {
  $.ajax('/alerts/ajax/notifications/', {
    dataType: 'json',
    cache: false,
    success: function(data, textStatus, jqXHR) {
      $('#alert-counter').html(data.length);
      $('#activity-popover').find('li.new').remove();
      if (data.notifications) {
        for (var i = 0; i < data.notifications.length; i++) {
          var msg = data.notifications[i].message_text;
          $('#view-all-notifications').before('<li class="new">' + msg + '</li>');
        }
      }
    }
  });
}
