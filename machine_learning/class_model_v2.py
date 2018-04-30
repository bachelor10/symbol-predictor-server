import math, keras
from itertools import cycle, combinations
import numpy as np
from PIL import Image, ImageDraw
from keras.preprocessing import sequence
from rdp import rdp
import matplotlib.pyplot as plt
from rpd_test import rdp_fixed_num

plt.style.use('ggplot')

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


class Segment:
    def __init__(self, id, truth, segment_type, traces):
        self.id = id
        self.traces = traces
        self.boundingbox = Boundingbox(traces)
        self.truth = truth
        self.type = segment_type

    def to_latex(self):
        return self.truth


class Group:
    def __init__(self, id, traces):
        self.id = id
        self.traces = traces
        self.boundingbox = Boundingbox(traces)
        self.truth = 'group'
        self.type = 'group'
            
    def to_latex(self):

        latex = ''

        if type(self) == Segmentgroup:

            for obj in self.objects:
                latex += obj.to_latex()

        elif type(self) == Fraction:
            
            latex += '\\frac{'
            
            for obj in self.numerator:
                latex += obj.to_latex()

            latex += '}{'

            for obj in self.denominator:
                latex += obj.to_latex()

            latex += '}'

        elif type(self) == Power:
            
            for obj in self.base:   
                latex += obj.to_latex()

            latex += '^{'
            
            for obj in self.exponent:
                latex += obj.to_latex()
            
            latex += '}'

        elif type(self) == Root:

            latex += '\\sqrt{'

            for obj in self.core:
                latex += obj.to_latex()

            latex += '}'

        return latex


class Segmentgroup(Group):
    def __init__(self, id, objects):
        super().__init__(id)
        self.objects = objects


    def add_object(self, obj):
        self.objects.append(obj)


    def to_latex(self):
        return super().to_latex()

        
class Fraction(Group):
    def __init__(self, id, numerator, denominator, frac_traces):

        traces = frac_traces
        for obj in numerator:
            traces += obj.traces

        for obj in denominator:
            traces += obj.traces

        super().__init__(id, traces)
        self.numerator = numerator
        self.denominator = denominator

    def to_latex(self):
        return super().to_latex()


class Power(Group):
    def __init__(self, id, base, exponent):

        traces = []

        for obj in base: 
            traces += obj.traces

        for obj in exponent:
            traces += obj.traces

        super().__init__(id, traces)
        self.base = base
        self.exponent = exponent

    def to_latex(self):
        return super().to_latex()


class Root(Group):
    def __init__(self, id, core, root_traces):

        traces = root_traces
        for obj in core:
            traces += obj.traces
            
        super().__init__(id, traces)
        self.core = core

    def to_latex(self):
        return super().to_latex()


class Sum(Group):
    def __init__(self, id, mid_x, body):
        super().__init__(id, mid_x)
        self.body = body

    def to_latex(self):
        return super().to_latex()


class Integral(Group):
    pass


