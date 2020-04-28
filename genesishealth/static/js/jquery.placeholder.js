// HTML5 placeholder plugin version 0.3
// Enables cross-browser* html5 placeholder for inputs, by first testing
// for a native implementation before building one.
//
// USAGE:
//$('input[placeholder]').placeholder();
(function($) {
  $.fn.placeholder = function(options) {
    return this.each(function() {
      if (!('placeholder' in document.createElement(this.tagName.toLowerCase()))) {
        var $this = $(this);
        var placeholder = $this.attr('placeholder');
        !$this.val() && $this.val(placeholder).data('color', $this.css('color')).css('color', '#aaa');
        $this.focus(function() {
          if ($.trim($this.val()) === placeholder) {
            $this.val('').css('color', $this.data('color'));
          }
        }).blur(function() {
          if (!$.trim($this.val())) {
            $this.val(placeholder).data('color', $this.css('color')).css('color', '#aaa');
          }
        });
      }
    });
  };
})(jQuery);
