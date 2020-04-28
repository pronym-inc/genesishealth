function createCharts(chartTitle, categories, series, useAnimation) {
    Highcharts.chart('container', {
        chart: {
            type: 'bar'
        },
        title: {
            text: chartTitle
        },
        xAxis: {
            categories: categories
        },
        yAxis: {
            min: 0,
            title: {
                text: false
            },
            stackLabels: {
                enabled: true
            }
        },
        plotOptions: {
            series: {
                animation: useAnimation
            },
            bar: {
                dataLabels: {
                    enabled: true,
                    formatter: function() {
                        if (this.y === 0) {
                            return;
                        }
                        return this.y;
                    }
                }
            }
        },
        series: series
    });
}