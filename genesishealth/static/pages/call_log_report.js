function createCharts(chartData, useAnimation) {
    $.each(chartData, function(idx, obj) {
        Highcharts.chart(obj.elementID, {
            chart: {
                type: 'column'
            },
            title: {
                text: obj.chartTitle
            },
            xAxis: {
                categories: obj.categories
            },
            yAxis: {
                min: 0,
                title: {
                    text: 'Calls'
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
            series: obj.series
        });
    });
}