import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AutoMethod:
    """AutoMethod provides methods to manage callback used in unifi-sync client
    """
    def __init__(self):
        self._am_callback = {}

    def is_method(self, method_name: str) -> bool:
        """
        Validate if method_name is present in dictionary

        :param method_name: method name.
        :type method_name: str
        :returns: True if method is defined
        :rtype: bool
        """
        if method_name:
            if method_name in self._am_callback.keys():
                return True
        return False

    def list_method(self, method_name: Optional[str] = '') -> dict[str, str]:
        """
        Get dictionary for method_name or all methods

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: Optional str
        :returns: dictionary
        :rtype: dict[str,str]
        """
        if method_name:
            if method_name in self._am_callback.keys():
                return self._am_callback[method_name]
        else:
            return self._am_callback

    def add_method(self, method_name: str, request_method: str, urlpath:
                   str, argv: Optional[str] = '', dargv: Optional[str] = '') -> bool:
        """
        Add method_name callback in dictionary

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :param request_method: request object method: GET, OPTIONS, HEAD, POST, PUT, PATCH, or DELETE
        :type request_method: str
        :param urlpath: path name (will be automatically prefixed with baseurl)
        :type urlpath: str
        :param argv: argument passed to method_name (this value will be evaluated and contatenate to urlpath at runtime)
        :type argv: Optional str
        :param dargv: default argument value
        :type dargv: Optional str
        :returns: True if method is added
        :rtype: bool
        """
        if request_method not in ['GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE']:
            logger.error(f"request {request_method} not a valid requests object supported methods")
            return False
        if not re.match('^/.*', urlpath):
            logger.error(f"urlpath should start with / method:{method_name} urlpath:{urlpath}")
            return False
        if method_name in self._am_callback.keys() and '_alias' in self._am_callback.get(method_name).keys():
            logger.error(f"Can't update method {method_name} it's an alias {self._am_callback[method_name]['_alias']}")
            return False
        self._am_callback.update({method_name: {'_request': request_method,
                                                '_urlpath': urlpath, '_argv': argv, '_dargv': dargv}})
        return True

    def add_method_alias(self, method_name: str, alias_method_name: str) -> bool:
        """
        Add method_name callback alias in dictionary

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :param alias_method_name: alias method name will become a callable from parent class from __getattr__
        :type alias_method_name: str
        :returns: True if alias method is added
        :rtype: bool
        """
        if method_name and alias_method_name:
            if method_name in self._am_callback.keys() and alias_method_name not in self._am_callback.keys():
                self._am_callback[alias_method_name] = self._am_callback.get(method_name).copy()
                self._am_callback[alias_method_name]['_alias'] = method_name
                return True
        return False

    def get_method(self, method_name: str) -> dict[str, str]:
        """
        Get callback dictionary from method_name

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :returns: dictionary for method_name
        :rtype: dict
        """
        if self.is_method(method_name):
            return self._am_callback[method_name]

    def get_method_request(self, method_name: str) -> str:
        """
        Get request using method_name from dictionary

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :returns: request
        :rtype: str
        """
        if self.is_method(method_name):
            return self._am_callback[method_name]['_request']

    def get_method_urlpath(self, method_name: str) -> str:
        """
        Get urlpath using method_name from dictionary

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :returns: urlpath
        :rtype: str
        """
        if self.is_method(method_name):
            return self._am_callback[method_name]['_urlpath']

    def get_method_argv(self, method_name: str) -> str:
        """
        Get argv using method_name from dictionary

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :returns: argv
        :rtype: str
        """
        if self.is_method(method_name):
            if '_argv' in self._am_callback[method_name]:
                return self._am_callback[method_name]['_argv']

    def get_method_dargv(self, method_name: str) -> str:
        """
        Get dargv using method_name from dictionary

        :param method_name: method name which will become a public callable in the parent class from __getattr__
        :type method_name: str
        :returns: dargv
        :rtype: str
        """
        if self.is_method(method_name):
            if '_dargv' in self._am_callback[method_name]:
                return self._am_callback[method_name]['_dargv']
