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
    type: 'horizontalBar',
    responsive: false,
    maintainAspectRatio: false,
    title: {text: "Sannsynligheter", display: true},
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
            gridLines: {
                offsetGridLines: true
            }
        }]
    }

    
};

var probabilityGraph = new Chart($('#chart'), chartOptions)

function displayGraphs(probabilites){

    //Add an extra element to enforce label width on graph

    chartOptions.data.labels = [...probabilites.labels, ".                ."]
    chartOptions.data.datasets[0].data = [...probabilites.values, 0]

    probabilityGraph.update()
}

/** 
 * Resets canvas size dynamically. Canvas needs fixed sizes.
*/
function setCanvasSize(){
    var containerElement = $('.content-container')
    var canvasElement = $('#canvas')

    
    canvasElement[0].width = containerElement.width()
    canvasElement[0].height = 600

    //To include color on full page
    var body = $(".page-container").css('min-height', window.innerHeight + 'px')

}

$(document).ready(function () {

    //Canvas needs a fixed height and width, therefore set dynamic through js.
    $(window).on('resize', setCanvasSize)
    setCanvasSize()


    var equation = $("#latex");

    var equationRaw = $("#latexRaw");

    var eraseButton = $("#erase")

    var canvasElement = $('#canvas')

    var canvas = new SymbolCanvas(canvasElement[0]);

    var canvasController = new CanvasController(canvas);

    var currentPrediction;
    var currentBuffer;

    //Handle erasing
    eraseButton.click(function(e) {
        canvasController.options.isErasing = !Boolean(canvasController.options.isErasing)
        eraseButton.toggleClass('selected-erase')
    })

    // Fetch from API when canvascontroller returns a buffer. (User is done typing)
    canvasController.on('release', function (buffer){
        console.log("Released", buffer)
        currentBuffer = buffer;
        fetchPrediction(buffer, function(err, result){
            if(err){
                return alert(err)
            }

            katex.render(result.latex, equation[0]);
            equationRaw.text(result.latex);
            
            currentPrediction = result;

            //Display the last drawing in graph
            displayGraphs(currentPrediction.probabilites[currentPrediction.probabilites.length - 1])


        })
    })

    //Mark symbol red when canvascontroller registers a symbolclick
    canvasController.on('symbolclick', function(clickedIndex) {

        //Find the corresponding symbol returned from server. (Server includes which traces were included to group in tracegroup)
        const matchingSymbol = currentPrediction.probabilites.find(proba => {
            return proba.tracegroup.indexOf(clickedIndex) >= 0
        });

        if(matchingSymbol){

            //Redraw all traces to remove possible previous red drawings
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
