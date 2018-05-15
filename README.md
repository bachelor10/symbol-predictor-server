# symbol-predictor-server 

This a server including a simple API to run prediction on mathematical symbols and expressions.

## API
The server has a single endpoint, a POST handler the on /api endpoint

```POST /api```

### Input
The endpoint expects data on the format application/JSON.

The request's body should be on the format:
```js
interface Coordinates2D = {x: number, y: number}

interface Buffer = Array<Trace>

{
    "buffer": "Array<Trace>"
}
```
### Output
The output from the endpoint includes:

1. The prediction converted to LaTeX.
2. A list of all the symbols segmented from the traces.
3. A list of the top ten probabilities for each segmented symbol

The response body will be on the format:
```js
interface TraceGroup = Array<number> // List of indexes which combined creates a symbol (indexes from the "buffer" in input). 

interface Probability = number // Number between 0 and 1.
interface Probabilities = Array<Probability> // List of top 10 propabilities.

interface Label = string // A latex representation of a single symbol.
interface Labels = Array<Label> // List of top 10 labels (corresponds with Probabilities).

{
    "latex": string, // The full expression in latex
    "probabilities": {
        "tracegroup": Array<TraceGroup>, // trace indexes combined into symbols
        "labels": Array<Labels>, // The labels corresponding with each probability.
        "values": Array<Probabilities> // The probabilities with length equal to the number of predicted symbols
    }
}
```
