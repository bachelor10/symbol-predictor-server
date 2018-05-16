import math
import numpy as np

class Boundingbox:
    def __init__(self, traces):
        max_x = 0
        min_x = math.inf
        max_y = 0
        min_y = math.inf

        x_in_max_y = 0

        for trace in traces:
            y = np.array(trace).astype(np.float)
            x, y = y.T

            if max_x < x.max():
                max_x = x.max()

            if max_y < y.max():
                max_y = y.max()
                indexes = np.nonzero(y == max_y)
                x_in_max_y = x[indexes[0][-1]]

            if min_x > x.min():
                min_x = x.min()

            if min_y > y.min():
                min_y = y.min()        
            
        self.mid_x = (max_x + min_x)/2
        self.mid_y = (max_y + min_y)/2
        self.max_x = max_x
        self.max_y = max_y
        self.min_x = min_x
        self.min_y = min_y
        self.width = max_x - min_x
        self.height = max_y - min_y
        self.x_in_max_y = x_in_max_y
