from itertools import combinations
import numpy as np
from .boundingbox import Boundingbox
from .notation_elements import Segment, Group, Fraction, Root, Power
from .preprocessor import Preprocessor
from .predictor import Predictor

class Expression:

    def __init__(self, predictor):
        self.segments = []
        self.groups = []
        self.predictor = predictor
        self.preprocessor = Preprocessor()


    def feed_traces(self, traces, truth):
        """
        The main input function.
        """

        # Find the overlapping traces
        overlap_pairs = self.preprocessor.find_overlap_pairs(traces)

        # Create groups of traces, each group represents a symbol
        tracegroups = self.preprocessor.create_tracegroups(traces, overlap_pairs)
        
        probabilities = []

        # Iterate over the symbols
        for i, group in enumerate(tracegroups):
            # find the correct traces for 
            segment_traces = [traces[j] for j in list(group)]
            id = str(i)

            # Predict the probabilites for the symbol
            predicted_truth, proba, predicted_type = self.predictor.predict(segment_traces, truth)

            # Probabilities to be returned
            proba['tracegroup'] = group
            probabilities.append(proba)

            # Create segment object to use in context search
            segment = Segment(id, predicted_truth, predicted_type, segment_traces)
            self.segments.append(segment)

        # Search for context
        self.groups = self.recursive_search_for_context(self.segments, 10000, 0, 10000, 0)

        return probabilities


    def recursive_search_for_context(self, objects, max_x, min_x, max_y, min_y):
        """
        Finds the context for objects within an area.
        """
        
        objects = self.find_roots(objects)
        objects = self.find_fractions(objects, max_x, min_x, max_y, min_y)
        objects = self.find_equalsigns(objects)
        objects = self.find_multiplicationsigns(objects)
        objects = self.sort_objects_by_x_value(objects)
        objects = self.find_exponents(objects, max_x, min_x, max_y, min_y)
        objects = self.sort_objects_by_x_value(objects)

        return objects


    def find_objects_in_area(self, max_x, min_x, max_y, min_y, objects):
        """
        Find segments and groups in specified area.
        Searches for middle values (mid_x, mid_y).

        Format:
         
        min_x, min_y ---------------
        |                          |
        |                          |
        ----------------max_x, max_y
        
        Returns a list of objects found.
        """
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
                # Create empty root object if objects was found within the bounds
                root_obj = Root(root.id, [], root.traces)
                objects.append(root_obj)

        return objects


    def check_if_fraction(self, minus_sign, objects, max_y, min_y):
        
        max_x = minus_sign.boundingbox.max_x
        min_x = minus_sign.boundingbox.min_x
        
        # Find the minus signs
        minus_signs = [obj for obj in objects if obj.truth == '-']

        # Find numerator and denominator
        numerator = self.find_objects_in_area(max_x, min_x, minus_sign.boundingbox.mid_y - 1, min_y, objects)
        denominator = self.find_objects_in_area(max_x, min_x, max_y, minus_sign.boundingbox.mid_y + 1, objects)

        # Return true if two or more objects is found in either numerator or denominator
        if len(numerator) > 1 or len(denominator) > 1:
            return True, numerator, denominator
        
        # Return true if one or more objects is found in one of them, and there is only one minus sign
        if len(numerator) > 0 or len(denominator) > 0:
            if len(minus_signs) == 1:
                return True, numerator, denominator
        
        Return true 
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

        # Iterate through each combination of minus sign pair
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
        
        # Find area of the object
        obj_area = object.boundingbox.width * object.boundingbox.height

        # Check if the area is withing the threshold
        if obj_area > 250:
            return False
        
        # Check if height and width is within the thresholds
        if object.boundingbox.height > 20 or object.boundingbox.width > 20:
            return False

        # Return true if the area is very small
        if obj_area < 51:
            return True

        # Check if the height and widt is similar
        if object.boundingbox.width >= 2 * object.boundingbox.height:
            return False

        if object.boundingbox.height >= 2 * object.boundingbox.width:
            return False

        return True


    def find_multiplicationsigns(self, objects):
        
        if len(objects) == 0:
            return objects

        area = 0

        # Find the average size of objects by area, is currently not used
        for obj in objects:
            area += obj.boundingbox.width * obj.boundingbox.height

        avg_area = area / len(objects)

        # Iterate through the object and check if it is a multiplication sign
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

        # Iterate through all the groups and find the corresponding latex script
        for group in self.groups:
            latex += group.to_latex()
            
        return latex
