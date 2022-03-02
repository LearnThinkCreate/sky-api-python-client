import pandas as pd
import pytz


from .auth import AuthApp, OAuth2Token
from authlib.integrations.requests_client import OAuth2Session
from typing import Union
from datetime import datetime

def authorize(func):
    """ Load OAuth2Session

    A :class:`authlib.integrations.requests_client.OAuth2Session ` is needed in order to 
    call the sky api and save api tokens.
    
    loadClient first attempts to load a token from the users cache but if there's no token 
    available it will automatically launch a local web server in order to authenticate you
    with the Sky API
    """    

    def wrap(*args, **kwargs):
        # Assing the sky instance
        skyObject = args[0]
        
        # Chcking if theres a client existant
        if not skyObject.client:
            # Chccking if the user already has a token caced
            if not skyObject._loadCachedToken():
                authorizationApp(skyObject)
            # Initalizing the client class
            skyObject.client = OAuth2Session(
                    token= skyObject.token,
                    client_id = skyObject.token['client_id'],
                    client_secret = skyObject.token['client_secret'],
                    token_endpoint='https://oauth2.sky.blackbaud.com/token',
                    token_endpoint_auth_method='client_secret_basic',
                    preserve_refresh_token=True
                )
            # Updating access token and preserving refresh token
            skyObject.client.refresh_token('https://oauth2.sky.blackbaud.com/token', preserve_refresh_token=True)
        # Running the call function
        return func(*args, **kwargs)
    return wrap


def authorizationApp(skyObject) -> None:
    """Launch server to retrieve Sky API token"""
    # Checking if the user passed in a valid dictionary with their credentials
    if skyObject.credentials and isinstance(skyObject.credentials, dict):
        valid_credentials = (skyObject.credentials.get('client_id') and skyObject.credentials.get('client_secret') and skyObject.credentials.get('redirect_uri'))
        if valid_credentials:
            app = AuthApp.load_credentials(skyObject.credentials)
        else:
            # If the credentials aren't valid then passing in the path to sky_credentials.json
            app = AuthApp.load_credentials(skyObject.file_path)
    else:
        # If the user didn't pass in a dict then passing in the path to sky_credentials.json
        app = AuthApp.load_credentials(skyObject.file_path)
    # Launching a local server
    skyObject.token = app.run_local_server()
    # Saving the new api token
    skyObject._saveToken(skyObject.token)


def cleanAdvancedList(
    data: pd.DataFrame
    ) -> pd.DataFrame:
    """ Cleans data from the legacy/list Sky API endpoint
    Args:
        data: Data returned from calling the legacy/list Sky API endpoint 

    Returns:
        Pandas DataFrame with data from a Core Advanced List        
    """
    # Initializing empty array to store index data
    index = []
    # Number of columns in the data
    ncol = len(data.name.unique())
    # Initializing index value
    num = 0

    for i in range(len(data)):
        if (i % ncol) == 0:
            num += 1
        index.append(num)

    # Setting the index values
    data['index'] = index
    
    # Piviting the data wider
    data = data.pivot(index = "index", columns = "name", values = "value")
    return data


def isActiveTerm(
    data: pd.DataFrame
        ) -> pd.DataFrame:
    """ Takes 

    Args:
        data: pd.DataFrame with two datetime columns named
        'begin_date' & 'end_date' respectfully 

    Returns:
        Orginal DataFrame, but with a 'active' column that represents whether the current date 
        lies within the date range provided in the ['begin_date'. 'end_date'] columns.        
    """
    # Setting time zone
    utc=pytz.UTC
    today = utc.localize(datetime.now()) 
    # Intializing active to be False
    data['active'] = False
    # Checking which terms are active
    for index, row in data.iterrows():
        data.loc[index, 'active'] = (row['begin_date'] <= today <= row['end_date'])
    return data