class Expression:
    def __init__(self, predictor):
        self.segments = []
        self.groups = []
        self.predictor = predictor
        self.preprocessor = Preprocessor()

    def feed_traces(self, traces, truth):
        overlap_pairs = self.preprocessor.find_overlap_pairs(traces)
        tracegroups = self.preprocessor.create_tracegroups(traces, overlap_pairs)
        
        probabilities = []

        for i, group in enumerate(tracegroups):
            segment_traces = [traces[j] for j in list(group)]
            id = str(i)

            predicted_truth, proba, predicted_type = self.predictor.predict(segment_traces, truth)

            proba['tracegroup'] = group
            probabilities.append(proba)

            segment = Segment(id, predicted_truth, predicted_type, segment_traces)
            self.segments.append(segment)

        self.groups = self.recursive_search_for_context(self.segments, 10000, 0, 10000, 0)

        return probabilities


    def recursive_search_for_context(self, objects, max_x, min_x, max_y, min_y):
        
        objects = self.find_roots(objects)
        objects = self.find_fractions(objects, max_x, min_x, max_y, min_y)
        objects = self.find_equalsigns(objects)
        objects = self.find_multiplicationsigns(objects)
        objects = self.sort_objects_by_x_value(objects)
        objects = self.find_exponents(objects, max_x, min_x, max_y, min_y)
        objects = self.sort_objects_by_x_value(objects)

        return objects


    def find_objects_in_area(self, max_x, min_x, max_y, min_y, objects):
        # Find segments and groups in specified area
        # Searches for middle values (mid_x, mid_y)
        # Format:
        # 
        # min_x, min_y ---------------
        # |                          |
        # |                          |
        # ----------------max_x, max_y

        # To return:
        objects_found = []

        # Find segments in area
        for obj in objects:
            if min_x < obj.boundingbox.mid_x < max_x and min_y < obj.boundingbox.mid_y < max_y:
                objects_found.append(obj)

        return objects_found


    def find_roots(self, objects):
        # Find all roots and sort them by width
        roots = [obj for obj in objects if obj.truth == 'sqrt']
        roots = self.sort_objects_by_width(roots)

        # Find context in roots
        for root in roots:
            if root in objects:
                objects.remove(root)

            # Find core
            core = self.find_objects_in_area(root.boundingbox.max_x, root.boundingbox.x_in_max_y, root.boundingbox.max_y, root.boundingbox.min_y, objects)

            if len(core) > 0:
                # Remove core objects from objects and roots
                for core_obj in core:
                    if core_obj in roots:
                        roots.remove(core_obj)

                    if core_obj in objects:
                        objects.remove(core_obj)

                # Send core objects to recursive search for context
                core = self.recursive_search_for_context(core, root.boundingbox.max_x, root.boundingbox.x_in_max_y, root.boundingbox.max_y, root.boundingbox.min_y)
                
                # Create Root object
                root_obj = Root(root.id, core, root.traces)

                # Add to groups
                objects.append(root_obj)
                
            else:
                root_obj = Root(root.id, [], root.traces)
                objects.append(root_obj)

        return objects


    def check_if_fraction(self, minus_sign, objects, max_y, min_y):

        max_x = minus_sign.boundingbox.max_x
        min_x = minus_sign.boundingbox.min_x
        
        minus_signs = [obj for obj in objects if obj.truth == '-']

        numerator = self.find_objects_in_area(max_x, min_x, minus_sign.boundingbox.mid_y - 1, min_y, objects)
        denominator = self.find_objects_in_area(max_x, min_x, max_y, minus_sign.boundingbox.mid_y + 1, objects)

        if len(numerator) > 1 or len(denominator) > 1:
            return True, numerator, denominator
        
        if len(numerator) > 0 or len(denominator) > 0:
            if len(minus_signs) == 1:
                return True, numerator, denominator
        
        if len(numerator) > 0 and len(denominator) > 0:
            return True, numerator, denominator
        else:
            return False, numerator, denominator
    

    def find_fractions(self, objects, max_x, min_x, max_y, min_y):
        # Find all minus signs and sort them by width
        minus_signs = [obj for obj in objects if obj.truth == '-']
        minus_signs = self.sort_objects_by_width(minus_signs)

        # Find fractions and context in numerator/denominator
        for minus_sign in minus_signs:
            # Check if minus sign can be a fraction, check if there are objects over and under
            obj_is_frac, numerator, denominator = self.check_if_fraction(minus_sign, objects, max_y, min_y)

            if obj_is_frac:
                objects.remove(minus_sign)

                # Remove fraction objects found from objects
                for obj in numerator:
                    if obj in minus_signs:
                        minus_signs.remove(obj)

                    if obj in objects:
                        objects.remove(obj)

                for obj in denominator:
                    if obj in minus_signs:
                        minus_signs.remove(obj)

                    if obj in objects:
                        objects.remove(obj)
                
                # Find context in numerator
                numerator = self.recursive_search_for_context(numerator, minus_sign.boundingbox.max_x, minus_sign.boundingbox.min_x, minus_sign.boundingbox.mid_y - 1, min_y)

                # Find context in denominator
                denominator = self.recursive_search_for_context(denominator, minus_sign.boundingbox.max_x, minus_sign.boundingbox.min_x, max_x, minus_sign.boundingbox.mid_y + 1)

                # Create Fraction object
                fraction = Fraction(minus_sign.id, numerator, denominator, minus_sign.traces)
                
                # Add to groups
                objects.append(fraction)

        return objects


    def check_if_equalsign(self, minus_one, minus_two):
        mid_x_one = minus_one.boundingbox.mid_x
        mid_x_two = minus_two.boundingbox.mid_x
        mid_y_one = minus_one.boundingbox.mid_y
        mid_y_two = minus_two.boundingbox.mid_y
        width_one = minus_one.boundingbox.width
        width_two = minus_two.boundingbox.width

        # Check if widths are similar
        if np.abs(width_one - width_two) > (width_one + width_two)/2:
            return False
        
        # Check if mid_x values are inside treshhold
        if np.abs(mid_x_one - mid_x_two) > (width_one + width_two)/3:
            return False
        
        # Check if mid_y values are inside treshhold
        if np.abs(mid_y_one - mid_y_two) > (width_one + width_two)/2:
            return False

        return True


    def find_equalsigns(self, objects):
        # Find equalsigns
        minus_signs = [obj for obj in objects if obj.truth == '-']

        for pair in combinations(minus_signs, r=2):
            if self.check_if_equalsign(pair[0], pair[1]):
                pair_processed = False
                
                # Remove from objects
                if pair[0] in objects and pair[1] in objects:
                    objects.remove(pair[0])
                    objects.remove(pair[1])
                else:
                    pair_processed = True

                if not pair_processed:
                    # Create equal object
                    equal_obj = Segment(pair[0].id, '=', 'operator', pair[0].traces + pair[1].traces)

                    # Add to objects
                    objects.append(equal_obj)
                
        return objects

    
    def check_if_multiplication(self, object, avg_area):
             
        obj_area = object.boundingbox.width * object.boundingbox.height

        if obj_area > 250:
            return False

        if object.boundingbox.height > 20 or object.boundingbox.width > 20:
            return False

        if obj_area < 51:
            return True

        if object.boundingbox.width >= 2 * object.boundingbox.height:
            return False

        if object.boundingbox.height >= 2 * object.boundingbox.width:
            return False

        return True

    def find_multiplicationsigns(self, objects):
        
        if len(objects) == 0:
            return objects

        area = 0

        for obj in objects:
            area += obj.boundingbox.width * obj.boundingbox.height

        avg_area = area / len(objects)

        for i, obj in enumerate(objects):
            
            if self.check_if_multiplication(obj, avg_area):
                objects[i].truth = '\cdot '
                objects[i].type = 'operator'
                
        return objects

    def check_if_exponent(self, base, exponent):
        mid_y_base = base.boundingbox.mid_y
        max_y_exp = exponent.boundingbox.max_y
        mid_y_exp = exponent.boundingbox.mid_y
        base_treshhold = (base.boundingbox.mid_y + base.boundingbox.min_y) / 2

        # Check if mid_y values are inside treshhold
        if max_y_exp > mid_y_base:
            return False

        if mid_y_exp > base_treshhold:
            return False

        if exponent.type == 'operator':
            if max_y_exp > base_treshhold:
                return False

        return True


    def find_exponents(self, objects, max_x, min_x, max_y, min_y):
         # Find exponents
        looking_for_exponents = True

        while looking_for_exponents:

            found_exponent = False

            for i, base in enumerate(objects[:-1]):

                # Operators and special signs should not have exponents         
                if base.type != 'operator' and base.type != 'special':

                    obj_base = []
                    obj_exp = []

                    # Search for exponent for current base
                    for exp in objects[i+1:]:
                        if self.check_if_exponent(base, exp):
                            obj_exp.append(exp)
                        else:
                            # Break out of loop when the sequence of exponents is broken for the first time
                            break

                    # Check if any exponent were found for current base
                    if len(obj_exp) > 0:
                        # Update objects
                        objects = [i for i in objects if i not in obj_exp]

                        # Look for context in exponent group
                        obj_exp = self.recursive_search_for_context(obj_exp, max_x, min_x, max_y, min_y)

                        objects.remove(base)
                        obj_base.append(base)
                        
                        # Create and add power group to objects
                        power = Power(base.id, obj_base, obj_exp)
                        objects.insert(0, power)
                        objects = self.sort_objects_by_x_value(objects)

                        found_exponent = True
                
                # If any exponent were found, restart the for loop
                if found_exponent:
                    break

            # Continue if no exponent were found
            if not found_exponent:
                break

        return objects


    def sort_objects_by_width(self, objects):
        return sorted(objects, key=lambda x: x.boundingbox.width, reverse=True)


    def sort_objects_by_x_value(self, objects):
        return sorted(objects, key=lambda x: x.boundingbox.mid_x, reverse=False)


    def to_latex(self):
        latex = ''
        for group in self.groups:
            latex += group.to_latex()
            
        return latex


