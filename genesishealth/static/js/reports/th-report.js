
var th = {
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
    var chartTitle;
    if (type == 'premeal') {
      chartTitle = 'Premeal Glucose Readings';
    } else if (type == 'postmeal') {
      chartTitle = 'Postmeal Glucose Readings';
    } else if (type == 'combined') {
      chartTitle = 'Combined Glucose Readings';
    }

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
        showFirstLabel: false,
        plotBands: [{
            from: -10000,
            to: parseInt(data.glucose_goal[0]),
            color: '#0066cc'
          },
          {
            from: parseInt(data.glucose_goal[0]),
            to: parseInt(data.glucose_goal[1]),
            color: '#3399cc'
          },
          {
            from: parseInt(data.glucose_goal[1]),
            to: parseInt(data.glucose_goal[2]),
            color: '#33cc33'
          },
          {
            from: parseInt(data.glucose_goal[2]),
            to: parseInt(data.glucose_goal[3]),
            color: '#ffff33'
          },
          {
            from: parseInt(data.glucose_goal[3]),
            to: 10000,
            color: '#f2473f'
          }
          ],
          min: 0
      },
      xAxis: {
          type: 'datetime',
          tickPixelInterval: 80,
          startOnTick: false
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
      exporting: {
        enabled: false
      },
      tooltip: {
          formatter: function() {
              return 'Glucose Value: <b>' + this.y + '</b> at <b>' + this.point.datetime + '</b>';
          }
      }
    });
  },
  ready_print_chart: function(data, chartID, type) {
    var date = new Date;
    var chartText = (type.charAt(0).toUpperCase() + type.slice(1)) + ' Glucose Readings' +
            '<br />Patient: ' + data.patient_name +
            '<br />Date Range: ' + data.date_range +
            '<br />Printed On: ' + date.toLocaleDateString() + ' ' + (date.getHours() % 12) + ':' + (date.getMinutes() < 10 && '0' || '') + date.getMinutes() + ' ' + (date.getHours() < 12 && 'AM' || 'PM');
    var titleMargin = 65;
    if (data.professional_name) {
      chartText += '<br />Printed By: ' + data.professional_name;
      titleMargin = 80;
    }
    window[chartID + '-printChart'] = new Highcharts.Chart({
      chart: {
        renderTo: chartID + '-print',
        defaultSeriesType: 'line'
      },
      credits: {
        enabled: false
      },
      legend: {
        enabled: false
      },
      title: {
        text: chartText,
        margin: titleMargin
      },
      yAxis: {
        title: {
          text: 'Glucose'
        },
        showFirstLabel: false,
        plotBands: [
          {
            from: -10000,
            to: parseInt(data.glucose_goal[0]),
            color: '#0066cc'
          },
          {
             from: parseInt(data.glucose_goal[0]),
             to: parseInt(data.glucose_goal[1]),
             color: '#ffff33'
          },
          {
            from: parseInt(data.glucose_goal[1]),
            to: parseInt(data.glucose_goal[2]),
            color: '#33cc33'
          },
          {
            from: parseInt(data.glucose_goal[2]),
            to: parseInt(data.glucose_goal[3]),
            color: '#3399cc'
          },
          {
            from: parseInt(data.glucose_goal[3]),
            to: 10000,
            color: '#f2473f'
          }
        ],
          min: 0
      },
      xAxis: {
          type: 'datetime',
          tickPixelInterval: 120
      },
      series: [{
          data: data.readings
      }],
      exporting: {
        enabled: false
      }
    });

    window[chartID + '-chart'].print = function() {
      window[chartID + '-printChart'].print();
    };

    window[chartID + '-chart'].exportChart = function(a, b) {
      window[chartID + '-printChart'].exportChart(a, b);
    };
  }
};

postCallbackQueue.push(function(div) {
  div.find('div.thChart').each(function() {
    $(this).html('');
     var that = this;
     var type = $(that).attr('id').replace(/^.+?-(.+?)$/, '$1');
       th.display_readings(function(data) {
         var width = 400;
         if (width > (0.95 * $('body').width())) {
           width = 0.95 * $('body').width();
         }
         $(that).css('max-width', width);
         var height = 320;
         th.generate_chart(data, width, height, $(that).attr('id'), type);
         th.ready_print_chart(data, $(that).attr('id'), type);
       }, chart_patient_id, $(that).attr('id'), type);
    });
});
