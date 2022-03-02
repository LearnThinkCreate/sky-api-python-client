import pandas as pd
import numpy as np

from unittest import TestCase
from sky import Sky
from dotenv import load_dotenv

# Loading BB_API_Key from .env file
load_dotenv()

client = Sky()

ID = 4738325

class TestGrades(TestCase):

    def test_paginated_response(self):
        raw_data = client.get()
        role_id = raw_data.query("name == 'Parent'")['base_role_id']
        roles = client.get(
            endpoint='users/extended',
            params={'base_role_ids':role_id}
        )   
        self.assertTrue(len(roles) > 1000)

    def test_single_user_response(self):
        user = client.get(f"users/extended/{ID}")
        self.assertTrue(isinstance(user, pd.DataFrame))

    def test_raw_data(self):
        user = client.get(f"users/extended/{ID}", raw_data=True)
        self.assertTrue(user, dict)

    def test_advancedList(self):
        self.assertTrue(isinstance(client.getAdvancedList(73113), pd.DataFrame))

    def test_getLevels(self):
        self.assertTrue(isinstance(client.getLevels(), pd.DataFrame))
        self.assertTrue(isinstance(client.getLevels(id=True), list))

    def test_getOfferingId(self):
        self.assertTrue(isinstance(client.getOfferingId(), list))

    def test_getTerm(self):
        self.assertTrue(isinstance(client.getTerm(), pd.DataFrame))
        self.assertTrue(isinstance(client.getTerm(active=True), list))

    def test_getSections(self):
        self.assertTrue(isinstance(client.getSections(), pd.DataFrame))

    def test_getUsers(self):
        self.assertTrue(isinstance(client.getUsers(), pd.DataFrame))

    def test_multiple_getUsers(self):
        self.assertTrue(isinstance(client.getUsers(['student', 'parent']), pd.DataFrame))