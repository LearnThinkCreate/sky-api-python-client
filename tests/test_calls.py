import os

from unittest import TestCase
from sky import Sky
from dotenv import load_dotenv

# Loading BB_API_Key from .env file
load_dotenv()

client = Sky(
    credentials={
    "client_id":os.getenv('CLIENT_ID'),
    "client_secret":os.getenv('CLIENT_SECRET'),
    "redirect_uri":os.getenv('REDIRECT_URI'),
    })

ID = None

class TestAuth(TestCase):
    
    def test_get(self):
        data = client.get()
        self.assertIsNotNone(data)

    def test_post_patch(self):

        data = client.post(data = {
            "first_name": "API",
            "last_name": "User"
        })
        ID=int(data.text)
        self.assertIsInstance(ID, int)
        
        data = client.patch(data={
            "id": ID,
            "last_name": "NewUser"
        })

        self.assertEqual(data.status_code, 200)

        