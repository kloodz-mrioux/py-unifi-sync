########################################
# ApiErrorException
########################################
class ApiErrorException(Exception):
    """Base exception class for API-related errors."""
    pass


class ApiErrorNoPermission(ApiErrorException):
    """Exception raised when permission is denied."""
    def __init__(self, message="Api Error Permission denied"):
        self.message = message
        super().__init__(self.message)


class ApiErrorInvalidObject(ApiErrorException):
    """Exception raised on invalid object"""
    def __init__(self, message="Api Error Invalid Object"):
        self.message = message
        super().__init__(self.message)


class ApiErrorLoginRequired(ApiErrorException):
    """Exception raised on login required"""
    def __init__(self, message="Api Error Login Required"):
        self.message = message
        super().__init__(self.message)


class ApiErrorNoDelete(ApiErrorException):
    """Exception raised on undeletable object"""
    def __init__(self, message="Api Error Undeletable Object"):
        self.message = message
        super().__init__(self.message)


class ApiErrorIdInvalid(ApiErrorException):
    """Exception raised on invalid id"""
    def __init__(self, message="Api Error Ivalid Id"):
        self.message = message
        super().__init__(self.message)


########################################
# UnifiSyncClientException
########################################
class UnifiSyncClientException(Exception):
    """UnifiSyncClient exception handler

    :param msg: Exception message
    :type msg: str
    :param response: Request object
    :type: requests object
    """
    def __init__(self, msg="Unknown UnifiSyncClient Exception", response=None):
        self.msg = msg
        self.response = response

    def __str__(self):
        api_err = None
        if self.response.json().get('meta', {}).get('rc') == 'error':
            if self.response.json().get('meta', {}).get('msg'):
                api_err = self.response.json().get('meta', {}).get('msg')
        return f"UnifiSyncClient Exception msg = '{self.msg}' url = '{self.response.url}' api_err = '{api_err}'"


class ConnectionError(UnifiSyncClientException):
    def __init__(self, msg="Connection failed", response=None):
        super().__init__(msg=msg, response=response)


class TimeoutError(UnifiSyncClientException):
    def __init__(self, msg="Timeout connection took too long to respond", response=None):
        super().__init__(msg=msg, response=response)


class LoginExhausted(UnifiSyncClientException):
    def __init__(self, msg="Login failed 2FA (exhausted)", response=None):
        super().__init__(msg=msg, response=response)


class LoginFailed(UnifiSyncClientException):
    def __init__(self, msg="Login failed", response=None):
        super().__init__(msg=msg, response=response)


class HttpError(UnifiSyncClientException):
    def __init__(self, msg="Api Unknown Error", response=None):
        super().__init__(msg=msg, response=response)


########################################
# Custom Exception
########################################
class MacInvalidFormatException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class EmailInvalidFormatException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
