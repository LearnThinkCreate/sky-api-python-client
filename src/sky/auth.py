import webbrowser
import wsgiref.simple_server
import wsgiref.util
import logging
import json
import urllib.parse as urlparse

from typing import Union, Iterable, Type, TypeVar, Generic, Tuple, Mapping, Callable, Any
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749.wrappers import OAuth2Token
from os.path import exists

from numpy import isin

_LOGGER = logging.getLogger(__name__)

Flow = TypeVar('Flow')

class AuthApp(Generic[Flow]):
    AUTHORIZATION_URL='https://oauth2.sky.blackbaud.com/authorization'


    def __init__(
        self,
        client: OAuth2Session,
        host: Union[str, int],
        port: int,
        client_id: str,
        client_secret: str
        ):
        """OAuth 2.0 Authorization App

        Here's an example of using :class:`AuthApp`::

        from funky.auth import AuthApp

        # Create the flow using the sky credentials file from the with 
        # client_id, client_secret, and redirect URI from your BlackBaud Sky api app
        app = AuthApp.load_credentials("path/to/sky_credentials.json")
        sky_token = app.run_local_server()
        """
        self.client = client
        self.host = host
        self.port = port
        self.client_id = client_id
        self.client_secret = client_secret
        
    @classmethod
    def load_credentials(
        cls, 
        sky_credentials: str
        ) -> Type[Flow]:
        """Creates a :class:`Flow` instance from a sky_credentials file.

        Args:
            sky_credentials: The path to the sky credentials .json file.
            kwargs: Any additional parameters passed to
                :class:`authlib.integrations.requests_client.OAuth2Session`

        Returns:
            Flow: The constructed Flow instance.
        """
        if isinstance(sky_credentials, dict):
            credentials = sky_credentials
        elif isinstance(sky_credentials, str):
            with open(sky_credentials, "r") as json_file:
                credentials = json.load(json_file)
        else:
            raise Exception("Invalid credentials")
        # Parsing the url for the host and port
        url = urlparse.urlparse(credentials['redirect_uri'])
        host = url.hostname
        port = url.port
        clientID= credentials['client_id']
        clientSecret = credentials['client_secret']

        client = OAuth2Session(
            client_id = clientID,
            client_secret = clientSecret,
            redirect_uri = credentials['redirect_uri'],
            token_endpoint='https://oauth2.sky.blackbaud.com/token',
            authorization_endpoint='https://oauth2.sky.blackbaud.com/authorization',
            token_endpoint_auth_method='client_secret_basic'
        )
        
        return cls(
            client,
            host,
            port,
            clientID,
            clientSecret
        )
    

    def run_local_server(
        self
        ) -> OAuth2Token:
        """Perform authorization flow using local server

        It will start a local web server to listen for the authorization
        response. Once authorization is complete the authorization server will
        redirect the user's browser to the local web server. The web server
        will get the authorization code from the response and shutdown. The
        code is then exchanged for a token.

        Returns:
            class:`authlib.oauth2.rfc6749.wrappers.OAuth2Token`

        """
        wsgi_app = _RedirectWSGIApp("You may close the browser now")
        local_server = wsgiref.simple_server.make_server(
            self.host, self.port, wsgi_app, handler_class=_WSGIRequestHandler
        )

        url, _ = self.authorization_url()

        webbrowser.open(url, new=1, autoraise=True)

        local_server.handle_request()

        # OAuth 2.0 should only occur over https.
        authorization_response = wsgi_app.last_request_uri.replace("http", "https")
        token = self.fetch_token(authorization_response=authorization_response)
        token['client_id'] = self.client_id
        token['client_secret']  = self.client_secret
        return token
    

    def authorization_url(self) -> Tuple[str, str]:
        """Generates an authorization URL

        This is the first step in the OAuth 2.0 Authorization Flow. The user's
        browser should be redirected to the returned URL.

        This method calls
        :meth:`authlib.integrations.requests_client.OAuth2Session.create_authorization_url`
        and specifies the client configuration's authorization URI. This is required in order to 
        obtain a refresh token.
        """
        return self.client.create_authorization_url(self.AUTHORIZATION_URL)


    def fetch_token(self, **kwargs) -> OAuth2Token:
        """Completes the Authorization Flow and obtains an access token.

        This is the final step in the OAuth 2.0 Authorization Flow. This is
        called after the user consents.

        Args:
        kwargs: Arguments passed through to
            :meth:`authlib.integrations.requests_client.OAuth2Session.fetch_token`. 
            client secret must be specified
        This method calls
        :meth:`authlib.integrations.requests_client.OAuth2Session.fetch_token`
        and specifies the client configuration's token URI
        """
        kwargs.setdefault("client_secret", self.client.client_secret)
        return self.client.fetch_token(self.client.metadata['token_endpoint'], **kwargs)
    
    
class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    """Custom WSGIRequestHandler.

    Uses a named logger instead of printing to stderr.
    """

    def log_message(self, format, *args):
        # pylint: disable=redefined-builtin
        # (format is the argument name defined in the superclass.)
        _LOGGER.info(format, *args)


class _RedirectWSGIApp(object):
    """WSGI app to handle the authorization redirect.

    Stores the request URI and displays the given success message.
    """
    def __init__(self, success_message):
        """
        Args:
            success_message (str): The message to display in the web browser
                the authorization flow is complete.
        """
        self.last_request_uri = None
        self._success_message = success_message

    def __call__(
        self, 
        environ: Mapping[str, Any], 
        start_response: Callable[[], str]
        ) -> Iterable[bytes]:
        """WSGI Callable.

        Args:
            environ (Mapping[str, Any]): The WSGI environment.
            start_response (Callable[str, list]): The WSGI start_response
                callable.

        Returns:
            Iterable[bytes]: The response body.
        """
        start_response("200 OK", [("Content-type", "text/plain")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]