"use strict";


function fetchPrediction(buffer, callback) {

    $.ajax({
        type: "POST",
        url: "/api",
        crossDomain: true,
        data: JSON.stringify({
            buffer: buffer,
        }),
        success: function (data) {
            var parsedData = JSON.parse(data);
            callback(null, parsedData)
        },
        error: function (error) {
            alert(error)
        }
    });
}



var chartOptions = {
    type: 'bar',
    responsive: false,
    data: {
        labels: [],
        datasets: [
            {
            label: 'Sannsynligheter',
            data: [],
            
            backgroundColor: [
                'rgb(255, 99, 132)',
                'rgb(54, 162, 235)',
                'rgb(255, 206, 86)',
                'rgb(75, 192, 192)',
                'rgb(153, 102, 255)',
                'rgba(255, 159, 64, 0.2)'
            ],
        }],
        
    },
    scales: {
        xAxes: [{
            barThickness : 10
        }]
    }
};

var myNewChart = new Chart($('#chart'), chartOptions)

function displayGraphs(probabilites){
    //Number of graphs to display

    chartOptions.data.labels = probabilites.labels
    chartOptions.data.datasets[0].data = probabilites.values

    myNewChart.update()
}


$(document).ready(function () {

    var equation = $("#latex");

    var equationRaw = $("#latexRaw");

    var eraseButton = $("#erase")

    var canvas = new SymbolCanvas($('#canvas')["0"]);

    var canvasController = new CanvasController(canvas);

    var currentPrediction;
    var currentBuffer;

    eraseButton.click(function(e) {
        canvas.options.isErasing = !Boolean(canvas.options.isErasing)
    })

    canvasController.on('release', function (buffer){
        currentBuffer = buffer;
        fetchPrediction(buffer, function(err, result){
            if(err){
                return alert(err)
            }

            katex.render(result.latex, equation[0]);
            equationRaw.text(result.latex);
            
            currentPrediction = result;

        })
    })

    canvasController.on('symbolclick', function(clickedIndex) {

        const matchingSymbol = currentPrediction.probabilites.find(proba => {
            return proba.tracegroup.indexOf(clickedIndex) >= 0
        });

        if(matchingSymbol){
            currentBuffer.forEach((trace, i) => {
                if(matchingSymbol.tracegroup.indexOf(i) >= 0){
                    canvasController.markTraceGroups([i], 'red')
                }
                else {
                    canvasController.markTraceGroups([i], '#A0A3A6')
                }
            })
            displayGraphs(matchingSymbol)
        }



    })


});
