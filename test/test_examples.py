import os, json, sys, unittest

# https://stackoverflow.com/questions/4060221/how-to-reliably-open-a-file-in-the-same-directory-as-a-python-script
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

from classification.predictor import Predictor
predictor = Predictor(os.getcwd() + '/classification/combined_model.h5')

# This class tests some of the algorithms directly used by our server
class TestExampleBuffers(unittest.TestCase):
    def fetch_json_fromfile(self, filename):
        with open(filename, 'r') as readfile:
            self.data = json.load(readfile)
        
        buffer = self.data['buffer']
        buffer_array = []
        
        for i, trace in enumerate(buffer):
            buffer_array.append([])
        
            if trace:
                for coords in trace:
                    buffer_array[i].append([int(coords['x']), int(coords['y'])])
        
        buffer_correct = [i for i in buffer_array if len(i) > 1]
        
        from classification.expression import Expression
        expression = Expression(self.predictor)
        self.expression = expression
        self.probabilities = expression.feed_traces(buffer_correct, None)


    def setUp(self):
        self.predictor = predictor
        self.data = None
        self.expression = None
        self.probabilities = None
        self.fetch_json_fromfile('test/4+3.json')
    
    def test_latex_response_simple(self):
        self.fetch_json_fromfile('test/4+3.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('4+3', latex_data)

    def test_latex_response_fraction(self):
        self.fetch_json_fromfile('test/frac{3_4x}.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('\\frac{3}{4x}', latex_data)

    def test_latex_response_exponents(self):
        self.fetch_json_fromfile('test/exp{2x+57}.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('2^{x}\\cdot 5^{7}', latex_data)

    def test_latex_response_root(self):
        self.fetch_json_fromfile('test/sqrt{2+3}.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('\\sqrt{2+3}', latex_data)
    
    def test_latex_response_recursive_root(self):
        self.fetch_json_fromfile('test/recursive_root.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('\\sqrt{\\sqrt{\\sqrt{2}}}', latex_data)
    
    def test_latex_response_recursive_fraction(self):
        self.fetch_json_fromfile('test/recursive_fraction.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('\\frac{\\frac{\\frac{1}{2}}{3}}{4}', latex_data)

    def test_latex_response_recursive_exp(self):
        self.fetch_json_fromfile('test/recursive_exp.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('2^{2^{2^{\\beta }}}', latex_data)
    
    def test_latex_response_multi_notation(self):
        self.fetch_json_fromfile('test/multi_notation.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('\\frac{\\sqrt{3-2}^{x}}{\\pi -\\sigma \\cdot \\beta }', latex_data)

    def test_latex_response_function(self):
        self.fetch_json_fromfile('test/function.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('f(x)=\\frac{x}{2}', latex_data)

    def test_latex_response_special_symbols(self):
        self.fetch_json_fromfile('test/special_symbols.json')
        latex_data = self.expression.to_latex()
        self.assertEqual('\\beta \\sigma \\pi \\alpha \\infty \\gamma \\mu \\theta ', latex_data)

if __name__ == '__main__':
    unittest.main()