class Preprocessor:
    def __init__(self):
        pass


    def find_single_trace_distances(self, trace):
        trace_cycle = cycle(trace)
        next(trace_cycle)

        distances = []

        for point in trace[:-1]:
            next_point = next(trace_cycle)
            dist = math.hypot(next_point[0] - point[0], next_point[1] - point[1])

            distances.append(dist)
        return distances

    
    def add_points_to_trace(self, trace, goal):
        
        while len(trace) < goal:
            to_add = goal - len(trace)

            if to_add > len(trace):
                to_add = len(trace) - 1

            distances = self.find_single_trace_distances(trace)
            distances_index = [[j, i] for i, j in enumerate(distances)]
            sorted_distances_index = np.asarray(sorted(distances_index, reverse=True))
            
            try:
                for i in sorted_distances_index[0:to_add, 1]:
                    index = int(i)

                    new_x = (trace[index][0] + trace[index + 1][0]) / 2
                    new_y = (trace[index][1] + trace[index + 1][1]) / 2

                    trace = np.insert(trace, index+1, np.array((new_x, new_y)), axis=0)
            except IndexError:
                return trace

        return trace

    
    def find_overlap_pairs(self, traces):
        overlap_pairs = set()

        traces_with_added_points = []

        for i, trace in enumerate(traces):
            new_trace = self.add_points_to_trace(trace, len(trace)*2)
            traces_with_added_points.append(new_trace)

        for i, trace in enumerate(traces[:-1]):
            for j, trace2 in enumerate(traces[i+1:]):
                for coord1 in trace:
                    for coord2 in trace2:
                        if math.hypot(coord2[0] - coord1[0], coord2[1] - coord1[1]) < 10:
                            overlap_pairs.add((i, i+j+1))
        
        return overlap_pairs

    
    def create_tracegroups(self, traces, trace_pairs):
        tracegroups = []
        
        for i, trace in enumerate(traces):

            flag = False
            for j, group in enumerate(tracegroups):

                common = []
                for p in trace_pairs:
                    if i in p:
                        common = common + list(p)
                common = list(set(common))

                if len(set(common).intersection(group)) > 0:
                     tracegroups[j] = list(set(common + group))
                     flag = True

            if not flag:
                new_group = [i]
                for pair in trace_pairs:
                    if i in pair:
                        new_group = new_group + list(pair)
                
                new_group = list(set(new_group))
                tracegroups.append(new_group)
            
        sorted_tracegroups = sorted(tracegroups, key=lambda m:next(iter(m)))
        return sorted_tracegroups



