
var th = {
  display_readings: function(callback, id, chartID, type, startDate, endDate) {
    if (startDate === undefined && endDate === undefined) {
      if ($('#id_' + chartID + '_start_date').length > 0) {
        startDate = $('#id_' + chartID + '_start_date').val();
      } else {
        var startDateObj = new Date(new Date() - 14 * 24 * 60 * 60 * 1000);
        startDate = (startDateObj.getMonth() + 1) + '/' + startDateObj.getDate() + '/' + startDateObj.getFullYear();
      }
      if ($('#id_' + chartID + '_end_date').length > 0) {
        endDate = $('#id_' + chartID + '_end_date').val();
      } else {
        var endDateObj = (new Date());
        endDate = (endDateObj.getMonth() + 1) + '/' + endDateObj.getDate() + '/' + endDateObj.getFullYear();
      }
    }
    var options = {
      method: 'GET',
      url: '/reports/test_history/data/',
      data: {start_date: startDate, end_date: endDate, type: type},
      success: callback
    };
    if (id) {
      options['url'] += id + '/';
    }
    $.ajax(options);
  },
  generate_chart: function(data, width, height, chartID, type) {
    var chartTitle = 'Glucose Readings';

    window[chartID + '-chart'] = new Highcharts.Chart({
      colors: ['#000000'],
      chart: {
        renderTo: chartID,
        defaultSeriesType: 'line',
        height: height,
        width: width
      },
      credits: {
        enabled: false
      },
      legend: {
        enabled: false
      },
      title: {
        text: chartTitle
      },
      yAxis: {
        title: {
          text: 'Glucose'
        },
        plotBands: [{
            from: -10000,
            to: parseInt(data.glucose_goal[0]),
            color: '#555555'
          },
          {
            from: parseInt(data.glucose_goal[0]),
            to: parseInt(data.glucose_goal[1]),
            color: '#AAAAAA'
          },
          {
            from: parseInt(data.glucose_goal[1]),
            to: parseInt(data.glucose_goal[2]),
            color: '#EEEEEE'
          },
          {
            from: parseInt(data.glucose_goal[2]),
            to: parseInt(data.glucose_goal[3]),
            color: '#AAAAAA'
          },
          {
            from: parseInt(data.glucose_goal[3]),
            to: 10000,
            color: '#555555'
          }
          ],
          min: 0,
      },
      xAxis: {
          type: 'datetime',
          tickPixelInterval: 80,
          startOnTick: true
      },
      plotOptions: {
          series: {
              enableMouseTracking: (window.isPDFExport ? false : true),
              shadow: false,
              animation: (window.isPDFExport ? false : true)
          }
      },
      series: [{
          data: data.readings
      }],
      tooltip: {
          formatter: function() {
              return 'Glucose Value: <b>' + this.y + '</b> at <b>' + this.point.datetime + '</b>';
          }
      }
    });
  }
};


var ta = {
  display_readings: function(callback, id, chartID, type, dateStart, dateEnd) {
    var options = {
      method: 'GET',
      url: '/reports/trending/average/data/',
      data: {start_date: dateStart, end_date: dateEnd, type: type},
      success: callback
    };
    if (id) {
      options['url'] += id + '/';
    }
    $.ajax(options);
  },
  generate_chart: function(data, width, height, chartID, type, chartTitle) {
    var chart = new Highcharts.Chart({
      colors: ['#DDDDDD', '#AAAAAA', '#777777', '#444444', '#111111'],
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
              ['Hypoglycemic', parseFloat(data.hypo_percentage)],
              ['Above range', parseFloat(data.above_percentage)],
              ['Below range', parseFloat(data.below_percentage)],
              ['Within range', parseFloat(data.within_percentage)],
              ['Hyperglycemic', parseFloat(data.hyper_percentage)]
          ]
      }]
    });

    window[chartID + '-chart'] = chart;
  }
};

 $(function() {
   var chart_patient_id = window.chart_patient_id;

  $('div.thChart').each(
    function() {
     var that = this;
     var type = $(that).attr('id').replace(/^.+?-(.+?)$/, '$1');
     var dateStart = $(that).attr('chart-date-start');
     var dateEnd = $(that).attr('chart-date-end');
     th.display_readings(function(data) {
       var width = 400;
       if (width > (0.95 * $('body').width())) {
         width = 0.95 * $('body').width();
       }
       $(that).css('max-width', width);
       var height = 320;
       th.generate_chart(data, width, height, $(that).attr('id'), type);
     }, chart_patient_id, $(that).attr('id'), type, dateStart, dateEnd);
   });

  $('div.taChart').each(function() {
     var that = this;
     var type = $(that).attr('id').replace(/^.+?-(.+?)$/, '$1');
     var chartTitle = $(that).attr('chart-title');
     var dateStart = $(that).attr('chart-date-start');
     var dateEnd = $(that).attr('chart-date-end');
     ta.display_readings(function(data) {
       var width = 220;
       $(that).css('max-width', width);
       var height = 230;
       ta.generate_chart(data, width, height, $(that).attr('id'), type, chartTitle);
     },
      chart_patient_id, $(that).attr('id'), type, dateStart, dateEnd);
  });

});
