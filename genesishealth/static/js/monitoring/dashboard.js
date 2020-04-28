updateCallbackQueue.push(function(div) {
    // Database data
    Highcharts.setOptions({
        global: {
            getTimezoneOffset: function (timestamp) {
                var zone = 'America/Chicago',
                    timezoneOffset = -moment.tz(timestamp, zone).utcOffset();
                return timezoneOffset;
            }
        }
    });
    $.getJSON(window.chartDataURLs.databaseServers, function(data) {
        function makeSeries(data) {
            var seriesOptions = [];
            $.each(data, function(key, value) {
                seriesOptions.push({
                    name: key + ' Load',
                    data: value.load,
                    dataGrouping: 'load'
                });
                seriesOptions.push({
                    name: key + ' Memory',
                    data: value.memory_free,
                    dataGrouping: 'memory',
                    yAxis: 1
                });
            });
            return seriesOptions;
        }
        var seriesOptions = makeSeries(data);
        $('#databaseChart').highcharts('StockChart', {
            yAxis: [{
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Load'
                },
                height: '60%',
                lineWidth: 2,
                max: 2
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Memory Free (MB)'
                },
                top: '65%',
                height: '35%',
                offset: 0,
                lineWidth: 2,
            }],
            navigator: {
                enabled: false
            },
            plotOptions: {
            },
            rangeSelector: {
                enabled: false
            },
            scrollbar: {
                enabled: false
            },
            tooltip: {
                pointFormat: '{series.name}: <b>{point.y}</b> ({point.change}%)<br/>',
                valueDecimals: 2
            },
            series: seriesOptions
        });
    });
    // Reading data
    $.getJSON(window.chartDataURLs.readingServers, function(data) {
        function makeSeries(data) {
            var seriesOptions = [];
            $.each(data, function(key, value) {
                seriesOptions.push({
                    name: key + ' Load',
                    data: value.load,
                    dataGrouping: 'load'
                });
                seriesOptions.push({
                    name: key + ' Memory',
                    data: value.memory_free,
                    dataGrouping: 'memory',
                    yAxis: 1
                });
                seriesOptions.push({
                    name: key + ' Reading Response Time',
                    data: value.reading_response_time,
                    dataGrouping: 'response_time',
                    yAxis: 2
                });
                seriesOptions.push({
                    name: key + ' Readings Received',
                    data: value.readings_received,
                    dataGrouping: 'readings_received',
                    yAxis: 3
                });
            });
            return seriesOptions;
        }
        var seriesOptions = makeSeries(data);
        $('#readingChart').highcharts('StockChart', {
            yAxis: [{
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Load'
                },
                height: '23%',
                lineWidth: 2,
                max: 2
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Memory Free (MB)'
                },
                top: '25%',
                height: '23%',
                offset: 0,
                lineWidth: 2,
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Response Time',
                },
                top: '50%',
                height: '23%',
                offset: 0,
                lineWidth: 2,
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Readings / 10 min',
                },
                top: '75%',
                height: '23%',
                offset: 0,
                lineWidth: 2,
            }],
            plotOptions: {
            },
            navigator: {
                enabled: false
            },
            rangeSelector: {
                enabled: false
            },
            scrollbar: {
                enabled: false
            },
            tooltip: {
                pointFormat: '{series.name}: <b>{point.y}</b> ({point.change}%)<br/>',
                valueDecimals: 2
            },
            series: seriesOptions
        });
    });
    // Web data
    $.getJSON(window.chartDataURLs.webServers, function(data) {
        function makeSeries(data) {
            var seriesOptions = [];
            $.each(data, function(key, value) {
                seriesOptions.push({
                    name: key + ' Load',
                    data: value.load,
                    dataGrouping: 'load'
                });
                seriesOptions.push({
                    name: key + ' Memory',
                    data: value.memory_free,
                    dataGrouping: 'memory',
                    yAxis: 1
                });
            });
            return seriesOptions;
        }
        var seriesOptions = makeSeries(data);
        $('#webChart').highcharts('StockChart', {
            yAxis: [{
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Load'
                },
                height: '60%',
                lineWidth: 2,
                max: 2
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Memory Free (MB)'
                },
                top: '65%',
                height: '35%',
                offset: 0,
                lineWidth: 2,
            }],
            plotOptions: {
            },
            navigator: {
                enabled: false
            },
            rangeSelector: {
                enabled: false
            },
            scrollbar: {
                enabled: false
            },
            tooltip: {
                pointFormat: '{series.name}: <b>{point.y}</b> ({point.change}%)<br/>',
                valueDecimals: 2
            },
            series: seriesOptions
        });
    });
    // MQ data
    $.getJSON(window.chartDataURLs.workerServers, function(data) {
        function makeSeries(data) {
            var seriesOptions = [];
            $.each(data, function(key, value) {
                seriesOptions.push({
                    name: key + ' Load',
                    data: value.load,
                    dataGrouping: 'load'
                });
                seriesOptions.push({
                    name: key + ' Memory',
                    data: value.memory_free,
                    dataGrouping: 'memory',
                    yAxis: 1
                });
                if (value.message_count) {
                   seriesOptions.push({
                        name: key + ' Messages',
                        data: value.message_count,
                        dataGrouping: 'messages',
                        yAxis: 2
                    }); 
                }
            });
            return seriesOptions;
        }
        var seriesOptions = makeSeries(data);
        $('#workerChart').highcharts('StockChart', {
            chart: {
                zoomType: 'x'
            },
            yAxis: [{
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Load'
                },
                height: '30%',
                lineWidth: 2,
                max: 2
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Memory Free (MB)'
                },
                top: '33%',
                height: '30%',
                offset: 0,
                lineWidth: 2,
            }, {
                labels: {
                    align: 'right',
                    x: -3
                },
                title: {
                    text: 'Messages',
                },
                top: '66%',
                height: '33%',
                offset: 0,
                lineWidth: 2,
            }],
            plotOptions: {
            },
            navigator: {
                enabled: false
            },
            scrollbar: {
                enabled: false
            },
            rangeSelector: {
                enabled: false
            },
            tooltip: {
                pointFormat: '{series.name}: <b>{point.y}</b> ({point.change}%)<br/>',
                valueDecimals: 2
            },
            series: seriesOptions
        });
    });
});