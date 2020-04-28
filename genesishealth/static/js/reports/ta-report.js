var ta = {
  display_readings: function(callback, id, chartID, type) {
    var startDate, endDate;
    if ($('#id_start_date').length > 0) {
      startDate = $('#id_start_date').val();
    } else {
      var startDateObj = new Date(new Date() - 14 * 24 * 60 * 60 * 1000);
      startDate = (startDateObj.getMonth() + 1) + '/' + startDateObj.getDate() + '/' + startDateObj.getFullYear();
    }
    if ($('#id_end_date').length > 0) {
      endDate = $('#id_end_date').val();
    } else {
      var endDateObj = (new Date());
      endDate = (endDateObj.getMonth() + 1) + '/' + endDateObj.getDate() + '/' + endDateObj.getFullYear();
    }
    var options = {
      method: 'GET',
      url: '/reports/trending/average/data/',
      data: {start_date: startDate, end_date: endDate, type: type},
      success: callback
    };
    if (id) {
      options['url'] += id + '/';
    }
    $.ajax(options);
  },
  generate_chart: function(data, width, height, chartID, type) {
    var chartTitle;
    if (type == 'premeal') {
      chartTitle = 'Premeal Trending Report';
    } else if (type == 'postmeal') {
      chartTitle = 'Postmeal Trending Report';
    } else if (type == 'combined') {
      chartTitle = 'Combined Trending Report';
    }
  	Highcharts.setOptions({
       colors: ['#cc3333', '#ffff33', '#33cc33', '#3399cc', '#0066cc', '#6AF9C4']
    });
    var chart = new Highcharts.Chart({
      chart: {
        renderTo: chartID,
        width: width,
        height: height
      },
      credits: {
        enabled: false
      },
      legend: {
        enabled: true
      },
      title: {
        text: chartTitle
      },
      tooltip: {
          formatter: function() {
              return '<strong>' + this.point.name + '</strong>: ' + this.y + '%';
          }
      },
      exporting: {enabled: false},
      plotOptions: {
          pie: {
              enableMouseTracking: (window.isPDFExport ? false : true),
              shadow: false,
              animation: (window.isPDFExport ? false : true),
              allowPointerSelect: true,
              cursor: 'pointer',
              dataLabels: {
                  enabled: false
              },
              showInLegend: true,
              size: '60%'
          }
      },
      series: [{
          type: 'pie',
          name: 'Average',
          data: [
              
              ['Hyperglycemic', parseFloat(data.hyper_percentage)],
							['Above range', parseFloat(data.above_percentage)],
              ['Within range', parseFloat(data.within_percentage)],
			  			['Below range', parseFloat(data.below_percentage)],
              ['Hypoglycemic', parseFloat(data.hypo_percentage)]
          ]
      }]
    });

    window[chartID + '-chart'] = chart;
  }
};

postCallbackQueue.push(function(div) {
  div.find('div.taChart').each(function() {
    var that = this;
    var type = $(that).attr('id').replace(/^.+?-(.+?)$/, '$1');
      ta.display_readings(function(data) {
        var width = 400;
        if (width > (0.95 * $('body').width())) {
          width = 0.95 * $('body').width();
        }
        $(that).css('max-width', width);
        var height = 300;
        ta.generate_chart(data, width, height, $(that).attr('id'), type);
       }, chart_patient_id, $(that).attr('id'), type);
  });
});
