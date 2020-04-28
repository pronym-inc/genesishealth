function createCharts(chartTitle, categories, series, useAnimation) {
    Highcharts.chart('container', {
        chart: {
            type: 'column'
        },
        title: {
            text: false
        },
        xAxis: {
            categories: categories
        },
        yAxis: {
            min: 0,
            title: {
                text: 'Resolved Communications'
            },
            stackLabels: {
                enabled: true
            }
        },
        plotOptions: {
            series: {
                stacking: 'normal',
                animation: useAnimation
            },
            column: {
                stacking: 'normal',
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