function setResize() {
  function getSizeInfo(elem) {
    size_css = $(elem).css('fontSize');
//  size_nr = parseFloat(size_css, 10);
    size_nr = parseInt(size_css);
    size_type = size_css.slice(-2);

    lh_size_css = $(elem).css('lineHeight');
//  lh_size_nr = parseFloat(lh_size_css, 10);
    lh_size_nr = parseInt(lh_size_css);
    lh_size_type = lh_size_css.slice(-2);
    return {
      element: elem,
      fontSize: {
        size_css: size_css,
        size_nr: size_nr,
        size_type: size_type
      },
      lineHeight: {
        size_css: lh_size_css,
        size_nr: lh_size_nr,
        size_type: lh_size_type
      }
    };
  };

  function alterSizes(exp) { // 1 - increase, -1 - decrease
    $('#main-content').find('*').each(function() {
      elem = getSizeInfo(this);
      elem.fontSize.size_nr *= Math.pow(1.1, exp);
      elem.lineHeight.size_nr *= Math.pow(1.1, exp);
      elem.fontSize.size_nr = Math.floor(elem.fontSize.size_nr);
      elem.lineHeight.size_nr = Math.floor(elem.lineHeight.size_nr);
      applySize(elem);
    });
  }

  function applySize(elem) {
    if (!isNaN(elem.fontSize.size_nr) && !isNaN(elem.lineHeight.size_nr)) {
//    $(elem.element).animate({fontSize: elem.fontSize.size_nr + elem.fontSize.size_type, 'line-height': elem.lineHeight.size_nr + elem.lineHeight.size_type}, 600);
      $(elem.element).animate({fontSize: elem.fontSize.size_nr + elem.fontSize.size_type}, 300);
      $(elem.element).animate({'line-height': elem.lineHeight.size_nr + elem.lineHeight.size_type}, 300);
    }
  }

  function readCookie(name) {
    var nameEQ = name + '=';
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
      var c = ca[i];
      while (c.charAt(0) == ' ') {
        c = c.substring(1, c.length);
      }
      if (c.indexOf(nameEQ) == 0) {
        return c.substring(nameEQ.length, c.length);
      }
    }
    return null;
  };

  var sd = (readCookie('steps_increase') * 1);
  if (sd != 0) {
    alterSizes(sd);
  }
}
