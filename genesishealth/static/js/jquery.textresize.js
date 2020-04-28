(function($){
	$("head").append("<link>");

	$.fn.textResize = function(passed_params) {
	// initialization
		var parent = this;
		var params = {
			createNav: 0,
			navHolder: '#navHere',
			skin: 0,
			persistSize: 1,
			sizeStep: 1.1,
			innerTags: '*',
			maxSteps: {increase: 5, decrease: 5}
		};
		var default_sizes = [];
		var steps = {increase: 0, decrease: 0};
		$.extend(params, passed_params);
		if (params.createNav == 1) {
			createNav(params.navHolder, params.skin);
		}
		// GTFHRCPH
		
		$(params.navHolder+' .increase').click(function() { modifySize(1); return false; });
		$(params.navHolder+' .decrease').click(function() { modifySize(-1); return false; });
		  $(params.navHolder+' .revert').click(function() { modifySize(0); return false; });
		registerDefaults();
		function setCookie(c_name, value, exdays) {
			var exdate = new Date();
			exdate.setDate(exdate.getDate() + exdays);
			var c_value = escape(value) + ((exdays==null) ? "" : "; expires="+exdate.toUTCString());
			document.cookie = c_name + "=" + c_value;
		}
		function readCookie(name) {
			var nameEQ = name + "=";
			var ca = document.cookie.split(';');
			for(var i=0;i < ca.length;i++) {
				var c = ca[i];
				while (c.charAt(0)==' ') c = c.substring(1,c.length);
				if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
			}
			return null;
		};

	// function definition
		function createNav(selector, css_class) {
			$(selector).each(function() {
				$(this).addClass('skin');
				$(this).html('<div class="skin'+css_class+' skin_actions"><a href="#" class="decrease">a</a><a href="#" class="revert">a</a><a href="#" class="increase">a</a></div>');
			});
		};
		function getSizeInfo(elem) {
			size_css 	= $(elem).css('fontSize');
//			size_nr		= parseFloat(size_css, 10);
			size_nr		= parseInt(size_css);
			size_type 	= size_css.slice(-2);

			lh_size_css 	= $(elem).css('lineHeight');
//			lh_size_nr		= parseFloat(lh_size_css, 10);
			lh_size_nr		= parseInt(lh_size_css);
			lh_size_type 	= lh_size_css.slice(-2);
			return {
				element: 	elem,
				fontSize:	{
					size_css: 	size_css, 
					size_nr:	size_nr, 
					size_type: 	size_type
				},
				lineHeight: {
					size_css: 	lh_size_css, 
					size_nr:	lh_size_nr, 
					size_type: 	lh_size_type
				}
			};
		};
		function registerDefaults() {
			$(parent).find(params.innerTags).each(function() {
				info = getSizeInfo(this);
				default_sizes.push(info);
//				console.log(info.element, info.fontSize.size_css, info.fontSize.size_type);
			});
			if (params.persistSize) {
				var cookie_steps = {decrease: readCookie('steps_decrease'), increase: readCookie('steps_increase')};
				if (cookie_steps) {
					if (cookie_steps.decrease != 0 || cookie_steps.increase != 0) {
//						console.log(cookie_steps);
						var direction = (cookie_steps.decrease > 0) ? -1 : 1;
						var direction_steps = (cookie_steps.decrease > 0) ? cookie_steps.decrease : cookie_steps.increase;
						for (var i=0; i<direction_steps; i++) {
//							console.log('direction_steps:', direction_steps, 'direction:', direction, 'step:', i);
							window.setTimeout(function () { 
								modifySize(direction);
							},  i*500);
//							window.setTimeout('modifySize', i*600, direction);
						}
					}
				}
				
			}
		};
		function resetDefaults() {
			var count = default_sizes.length;
			for (var i=0; i<count; i++) {
				var elem = default_sizes[i];
				elem = default_sizes[i];
				applySize(elem);
			}
		};
		function alterSizes(type) { // 1 - increase, -1 - decrease
			$(parent).find(params.innerTags).each(function() {
				elem = getSizeInfo(this);
				if (type === 1) {
					elem.fontSize.size_nr 		*= params.sizeStep;
					elem.lineHeight.size_nr 	*= params.sizeStep;
					elem.fontSize.size_nr 		 = Math.floor(elem.fontSize.size_nr);
					elem.lineHeight.size_nr 	 = Math.floor(elem.lineHeight.size_nr);
				}
				if (type === -1) {
					elem.fontSize.size_nr 		/= params.sizeStep;
					elem.lineHeight.size_nr 	/= params.sizeStep;
					elem.fontSize.size_nr 		 = Math.ceil(elem.fontSize.size_nr);
					elem.lineHeight.size_nr 	 = Math.ceil(elem.lineHeight.size_nr);
				}
//				console.log(!isNaN(elem.fontSize.size_nr), ', ', !isNaN(elem.lineHeight.size_nr));
				applySize(elem);
			});
		}
		function applySize(elem) {
			if ($(elem.element).attr('id') == 'test_js') {
//				console.log(elem.fontSize.size_nr);
			}
			if (!isNaN(elem.fontSize.size_nr) && !isNaN(elem.lineHeight.size_nr)) {
//			$(elem.element).animate({fontSize: elem.fontSize.size_nr + elem.fontSize.size_type, 'line-height': elem.lineHeight.size_nr + elem.lineHeight.size_type}, 600);
				$(elem.element).animate({fontSize: elem.fontSize.size_nr + elem.fontSize.size_type}, 300);
				$(elem.element).animate({'line-height': elem.lineHeight.size_nr + elem.lineHeight.size_type}, 300);
			}
		}
		function modifySize(mode) { // 0 - default, 1 - increase, -1 decrease
//			console.log('start modifySize('+mode+'); decrease: '+steps.decrease+'; increase: '+steps.increase);
			if (mode === -1) {
				if (steps.decrease >= params.maxSteps.decrease) { // max decrease limit reached
//					console.log('decrease steps limit of '+params.maxSteps.decrease+' reached');
				}
				else {
					alterSizes(-1);
					steps.decrease += 1;
					steps.increase -= 1;
				}
			}
			if (mode === 0) {
				resetDefaults();
				steps.increase = 0;
				steps.decrease = 0;
			}
			if (mode === 1) {
				if (steps.increase >= params.maxSteps.increase) { // max increase limit reached
//					console.log('increase steps limit of '+params.maxSteps.increase+' reached');
				}
				else {
					alterSizes(1);
					steps.increase += 1;
					steps.decrease -= 1;
				}
			}
//			console.log('end modifySize('+mode+'); decrease: '+steps.decrease+'; increase: '+steps.increase);
			setCookie('steps_decrease', steps.decrease, 10);
			setCookie('steps_increase', steps.increase, 10);
		};
	};
})(jQuery);
