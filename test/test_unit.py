import os, json, sys, unittest

import numpy as np

from classification.expression import Expression
from classification.predictor import Predictor
from classification.preprocessor import Preprocessor
from classification.notation_elements import Group, Segment, Power, Fraction, Root

from classification.fixed_rdp import rdp_fixed_num


class TestLatexGenerator(unittest.TestCase):

    def test_simple_expression(self):
        ex = Expression(None)

        s1 = Segment(1,'2', 'num', [])
        s2 = Segment(2,'+', 'num', [])
        s3 = Segment(3,'2', 'num', [])
        s4 = Segment(4,'=', 'operator', [])
        s5 = Segment(5,'4', 'num', [])

        ex.groups = [s1, s2, s3, s4, s5]
        
        self.assertEqual('2+2=4', ex.to_latex())

    def test_another_simple_expresssion(self):
        ex = Expression(None)
        s1 = Segment(1,'4', 'num', [])
        s2 = Segment(2,'-', 'num', [])
        s3 = Segment(3,'1', 'num', [])
        s4 = Segment(4,'=', 'operator', [])
        s5 = Segment(5,'3', 'num', [])

        ex.groups = [s1, s2, s3, s4, s5]
        
        self.assertEqual('4-1=3', ex.to_latex())

    def test_simple_power(self):
        ex = Expression(None)
        s1 = Segment(1,'4', 'num', [])
        s2 = Segment(2,'2', 'num', [])
        p1 = Power(3, [s1], [s2])

        ex.groups = [p1]
        self.assertEqual('4^{2}', ex.to_latex())
        
    def test_simple_fraction(self):
        ex = Expression(None)
        s1 = Segment(1,'4', 'num', [])
        s2 = Segment(2,'2', 'num', [])
        f1 = Fraction(3, [s1], [s2], [])

        ex.groups = [f1]
        self.assertEqual('\\frac{4}{2}', ex.to_latex())

    def test_simple_root(self):
        ex = Expression(None)
        s1 = Segment(2,'3', 'num', [])
        r1 = Root(3, [s1], [])

        ex.groups = [r1]
        self.assertEqual('\\sqrt{3}', ex.to_latex())
        pass

    def test_simple_multigroup(self):
        ex = Expression(None)
        s1 = Segment(1,'5', 'num', [])
        r1 = Root(2, [s1], [])

        s2 = Segment(3,'2', 'num', [])
        s3 = Segment(4,'2', 'num', [])
        p1 = Power(5, [s2], [s3])

        f1 = Fraction(6, [r1], [p1], [])

        ex.groups = [f1]
        self.assertEqual('\\frac{\\sqrt{5}}{2^{2}}', ex.to_latex())

    def test_advanced_multigroup(self):
        ex = Expression(None)
        s1 = Segment(1,'3', 'num', [])
        s2 = Segment(2,'+', 'operator', [])
        s3 = Segment(3,'2', 'num', [])
        r1 = Root(4, [s1, s2, s3], [])

        s4 = Segment(5,'5', 'num', [])
        s5 = Segment(6,'3', 'num', [])
        s6 = Segment(7,'-', 'operator', [])
        s7 = Segment(8,'2', 'num', [])
        f1 = Fraction(9, [s4], [s5, s6, s7], [])
        f2 = Fraction(10, [r1], [f1], [])

        s8 = Segment(11,'+', 'operator', [])
        s9 = Segment(12,'3', 'num', [])
        s10 = Segment(13,'x', 'var', [])
        s11 = Segment(14,'2', 'num', [])
        f1 = Fraction(6, [s10], [s11], [])
        p1 = Power(5, [s9], [f1])

        ex.groups = [f2, s8, p1]
        self.assertEqual('\\frac{\\sqrt{3+2}}{\\frac{5}{3-2}}+3^{\\frac{x}{2}}', ex.to_latex())

    def test_recursive_fraction(self):
        ex = Expression(None)
        s1 = Segment(1,'1', 'num', [])
        s2 = Segment(2,'2', 'num', [])
        s3 = Segment(3,'3', 'num', [])
        s4 = Segment(4,'4', 'num', [])
        f1 = Fraction(5, [s1], [s2], [])
        f2 = Fraction(6, [f1], [s3], [])
        f3 = Fraction(7, [f2], [s4], [])

        ex.groups = [f3]
        self.assertEqual('\\frac{\\frac{\\frac{1}{2}}{3}}{4}', ex.to_latex())

    def test_recursive_exponent(self):
        ex = Expression(None)
        s1 = Segment(1,'2', 'num', [])
        s2 = Segment(2,'2', 'num', [])
        s3 = Segment(3,'2', 'num', [])
        s4 = Segment(4,'x', 'num', [])
        p1 = Power(5, [s3], [s4])
        p2 = Power(6, [s2], [p1])
        p3 = Power(7, [s1], [p2])

        ex.groups = [p3]
        self.assertEqual('2^{2^{2^{x}}}', ex.to_latex())

    def test_recursive_root(self):
        ex = Expression(None)
        s1 = Segment(1,'3', 'num', [])
        r1 = Root(2, [s1], [])
        r2 = Root(3, [r1], [])
        r3 = Root(4, [r2], [])

        ex.groups = [r3]
        self.assertEqual('\\sqrt{\\sqrt{\\sqrt{3}}}', ex.to_latex())


