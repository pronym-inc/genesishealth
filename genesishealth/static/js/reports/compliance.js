function display_readings(callback, id) {
  var options = {
    method: 'GET',
    url: '/reports/compliance/data/' + id + '/',
    success: callback
  };
  $.ajax(options);
}

function generate_chart(data, width) {
  var chart = new Highcharts.Chart({
    chart: {
      renderTo: 'chart',
      type: 'column'
    },
    credits: {
      enabled: false
    },
    legend: {
      enabled: false
    },
    title: {
      text: 'Compliance Report'
    },
    yAxis: {
      min: 0,
      title: {
        text: 'Readings'
      }
    },
    xAxis: {
      categories: data.labels
    },
    tooltip: {
        formatter: function() {
            return '<strong>' + this.x + '</strong>: ' + this.y;
        }
    },
    series: [{
        name: 'Daily Readings',
        data: data.readings
    }],
    width: width
  });

  window.hcChart = chart;
}

function ready_print_chart(data) {
  var date = new Date;
  var chartText = 'Compliance Report' +
          '<br />Patient: ' + data.patient_name +
          '<br />Date Range: ' + data.date_range +
          '<br />Printed On: ' + date.toLocaleDateString() + ' ' + (date.getHours() % 12) + ':' + (date.getMinutes() < 10 && '0' || '') + date.getMinutes() + ' ' + (date.getHours() < 12 && 'AM' || 'PM') +
          '<br />Printed By: ' + data.professional_name;
  var titleMargin = 80;

  window.printChart = new Highcharts.Chart({
    chart: {
      renderTo: 'print-chart',
      type: 'column'
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
    xAxis: {
      categories: data.labels
    },
    series: [{
        name: 'Daily Readings',
        data: data.readings
    }],
    exporting: {
      enabled: false
    }
  });

  window.hcChart.print = function() {
    window.printChart.print();
  };

  window.hcChart.exportChart = function(a, b) {
    window.printChart.exportChart(a, b);
  };
}

window.ghrCallback = function() {
  if ($('#chart').length > 0) {
    var chart_patient_id;
    if (window.chart_patient_id !== null) {
      chart_patient_id = window.chart_patient_id;
      window.chart_patient_id = null;
    }
    display_readings(function(data) {
      var width = 0.9 * $('#chart').width();
      if (width > (0.9 * $('body').width())) {
        width = 0.9 * $('body').width();
      }
      $('#chart').css('max-width', width);
      generate_chart(data, width);
      ready_print_chart(data);
    }, chart_patient_id);
  }
};
