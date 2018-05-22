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


if __name__ == '__main__':
    server.test_dir = 'gatherer'
    unittest.main()