class TestPredictor(unittest.TestCase):

    def test_scale_linear_bycolumn(self):
        values = np.array([1,2,3]).astype(np.float)
        new_values = Predictor.scale_linear_bycolumn(Predictor, rawpoints=values, high=20, low=0, ma=3, mi=1)
        
        self.assertEqual(new_values[0], 0)
        self.assertEqual(new_values[1], 10)
        self.assertEqual(new_values[2], 20)

    def test_combine_segment(self):
        traces = [[(0,0),(1,1),(2,2)],[(3,3),(4,4),(5,5)],[(6,6),(7,7),(8,8)]]
        new_trace = Predictor.combine_segment(Predictor, traces)

        self.assertEqual(len(new_trace), 9)

class TestPreprocessor(unittest.TestCase):

    def test_find_single_trace_distances(self):
        trace = [(0,0),(4,0),(4,6),(2,3)]
        distances = Preprocessor.find_single_trace_distances(Preprocessor, trace)
        
        self.assertEqual(distances[0], 4)
        self.assertEqual(distances[1], 6)
        self.assertEqual(distances[2], 3.605551275463989)

    def test_create_tracegroups(self):
        traces = [0,1,2,3,4,5,6,7,8]
        trace_pairs = [(1,2),(2,4),(3,5),(8,7)]

        trace_groups = Preprocessor.create_tracegroups(Preprocessor, traces, trace_pairs)

        self.assertEqual(trace_groups[0], [0])
        self.assertEqual(trace_groups[1], [1, 2, 4])
        self.assertEqual(trace_groups[2], [3, 5])
        self.assertEqual(trace_groups[3], [6])
        self.assertEqual(trace_groups[4], [8, 7])

class TestRamerDouglasPeuckerAlgorithm(unittest.TestCase):
    def populate_traces(self,filename):
        with open(filename, 'r') as readfile:
            self.data = json.load(readfile)
        
        buffer = self.data['buffer']
        buffer_array = []
        
        for i, trace in enumerate(buffer):
            buffer_array.append([])
        
            if trace:
                for coords in trace:
                    buffer_array[i].append([int(coords['x']), int(coords['y'])])
        
        self.buffer_correct = [i for i in buffer_array if i != []]


    def setUp(self):
        self.populate_traces("test/4+3.json")

    def test_rdp_fixed_num(self):
        #print(self.buffer_correct[0])

        actual_0 = rdp_fixed_num(np.array(self.buffer_correct[0]),30)
        actual_1 = rdp_fixed_num(np.array(self.buffer_correct[1]),10)

        self.assertEqual(30,len(actual_0))
        self.assertEqual(10,len(actual_1))


if __name__ == '__main__':
    unittest.main()
