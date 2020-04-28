// Date select widget javascript.
// Call jQuery(document).selectDays(callback); to register a callback.
// HTML templates can be included from:
//  /reports/selectdays_select.html
//  /reports/selectdays_customform.html

(function($) {
    var defaults = {
        defaultDays: 30,
        selectID: '[id$="selectDays"]',
        customID: '#selectDaysDate',
        submitID: '#selectDaysSubmit',
        startID: '#startDate',
        endID: '#endDate'
    };
    $.extend($.fn, {
        selectDays: function(callback, options) {
            var opt = $.extend({}, defaults, options);
            if (typeof defaultDays == 'undefined') {
                var defaultDays = defaults.defaultDays;
            }
            $(opt.selectID).change(function(event) {
                event.preventDefault();
                var val = $(this).val();
                if (val == 'custom') {
                    $(opt.customID).show();
                } else {
                    val = parseInt(val) - 1;
                    $(opt.customID).hide();
                    var endDate = new Date(),
                        startDate = new Date();
                    startDate = new Date(startDate.setDate(startDate.getDate() - val));
                    callback(startDate, endDate);
                }
            }).val(opt.defaultDays);

            $(opt.submitID).click(function(event) {
                event.preventDefault();
                var startDate = $(opt.startID).val(),
                    endDate = $(opt.endID).val();
                if (startDate && endDate) {
                    callback(new Date(startDate), new Date(endDate));
                }
            });
        }
    });
})(jQuery);
