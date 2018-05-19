import math, keras
from itertools import cycle, combinations
import numpy as np
from PIL import Image, ImageDraw
from keras.preprocessing import sequence
from classification.fixed_rdp import rdp_fixed_num

class Predictor:

    # Dictinoary for the truth values
    CLASS_INDICES = {'3': 7, 'y': 36, '<': 26, '\\gamma ': 22, '\\beta ': 20, ')': 1, '0': 4, '1': 5, 'sqrt': 33, '\\lambda ': 25, '7': 11, 'z': 37, '6': 10, '\\Delta ': 15, '-': 3, '\\neq ': 28, '=': 14, '8': 12, 'G': 16, '\\sigma ': 32, 'f': 21, '\\rightarrow ': 31, '\\phi ': 29, '\\infty ': 24, 'x': 35, '[': 17, '9': 13, '>': 23, '\\theta ': 34, '\\pi ': 30, '4': 8, '5': 9, '2': 6, '\\mu ': 27, '(': 0, ']': 18, '\\alpha ': 19, '+': 2}
    
    # Dictionary for the class types
    CLASS_TYPES = {'3': 'num', 'y': 'var', '<': 'operator', '\\gamma ': 'var', '\\beta ': 'var', ')': 'structure', '0': 'num', '1': 'num', 'sqrt': 'special', '\\lambda ': 'var', '7': 'num', 'z': 'var', '6': 'num', '\\Delta ': 'var', '-': 'operator', '\\neq ': 'operator', '=': 'operator', '8': 'num', 'G': 'var', '\\sigma ': 'var', 'f': 'var', '\\rightarrow ': 'operator', '\\phi ': 'var', '\\infty ': 'num', 'x': 'var', '[': 'structure', '9': 'num', '>': 'operator', '\\theta ': 'var', '\\pi ': 'var', '4': 'num', '5': 'num', '2': 'num', '\\mu ': 'var', '(': 'structure', ']': 'structure', '\\alpha ': 'var', '+': 'operator'}

    def __init__(self, model_path):
        self.model = keras.models.load_model(model_path)


    def predict(self, segment_traces, truth):

        # Create input data for the neural network
        input_image = self.create_image(segment_traces)
        sequence = self.create_sequence(segment_traces)        
        
        # Predict the class with the model
        truth_proba = self.model.predict([sequence, input_image])
        bestProbabilites = np.argsort(truth_proba[0])[::-1][:10]

        labels = []
        values = []
        truth = ''
        type_truth = ''

        # Get the corresponding class from the indices and clas dictionaries
        for i, index in enumerate(bestProbabilites):
            for key, value in Predictor.CLASS_INDICES.items():
                if value == index:
                    if i == 0:
                        truth = key
                        type_truth = Predictor.CLASS_TYPES[key]
                    
                    labels.append(key)
                    values.append(float(truth_proba[0][index]))

        return truth, {
            'labels': labels,
            'values': values
        }, type_truth


    def scale_linear_bycolumn(self, rawpoints, high=24, low=0, ma=0, mi=0):
        # Scales a input list of numerical values to a given interval
        mins = mi
        maxs = ma
        rng = maxs - mins

        output = high - (((high - low) * (maxs - rawpoints)) / rng)

        return output


    def create_image(self, traces):
        # Creates the image used for classification in the neural network

        # Constants for image resolution
        resolution = 26
        image_resolution = 26

        image = Image.new('L', (image_resolution, image_resolution), "black")
        draw = ImageDraw.Draw(image)

        max_x = 0
        min_x = math.inf
        max_y = 0
        min_y = math.inf

        # Iterate through the traces and find maximim and minimum values
        for trace in traces:
            y = np.array(trace).astype(np.float)
            x, y = y.T

            if max_x < x.max():
                max_x = x.max()

            if max_y < y.max():
                max_y = y.max()

            if min_x > x.min():
                min_x = x.min()

            if min_y > y.min():
                min_y = y.min()

        width = max_x - min_x
        height = max_y - min_y
        scale = width / height

        width_scale = 0
        height_scale = 0

        if scale > 1:
            # If width > height
            height_scale = resolution / scale
        else:
            # If width < height
            width_scale = resolution * scale

        for trace in traces:

            y = np.array(trace).astype(np.float)

            x, y = y.T

            if width_scale > 0:
                # Add padding in x-direction
                new_y = self.scale_linear_bycolumn(y, high=resolution, low=0, ma=max_y, mi=min_y)
                side = (resolution - width_scale) / 2
                new_x = self.scale_linear_bycolumn(x, high=(resolution - side), low=(side), ma=max_x, mi=min_x)
            else:
                # Add padding in y-direction
                new_x = self.scale_linear_bycolumn(x, high=resolution, low=0, ma=max_x, mi=min_x)  # , maximum=(max_x, max_y), minimum=(min_x, min_y))
                side = (resolution - height_scale) / 2
                new_y = self.scale_linear_bycolumn(y, high=(resolution - side), low=(side), ma=max_y, mi=min_y)  # , maximum=(max_x, max_y), minimum=(min_x, min_y))

            coordinates = list(zip(new_x, new_y))
            xy_cycle = cycle(coordinates)

            next(xy_cycle)

            # Draw lines between points
            for x_coord, y_coord in coordinates[:-1]:
                next_coord = next(xy_cycle)
                draw.line([x_coord, y_coord, next_coord[0], next_coord[1]], fill="white", width=1)

        return np.array(image).reshape(1, 26, 26, 1)/255


    def scale_traces(self, trace, resolution=1):

        trace = np.array(trace)

        # Extract x- and y-coordinates
        traceX = trace[:, 0]
        traceY = trace[:, 1]

        # Find maximum and minimum values
        max_x = np.max(traceX)
        min_x = np.min(traceX)
        max_y = np.max(traceY)
        min_y = np.min(traceY)

        # Find width, height and the ratio
        width = max_x - min_x
        height = max_y - min_y
        scale = width / height

        width_scale = 0
        height_scale = 0

        if scale > 1:
            # If width > height
            height_scale = resolution / scale
        else:
            # If width < height
            width_scale = resolution * scale

        side = (resolution - width_scale) / 2

        if width_scale > 0:
            # Add padding in x-direction
            trace[:,1] = self.scale_linear_bycolumn(trace[:,1], high=resolution, low=-resolution, ma=max_y, mi=min_y)
            side = (resolution - width_scale) / 2
            trace[:,0] = self.scale_linear_bycolumn(trace[:,0], high=(resolution - side), low=(-resolution + side), ma=max_x, mi=min_x)
        else:
            # Add padding in y-direction
            trace[:,0] = self.scale_linear_bycolumn(trace[:,0], high=resolution, low=-resolution, ma=max_x, mi=min_x) 
            side = (resolution - height_scale) / 2
            trace[:,1] = self.scale_linear_bycolumn(trace[:,1], high=(resolution - side), low=(-resolution +side), ma=max_y, mi=min_y) 

        return trace


    def combine_segment(self, traces):
        # Combines a list of traces to a single trace

        combined_segment = []

        max_len = -math.inf
        for trace in traces:
            if(len(trace) > max_len):
                max_len = len(trace) 

        for trace in traces:
            for i, coords in enumerate(trace):
                if i == len(trace) - 1:
                    combined_segment.append([coords[0], coords[1], 1])
                else:
                    combined_segment.append([coords[0], coords[1], 0])

        return np.array(combined_segment)


    def run_rdp_on_traces(self, traces):
        # Iterates through the traces and downsamples each with rdp to 40 points

        traces_after_rdp = []

        for trace in traces:
            rdp_ed = rdp_fixed_num(np.array(trace), 40)
            traces_after_rdp.append(rdp_ed)

        return traces_after_rdp


    def create_sequence(self, traces): 
        # Creates the sequential input data

        processed = self.run_rdp_on_traces(traces)
        processed = self.combine_segment(processed)
        processed = self.scale_traces(np.array(processed, dtype="float32"))

        return sequence.pad_sequences([processed], dtype='float32', maxlen=40)
