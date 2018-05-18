# System setup

This document includes instructions for integration mathematical symbol prediction in Matistikk.

## Overview

There are two projects needed in order to integrate the mathematical predictions into Matistikk. The [predictor client](https://github.com/bachelor10/PredictorClient) and the [predictor server](https://github.com/bachelor10/symbol-predictor-server).

The predictor client is a simple javascript module, which can be included as a script (see [predictor server example](https://github.com/bachelor10/symbol-predictor-server/tree/master/example)), or as an npm module (the package has to be published first or downloaded locally).

The server is currently an independent python (Tornado) server. It can  be used either as an external API (hosted on a different server than Matistikk), or by integrating the prediction code into an existing server.

## Integrating the front end library

Running predictions first requires the input data to be on a specific format, as well as an implementation of drawing on a canvas. Therefore we have created a utility JavaScript module to handle the canvas events, and converting drawings to a format that the server expects.

A full example of using the front end library is found in the [predictor server example](https://github.com/bachelor10/symbol-predictor-server/tree/master/example).

Documentation of the client API can be found in the [predictor client repository](https://github.com/bachelor10/PredictorClient).

## Using the server independent of Matistikk

The predictor server includes code to run the server independently. It is currently hosted on an Heroku server, with both the example implementation and the API. [Symbol Predictor](https://symbol-predictor-server.herokuapp.com
). 

Running the server in your own enviroment is described in the [predictor server README](https://github.com/bachelor10/symbol-predictor-server/blob/master/README.md)

![Model of an independent predictor server connected the Matstikk client.](./independent_server_model2.png "Independent server model")


## Integrating the server to Matistikk

If you wish to host the server using a different library than Tornado, the best approach will be to copy the relevant code, and write your own integration.

All relevant code for prediction is available in the [classification folder]() of predictor server. This is the code you will need to copy into your own project.

An example of interacting with the classification folder can be found in [server.py](https://github.com/bachelor10/symbol-predictor-server/blob/master/server.py). 

In order to use the classification code in Django, you will have to write a POST handler to extract the relevant buffer from the POST request, and run prediction using the components in the classification folder. This can be replicated from the mentioned [server.py](https://github.com/bachelor10/symbol-predictor-server/blob/master/server.py) file.

![Model of an independent predictor server connected the Matstikk client.](https://github.com/bachelor10/symbol-predictor-server/blob/master/docs/combined_sys_model.png "Independent server model")
