class UnifiSyncClientException(Exception):
    """UnifiSyncClient exception handler

    :param msg: Exception message
    :type msg: str
    :param response: Request object
    :type: requests object
    """
    def __init__(self, msg = "Unknown UnifiSyncClient Exception", response = None):
        self.msg = msg
        self.response = response

    def __str__(self):
        api_err = None
        if self.response.json().get('meta', {}).get('rc') == 'error':
            if self.response.json().get('meta', {}).get('msg'):
                api_err = self.response.json().get('meta', {}).get('msg')
        return f"UnifiSyncClient Exception msg = '{self.msg}' while accessing url = '{self.response.url}' api_err = '{api_err}'"

class ConnectionError(UnifiSyncClientException):
    def __init__(self, msg = "Connection failed", response = None):
        super().__init__(msg = msg, response = response)

class TimeoutError(UnifiSyncClientException):
    def __init__(self, msg = "Timeout connection took too long to respond", response = None):
        super().__init__(msg = msg, response = response)

class LoginExhausted(UnifiSyncClientException):
    def __init__(self, msg = "Login failed 2FA (exhausted)", response = None):
        super().__init__(msg = msg, response = response)

class LoginFailed(UnifiSyncClientException):
    def __init__(self, msg = "Login failed", response = None):
        super().__init__(msg = msg, response = response)

class HttpError(UnifiSyncClientException):
    def __init__(self, msg = "Api Unknown Error", response = None):
        super().__init__(msg = msg, response = response)

class MacInvalidFormatException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class EmailInvalidFormatException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
