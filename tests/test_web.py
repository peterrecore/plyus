import unittest
import logging
from plyus import app


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_empty(self):
        rv = self.app.get('/')

    def test_list_games(self):
        rv = self.app.get('/games')
        assert rv.status_code == 200
        logging.warn("just did games")