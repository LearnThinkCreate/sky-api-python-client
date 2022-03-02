from authlib.integrations.requests_client import OAuth2Session
from typing import Union


class BaseRequest:

    def __init__(
        self,
        client: OAuth2Session,
        url: str,    
        header: dict,
        params: Union[dict, None] = None,
        data: Union[dict, None] = None
        ):
        self.client = client
        self.url = url
        self.header = header
        self.params = params
        self.data = data

    def getData(self):
        pass

    def cleanData(self):
        pass

    def updateToken(self, cache_token):
        self.client.token['client_id'] = cache_token['client_id']
        self.client.token['client_secret'] = cache_token['client_secret']
        if self.client.token != cache_token:
            return self.client.token
        return cache_token


class GetRequest(BaseRequest):

    def getData(self):
        raw = self.client.get(
            self.url, 
            headers = self.header, 
            params=self.params
            )
        return raw.json()

    def cleanData(self):
        pass


class PostRequest(BaseRequest):

    def getData(self):
        self.header['Content-Type'] = 'application/json'
        raw = self.client.post(
                    self.url, 
                    headers = self.header, 
                    json=self.data
                )
        return raw


class PatchRequest(BaseRequest):

    def getData(self, **kwargs):
        self.header['Content-Type'] = 'application/json'
        raw = self.client.patch(
            self.url, 
            headers = self.header, 
            params=None,
            data=None,
            json=self.data
        )
        return raw

  
class DeleteRequest(BaseRequest):

    def getData(self, **kwargs):
        raw = self.client.delete(
            self.url, 
            headers=self.header, 
            params=self.params, 
            body=self.data, 
            **kwargs
        )
        return raw.text