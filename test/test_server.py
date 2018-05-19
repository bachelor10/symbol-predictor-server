import os
import json
import sys
import unittest
import urllib

from tornado.testing import AsyncHTTPTestCase

import server  # to import run from parent directory or make a package of root directory

from tornado import testing
from tornado import gen
from tornado import web

# https://stackoverflow.com/questions/4060221/how-to-reliably-open-a-file-in-the-same-directory-as-a-python-script
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


# python3 -m unittest -v test.testserver

class TestServerBoot(AsyncHTTPTestCase):

    # Must be overridden 
    def get_app(self):
        return server.app

    def test_get_index(self):
        res = self.fetch('/')
        self.assertEqual(res.code, 200)

    def test_get_static_js(self):
        res = self.fetch('/index.js')
        self.assertEqual(res.code, 200)

    def test_get_static_css(self):
        res = self.fetch('/style.css')
        self.assertEqual(res.code, 200)

    def test_get_static_html(self):
        res = self.fetch('/index.html')
        self.assertEqual(res.code, 200)


# http://www.tornadoweb.org/en/stable/testing.html
# Important to understand that with an async library/server it's necessary to test in an async way
# TLDR, if you experience undefined behaviour, double check the use of yield, self.stop, self.wait()

# class TestServerResponse(AsyncHTTPTestCase):
#     def setUp(self):
#         with open('test/4+3.json', 'r') as readfile:
#             self.data = json.load(readfile)
#
#     # must be overridden
#     def get_app(self):
#         return server.app
#
#
#     def test_post_api(self):
#         pass
#         resp = self.fetch(
#             '/api',
#             method='POST',
#             body=urllib.parse.urlencode(self.data)
#         )
#         print(resp)
#         self.assertEqual(resp.code, 200)
from classification.predictor import Predictor
predictern = Predictor(os.getcwd() + '/classification/combined_model.h5')




class TestBasicBackend(unittest.TestCase):
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
        buffer_correct = [i for i in buffer_array if i != []]
        from classification.expression import Expression
        expression = Expression(self.predictor)
        self.expression = expression
        self.probabilities = expression.feed_traces(buffer_correct, None)


    def setUp(self):
        self.predictor = predictern
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
        self.assertEqual('2^{x}\cdot 5^{7}', latex_data)




if __name__ == '__main__':
    server.test_dir = 'gatherer'
    unittest.main()