class Predictor:

    #CLASS_INDICES = {']': 17, 'z': 38, 'int': 23, 'sqrt': 32, '3': 7, '\\infty': 22, '\\neq': 27, '6': 10, '0': 4, '[': 16, '7': 11, '4': 8, '(': 0, 'x': 36, '\\alpha': 18, '\\lambda': 24, '\\beta': 19, '\\rightarrow': 30, '8': 12, ')': 1, '=': 14, 'y': 37, '\\phi': 28, 'x': 35, '1': 5, '<': 25, '\\Delta': 15, '\\gamma': 20, '9': 13, '\\pi': 29, '2': 6, '\\sum': 33, '\\theta': 34, '\\mu': 26, '-': 3, '>': 21, '+': 2, '\\sigma': 31, '5': 9}
    #CLASS_TYPES = {']': 'structure', 'z': 'var', 'int': 'special', 'sqrt': 'special', '3': 'num', '\\infty': 'num', '\\neq': 'operator', '6': 'num', '0': 'num', '[': 'structure', '7': 'num', '4': 'num', '(': 'structure', 'x': 'var', '\\alpha': 'var', '\\lambda': 'var', '\\beta': 'var', '\\rightarrow': 'operator', '8': 'num', ')': 'structure', '=': 'operator', 'y': 'var', '\\phi': 'var', 'x': 'var', '1': 'num', '<': 'operator', '\\Delta': 'var', '\\gamma': 'var', '9': 'num', '\\pi': 'var', '2': 'num', '\\sum': 'special', '\\theta': 'var', '\\mu': 'var', '-': 'operator', '>': 'operator', '+': 'operator', '\\sigma': 'var', '5': 'num'}


    CLASS_INDICES = {'3': 7, 'y': 36, '<': 26, '\\gamma ': 22, '\\beta ': 20, ')': 1, '0': 4, '1': 5, 'sqrt': 33, '\\lambda ': 25, '7': 11, 'z': 37, '6': 10, '\\Delta ': 15, '-': 3, '\\neq ': 28, '=': 14, '8': 12, 'G': 16, '\\sigma ': 32, 'f': 21, '\\rightarrow ': 31, '\\phi ': 29, '\\infty ': 24, 'x': 35, '[': 17, '9': 13, '>': 23, '\\theta ': 34, '\\pi ': 30, '4': 8, '5': 9, '2': 6, '\\mu ': 27, '(': 0, ']': 18, '\\alpha ': 19, '+': 2}
    CLASS_TYPES = {'3': 'num', 'y': 'var', '<': 'operator', '\\gamma ': 'var', '\\beta ': 'var', ')': 'structure', '0': 'num', '1': 'num', 'sqrt': 'special', '\\lambda ': 'var', '7': 'num', 'z': 'var', '6': 'num', '\\Delta ': 'var', '-': 'operator', '\\neq ': 'operator', '=': 'operator', '8': 'num', 'G': 'var', '\\sigma ': 'var', 'f': 'var', '\\rightarrow ': 'operator', '\\phi ': 'var', '\\infty ': 'num', 'x': 'var', '[': 'structure', '9': 'num', '>': 'operator', '\\theta ': 'var', '\\pi ': 'var', '4': 'num', '5': 'num', '2': 'num', '\\mu ': 'var', '(': 'structure', ']': 'structure', '\\alpha ': 'var', '+': 'operator'}

    def __init__(self, model_path):
        self.model = keras.models.load_model(model_path)
        #self.trainY = []
        #self.trainX_img = []
        #self.trainX_trace = []

        #try:
        #    self.trainY = np.load('./data/trainY').to_list()
        #    self.trainX_img = np.load('./data/trainX_img').to_list()
        #    self.trainY_trace = np.load('./data/trainY_trace').to_list()
        #except:
        #    pass

    def vizualize(self, image, sequence):
        f, (ax1, ax2) = plt.subplots(1, 2)
        ax1.imshow(np.array(image).reshape(26, 26))
        ax2.plot(sequence[0][:, 0], sequence[0][:, 1], '-o')
        ax2.set_xlim([-1, 1])
        ax2.set_ylim([1, -1])


        plt.show()

    def store_train_data(self, image, sequence, truth):

        trainY = np.zeros(len(Predictor.CLASS_INDICES.keys()))
        print("TRUTH", truth)
        try:
            trainY[Predictor.CLASS_INDICES[truth]] = 1.0
        except KeyError as e:
            print("Error", e)
            return
        
        self.trainY.append(trainY)
        self.trainX_img.append(image)
        self.trainX_trace.append(sequence)

        np.save('./data/trainY', np.array(self.trainY))
        np.save('./data/trainX_img', np.array(self.trainX_img))
        np.save('./data/trainX_trace', np.array(self.trainX_trace))


    def predict(self, segment_traces, truth):
        input_image = self.create_image(segment_traces)
        sequence = self.create_sequence(segment_traces)
        
        #self.store_train_data(input_image, sequence, truth)
        #self.vizualize(input_image, sequence)
        truth_proba = self.model.predict([sequence, input_image])
        bestProbabilites = np.argsort(truth_proba[0])[::-1][:10]

        labels = []
        values = []
        truth = ''
        type_truth = ''

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
        mins = mi
        maxs = ma

        rng = maxs - mins

        output = high - (((high - low) * (maxs - rawpoints)) / rng)

        return output

    def create_image(self, traces):
        resolution = 26
        image_resolution = 26

        image = Image.new('L', (image_resolution, image_resolution), "black")
        draw = ImageDraw.Draw(image)


        max_x = 0
        min_x = math.inf
        max_y = 0
        min_y = math.inf


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
            # width > height
            height_scale = resolution / scale
        else:
            # width < height
            width_scale = resolution * scale

        for trace in traces:

            y = np.array(trace).astype(np.float)

            x, y = y.T

            if width_scale > 0:
                # add padding in x-direction
                new_y = self.scale_linear_bycolumn(y, high=resolution, low=0, ma=max_y, mi=min_y)
                side = (resolution - width_scale) / 2
                new_x = self.scale_linear_bycolumn(x, high=(resolution - side), low=(side), ma=max_x, mi=min_x)
            else:
                # add padding in y-direction
                new_x = self.scale_linear_bycolumn(x, high=resolution, low=0, ma=max_x, mi=min_x)  # , maximum=(max_x, max_y), minimum=(min_x, min_y))
                side = (resolution - height_scale) / 2
                new_y = self.scale_linear_bycolumn(y, high=(resolution - side), low=(side), ma=max_y, mi=min_y)  # , maximum=(max_x, max_y), minimum=(min_x, min_y))

            coordinates = list(zip(new_x, new_y))
            xy_cycle = cycle(coordinates)

            next(xy_cycle)

            for x_coord, y_coord in coordinates[:-1]:
                next_coord = next(xy_cycle)
                draw.line([x_coord, y_coord, next_coord[0], next_coord[1]], fill="white", width=1)

        #return np.asarray([np.asarray(image).reshape((26, 26, 1))])
        return np.array(image).reshape(1, 26, 26, 1)/255

    def scale_traces(self, trace, resolution=1):

        trace = np.array(trace)

        traceX = trace[:, 0]
        traceY = trace[:, 1]

        max_x = np.max(traceX)
        min_x = np.min(traceX)
        max_y = np.max(traceY)
        min_y = np.min(traceY)

        width = max_x - min_x
        height = max_y - min_y
        scale = width / height

        width_scale = 0
        height_scale = 0

        if scale > 1:
            # width > height
            height_scale = resolution / scale
        else:
            # width < height
            width_scale = resolution * scale

        side = (resolution - width_scale) / 2

        if width_scale > 0:
            # add padding in x-direction

            trace[:,1] = self.scale_linear_bycolumn(trace[:,1], high=resolution, low=-resolution, ma=max_y, mi=min_y)
            side = (resolution - width_scale) / 2
            trace[:,0] = self.scale_linear_bycolumn(trace[:,0], high=(resolution - side), low=(-resolution + side), ma=max_x, mi=min_x)
        else:

            # add padding in y-direction
            trace[:,0] = self.scale_linear_bycolumn(trace[:,0], high=resolution, low=-resolution, ma=max_x,
                                            mi=min_x) 
            side = (resolution - height_scale) / 2
            trace[:,1] = self.scale_linear_bycolumn(trace[:,1], high=(resolution - side), low=(-resolution +side), ma=max_y,
                                            mi=min_y) 

        return trace

    def combine_segment(self, traces):
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
        traces_after_rdp = []

        for trace in traces:
            #print("Len before", len(trace))
            rdp_ed = rdp_fixed_num(np.array(trace), 40)
            #print("Len after", len(rdp_ed))
            traces_after_rdp.append(rdp_ed)
            #traces_after_rdp.append(rdp_fixed_num(trace, ))

        return traces_after_rdp


    def to_distance_between(self, traces):
        traces[1:, 0:0] = traces[1:, 0:1] - traces[0:-1, 0:1]
        traces = traces[1:, :]
        traces[:, 1] = traces[:,2]
        traces = traces[:, 0:2]
        return traces

    def create_sequence(self, traces): 
        processed = self.run_rdp_on_traces(traces)
        
        processed = self.combine_segment(processed)

        processed = self.scale_traces(np.array(processed, dtype="float32"))


        return sequence.pad_sequences([processed], dtype='float32', maxlen=40)

def main():
    s1 = Segment(0, '1')
    s2 = Segment(1, '+')
    s3 = Segment(2, '2')

    sg1 = Segmentgroup(3, 3.4, [s1, s2, s3])

    f1 = Fraction(4, 2.4, [sg1], [s3])
    f2 = Fraction(4, 2.4, [f1], [s3])
    
    print(f2.to_latex())


    
    pass

if __name__ == '__main__':
    main()
