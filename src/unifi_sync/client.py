import requests
import urllib3
import re
import time
import logging
import uuid
import json
from typing import Optional
from datetime import datetime, timezone
from .automethod import AutoMethod


class api_exception:
    from .exception import (
        ApiErrorException,
        ApiErrorInvalidObject,
        ApiErrorNoPermission,
        ApiErrorLoginRequired,
        ApiErrorNoDelete,
        ApiErrorIdInvalid,
        HttpError,
        LoginExhausted,
        LoginFailed,
        EmailInvalidFormatException,
        MacInvalidFormatException,
    )


logging.basicConfig()
logger = logging.getLogger(__name__)


class UnifiSyncClient:
    """This class provides methods to authenticate with a UniFi Controller,
    retrieve device information, and manage multiple settings synchronously.

    :param username: The admin username for the UniFi Controller. Defaults to ubnt
    :type username: Optional str
    :param password: The admin password for the UniFi Controller. Defaults to ubnt
    :type password: Optional str
    :param base_url: The url of the UniFi Controller. Defaults to https://localhost:8443
    :type base_url: Optional str
    :param site_name: The site name on the UniFi Controller. Defaults to default
    :type site_name: Optional str
    :param verify_ssl: Whether to verify the SSL certificate. Defaults to False
    :type verify_ssl: Optional bool
    """

    from .__version__ import (
        __author__,
        __author_email__,
        __copyright__,
        __description__,
        __license__,
        __title__,
        __url__,
        __version__,
        __git_project__,
        __git_repo__,
        __git_reponame__,
        __git_repouser__,
    )

    def __init__(
        self,
        username: Optional[str] = "ubnt",
        password: Optional[str] = "ubnt",
        baseurl: Optional[str] = "https://localhost:8443",
        site_name: Optional[str] = "default",
        ssl_verify: Optional[bool] = False,
    ):

        self.username = username.strip()
        self.password = password.strip()
        self.baseurl = baseurl.strip()
        self.site = site_name.lower().strip()
        self.ssl_verify = ssl_verify

        # WARNING: disable exceptions from requests if ssl validation is disable
        if not ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.authurl_login = self.baseurl + "/api/login"
        self.authurl_logout = self.baseurl + "/api/logout"
        self.authurl_twofa = self.baseurl + "/api/login"
        self.authurl_twofaself = self.baseurl + "/api/self"
        self.referer_twofa = self.baseurl + "/manage/account/login/2fa"
        self.ui_ssourl_login = "https://sso.ui.com/api/sso/v1/login"
        self.ui_ssourl_mfa = (
            "https://sso.ui.com/api/sso/v1/user/self/mfa/push/poll-login"
        )
        self.ui_ssourl_device = "https://sso.ui.com/api/sso/v1/user/self/device"
        self.ui_ssourl_token = "https://sso.ui.com/api/sso/v1/jwt/token"
        self.ui_device_id = str(uuid.uuid1())
        self.headers = {}
        self.cookies = {}
        self.mfa_wait = 5
        self.mfa_retry = 12
        self.is_mfa_login = False

        self.session = requests.Session()
        self.cb = AutoMethod()
        self._init_callback_method()

        self.reshape_str = (
            '{"meta": {"rc": "ok", "unifi-sync-msg": "data reshape"}, "data": []}'
        )

        self.default_site_stats_attributes = [
            "bytes",
            "wan-tx_bytes",
            "wan-rx_bytes",
            "wlan_bytes",
            "num_sta",
            "lan-num_sta",
            "wlan-num_sta",
            "time",
        ]

        self.default_group_type_attributes = [
            "address-group",
            "ipv6-address-group",
            "port-group",
        ]

    def __getattr__(self, method_name: str):
        if self.cb.is_method(method_name):

            def __automatic_method(*args):
                logger.debug(f"AM  method = {method_name}")
                logger.debug(f"AM request = {self.cb.get_method_request(method_name)}")
                logger.debug(f"AM urlpath = {self.cb.get_method_urlpath(method_name)}")
                url_path = eval(f'f"""{self.cb.get_method_urlpath(method_name)}"""')
                if args:
                    url_path += eval(f'f"""{self.cb.get_method_argv(method_name)}"""')
                    logger.debug(
                        f"AM  method = {method_name} args = {list(args)} url_path(eval) = {url_path}"
                    )
                elif self.cb.get_method_dargv(method_name):
                    url_path += eval(f'f"""{self.cb.get_method_dargv(method_name)}"""')
                    logger.debug(
                        f"AM  method = {method_name} args = {list(args)} url_path(eval) = {url_path} (default value)"
                    )
                if self.cb.get_method_request(method_name) in ["DELETE"]:
                    return self._request_results_boolean(
                        self.cb.get_method_request(method_name), url_path
                    )
                else:
                    return self._request_results(
                        self.cb.get_method_request(method_name), url_path
                    )

            return __automatic_method
        else:
            logger.error(f"AM  method = {method_name} does not exist")

    def _request_results(
        self, method: str, url_path: str, payload: dict[str, str] = dict()
    ):
        try:
            logger.debug(f"RR   method = {method}")
            logger.debug(f"RR url_path = {url_path}")
            logger.debug(f"RR  payload = {payload}")
            logger.debug(f"RR   header = {self.headers}")
            logger.debug(f"RR   cookie = {self.cookies}")

            self.session.verify = self.ssl_verify

            response = self.session.request(
                method,
                f"{self.baseurl}{url_path}",
                json=payload,
                headers=self.headers,
                cookies=self.cookies,
            )
            response_json = response.json()

            logger.debug(f"RR  response(j) = {response_json}")
            logger.debug(f"RR  response(h) = {response.headers}")
            logger.debug(f"RR  response(c) = {response.cookies}")

            # DEBUG response.raise_for_status()
            if re.match("^/v2/api/", url_path):
                if response.status_code == 200:
                    reshape = json.loads(self.reshape_str)
                    reshape.update({"data": response_json})
                    logger.debug(f"RR  reshape = {reshape}")
                    return reshape
                else:
                    raise api_exception.HttpError("API V2 response error", response)

            if response_json.get("meta", {}).get("rc") == "ok":
                return response.json()

            if response_json.get("meta", {}).get("rc") == "error":
                try:
                    if response_json.get("meta", {}).get("msg"):
                        err_name = response_json.get("meta", {}).get("msg")
                        exception_name = f"ApiError{err_name.split('.')[-1]}"

                        exception_class = getattr(api_exception, exception_name, None)
                        if exception_class is not None and issubclass(
                            exception_class, api_exception.ApiErrorException
                        ):
                            logger.debug(
                                f"RR   exception_name = {exception_name} exception_class {exception_class}"
                            )
                            raise exception_class()
                        else:
                            raise Exception(
                                f"Unknow ApiError exception {err_name} {exception_name}. DEV: add this exception.py"
                            )
                    else:
                        raise api_exception.HttpError("API V1 response error", response)
                except api_exception.ApiErrorInvalidObject:
                    return response.json()
                # except api_exception.ApiErrorNoPermission:
                #    return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise Exception(f"_request_results - HTTP error occurred: {http_err}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"_request_results - Unknown error occurred: {e}")

    def _request_results_boolean(
        self, method: str, url_path: str, payload: dict[str, str] = dict()
    ) -> bool:
        response = self._request_results(method, url_path, payload)
        return response.get("meta", {}).get("rc") == "ok"

    def _request_results_boolean_tuple(
        self, method: str, url_path: str, payload: dict[str, str] = dict()
    ) -> tuple:
        response = self._request_results(method, url_path, payload)
        if response.get("meta", {}).get("rc") == "ok":
            return (True, response)
        return (False, response)

    def _unifi_update_cookies_headers(self, response):
        for e in ["unifises", "csrf_token"]:
            if e in response.cookies:
                self.cookies.update({e: response.cookies[e]})
                logger.debug(f"_UUCH C({e}) = {response.cookies[e]}")

                if e == "csrf_token":
                    self.headers.update({"X-Csrf-token": response.cookies[e]})
                    logger.debug(f"_UUCH H(X-Csrf-token) = {response.cookies[e]}")

    def _validate_mac(self, mac: str) -> bool:
        mac = mac.lower().strip()
        if re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac):
            return True, mac
        return False, mac

    def _get_valid_macs(self, macs: list) -> list:
        vmacs = []

        if isinstance(macs, str):
            macs = [macs]

        for mac in macs:
            rc, vmac = self._validate_mac(mac)
            if rc:
                vmacs.append(vmac)
        return vmacs

    def _validate_email(self, email: str) -> bool:
        if re.match(r"^[\w\.-]+@[a-zA-Z\d-]+\.[a-zA-Z]{2,}$", email):
            return True
        return False

    def _validate_passphrase(self, password: str) -> bool:
        if 64 > len(password) > 7:
            return True
        return False

    def _validate_uuid(self, uuid: str) -> bool:
        if re.match(
            r"^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$",
            uuid,
        ):
            return True
        return False

    def _init_callback_method(self):
        self.cb.add_method(
            "get_client_wifi_experience",
            "GET",
            "/v2/api/site/{self.site}/client/",
            "{args[0].lower().strip()}/24hr-satisfaction?mac={args[0].lower().strip()}",
        )
        self.cb.add_method(
            "get_tag", "GET", "/api/s/{self.site}/rest/tag/", "{args[0].strip()}"
        )
        self.cb.add_method("get_topology", "GET", "/v2/api/site/{self.site}/topology")
        self.cb.add_method(
            "get_wlan_capabilities", "GET", "/v2/api/site/{self.site}/wlan-capabilities"
        )
        self.cb.add_method(
            "get_wlan_enriched_configuration",
            "GET",
            "/v2/api/site/{self.site}/wlan/enriched-configuration",
        )
        self.cb.add_method("list_all_admins", "GET", "/api/stat/admin")
        self.cb.add_method("list_apgroups", "GET", "/v2/api/site/{self.site}/apgroups")
        self.cb.add_method(
            "list_clients",
            "GET",
            "/api/s/{self.site}/stat/sta/",
            "{args[0].lower().strip()}",
        )
        self.cb.add_method("list_country_codes", "GET", "/api/s/{self.site}/stat/ccode")
        self.cb.add_method(
            "list_current_channels", "GET", "/api/s/{self.site}/stat/current-channel"
        )
        self.cb.add_method(
            "list_devices_basic", "GET", "/api/s/{self.site}/stat/device-basic"
        )
        self.cb.add_method(
            "list_dynamicdns", "GET", "/api/s/{self.site}/rest/dynamicdns"
        )
        self.cb.add_method("list_extension", "GET", "/api/s/{self.site}/list/extension")
        self.cb.add_method(
            "list_fingerprint_devices",
            "GET",
            "/v2/api/fingerprint_devices/",
            "{args[0].strip()}",
            "0",
        )
        self.cb.add_method(
            "list_firewallgroups",
            "GET",
            "/api/s/{self.site}/rest/firewallgroup/",
            "{args[0].strip()}",
        )
        self.cb.add_method("list_health", "GET", "/api/s/{self.site}/stat/health")
        self.cb.add_method("list_hotspotop", "GET", "/api/s/{self.site}/rest/hotspotop")
        self.cb.add_method(
            "list_known_rogueaps", "GET", "/api/s/{self.site}/rest/rogueknown"
        )
        self.cb.add_method(
            "list_networkconf",
            "GET",
            "/api/s/{self.site}/rest/networkconf/",
            "{args[0].strip()}",
        )
        self.cb.add_method("list_portconf", "GET", "/api/s/{self.site}/list/portconf")
        self.cb.add_method(
            "list_portforwarding", "GET", "/api/s/{self.site}/list/portforward"
        )
        self.cb.add_method(
            "list_portforward_stats", "GET", "/api/s/{self.site}/stat/portforward"
        )
        self.cb.add_method(
            "list_radius_accounts", "GET", "/api/s/{self.site}/rest/account"
        )
        self.cb.add_method(
            "list_radius_profiles", "GET", "/api/s/{self.site}/rest/radiusprofile"
        )
        self.cb.add_method(
            "list_routing",
            "GET",
            "/api/s/{self.site}/rest/routing/",
            "{args[0].strip()}",
        )
        self.cb.add_method("list_self", "GET", "/api/s/{self.site}/self")
        self.cb.add_method("list_settings", "GET", "/api/s/{self.site}/get/setting")
        self.cb.add_method("list_sites", "GET", "/api/self/sites")
        self.cb.add_method("list_tags", "GET", "/api/s/{self.site}/rest/tag")
        self.cb.add_method(
            "list_usergroups", "GET", "/api/s/{self.site}/list/usergroup"
        )
        self.cb.add_method("list_users", "GET", "/api/s/{self.site}/list/user")
        self.cb.add_method(
            "list_wlanconf",
            "GET",
            "/api/s/{self.site}/rest/wlanconf/",
            "{args[0].strip()}",
        )
        self.cb.add_method(
            "stat_client",
            "GET",
            "/api/s/{self.site}/stat/user/",
            "{args[0].lower().strip()}",
        )
        self.cb.add_method(
            "delete_apgroup",
            "DELETE",
            "/v2/api/site/{self.site}/apgroups/",
            "{args[0].strip()}",
        )
        self.cb.add_method(
            "delete_firewallgroup",
            "DELETE",
            "/rest/firewallgroup/",
            "{args[0].strip()}",
        )
        self.cb.add_method(
            "delete_radius_account",
            "DELETE",
            "/api/s/{self.site}/rest/account/",
            "{args[0].strip()}",
        )
        self.cb.add_method(
            "delete_radius_profile",
            "DELETE",
            "/api/s/{self.site}/rest/radiusprofile/",
            "{args[0].strip()}",
        )
        self.cb.add_method(
            "delete_tag", "DELETE", "/api/s/{self.site}/rest/tag/", "{args[0].strip()}"
        )
        self.cb.add_method(
            "delete_usergroup",
            "DELETE",
            "/api/s/{self.site}/rest/usergroup/",
            "{args[0].strip()}",
        )

    ################################################################################
    # PUBLIC INTERFACES
    ################################################################################
    def set_ui_device_uuid(self, uuid: str) -> bool:
        """Set device id to authorize unifi-sync on ui sso web portal

        :param uuid: UUID Universally Unique Identifier 36 characters
        :type uuid: str
        :returns: True on success
        :rtype: bool
        """
        if self._validate_uuid(uuid):
            self.ui_device_id = uuid
            return True
        return False

    def authorize_device(self, uuid: Optional[str] = "") -> bool:
        """Authorize unifi-sync as known device on ui web portal (2FA authentification is supported)

        :param uuid: UUID 36 characters. A random sequence number is chosen if not specified
        :type uuid: Optional str
        :returns: True on success
        :rtype: bool
        """
        if uuid:
            self.set_ui_device_uuid(uuid)

        payload = header = cookie = {}

        # INFO: OPTIONS REQUEST
        logger.debug(f"AUTH_DEV 1         url = {self.ui_ssourl_login}")
        logger.debug(f"AUTH_DEV 1     payload = {payload}")
        logger.debug(f"AUTH_DEV 1      header = {header}")
        logger.debug(f"AUTH_DEV 1      cookie = {cookie}")
        response = self.session.request("OPTIONS", self.ui_ssourl_login)
        logger.debug(f"AUTH_DEV 1 response(j) = {response.json()}")
        logger.debug(f"AUTH_DEV 1 response(h) = {response.headers}")
        logger.debug(f"AUTH_DEV 1 response(c) = {response.cookies}")

        # INFO: PREP REQUEST
        payload = {"user": self.username, "password": self.password}

        # Ref: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Sec-CH-UA
        agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

        header = {
            "Origin": "https://account.ui.com",
            "Priority": "u=1, i",
            "Referer": "https://account.ui.com/",
            "User-Agent": agent,
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }
        cookie = {
            "UI_DEVICE_ID": self.ui_device_id,
        }

        logger.debug(f"AUTH_DEV 2         url = {self.ui_ssourl_login}")
        logger.debug(f"AUTH_DEV 2     payload = {payload}")
        logger.debug(f"AUTH_DEV 2      header = {header}")
        logger.debug(f"AUTH_DEV 2      cookie = {cookie}")
        response = self.session.request(
            "POST", self.ui_ssourl_login, json=payload, headers=header, cookies=cookie
        )
        logger.debug(f"AUTH_DEV 2 response(j) = {response.json()}")
        logger.debug(f"AUTH_DEV 2 response(h) = {response.headers}")
        logger.debug(f"AUTH_DEV 2 response(c) = {response.cookies}")

        if response.json().get("required") == "2fa":
            logger.debug("AUTH_DEV MFA")
            ubic_2fa = response.cookies.get("UBIC_2FA")
            cookie.update({"UBIC_2FA": ubic_2fa})
            cookie.update({"UBIC_AUTH": ubic_2fa.strip('"')})

            mfa_retry_count = self.mfa_retry
            mfa_waiting_msg = True
            mfa_sso_authenticated = False

            while mfa_retry_count > 0 and mfa_waiting_msg:
                logger.debug(
                    f"AUTH_DEV MFA stage1 {mfa_retry_count}             url = {self.ui_ssourl_mfa}"
                )
                logger.debug(
                    f"AUTH_DEV MFA stage1 {mfa_retry_count}         payload = NONE"
                )
                logger.debug(
                    f"AUTH_DEV MFA stage1 {mfa_retry_count}          header = {header}"
                )
                logger.debug(
                    f"AUTH_DEV MFA stage1 {mfa_retry_count}          cookie = {cookie}"
                )

                response = self.session.get(
                    self.ui_ssourl_mfa, headers=header, cookies=cookie
                )

                # INFO when status_code is 202 we are waiting for user mfa until 200 occur
                if response.status_code == 200:
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(j) = {response}"
                    )
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(h) = {response.headers}"
                    )
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(c) = {response.cookies}"
                    )
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}          status = {response.status_code}"
                    )
                    mfa_sso_authenticated = True
                    mfa_waiting_msg = False
                elif response.status_code == 202:
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(j) = {response}"
                    )
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(h) = {response.headers}"
                    )
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(c) = {response.cookies}"
                    )
                    logger.debug(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}         waiting = {self.mfa_wait}"
                    )
                    time.sleep(self.mfa_wait)
                    mfa_retry_count -= 1
                else:
                    logger.error(
                        f"AUTH_DEV MFA stage1 {mfa_retry_count}     response(j) = {response}"
                    )
                    raise Exception(
                        "ERROR wrong http status_code expected {response.status_code}"
                    )

            if mfa_sso_authenticated:
                logger.debug(f"AUTH_DEV 3         url = {self.ui_ssourl_device}")
                logger.debug(f"AUTH_DEV 3     payload = {None}")
                logger.debug(f"AUTH_DEV 3      header = {None}")
                logger.debug(f"AUTH_DEV 3      cookie = {None}")
                response = self.session.request("OPTIONS", self.ui_ssourl_device)
                logger.debug(f"AUTH_DEV 3 response(j) = {response.json()}")
                logger.debug(f"AUTH_DEV 3 response(h) = {response.headers}")
                logger.debug(f"AUTH_DEV 3 response(c) = {response.cookies}")

                payload = {
                    "device_id": self.ui_device_id,
                    "device_name": "py_unifi_api_client",
                    "device_model": "API py_unifi_api_client",
                }
                logger.debug(f"AUTH_DEV 4         url = {self.ui_ssourl_device}")
                logger.debug(f"AUTH_DEV 4     payload = {payload}")
                logger.debug(f"AUTH_DEV 4      header = {header}")
                logger.debug(f"AUTH_DEV 4      cookie = {cookie}")

                response = self.session.request(
                    "POST",
                    self.ui_ssourl_device,
                    json=payload,
                    headers=header,
                    cookies=cookie,
                )

                # IMPORTANT if you have unlocked securl_path setting from account.ui.com
                # you will received permission denied (403).
                # you should lock securl_path settings to obtain 204
                if response.status_code == 204:
                    return True
                return False

            else:
                raise Exception("To be implemented")
        else:
            raise Exception("To be implemented")

    def login(self) -> bool:
        """Authenticate on Unifi controller or ui web portal (2FA authentification is supported)

        :returns: True on success
        :rtype: bool
        :raises LoginExhausted: if number of attent exceed while waiting for ui verification authenticator (2fa)
        :raises LoginFailed: if user authentication failed
        :raises Exception:
        """
        try:
            self.session.verify = self.ssl_verify
            payload = {
                "username": self.username,
                "password": self.password,
                "remember": "false",
                "strict": "true",
            }
            self.headers.update({"Referer": f"{self.authurl_login}"})

            logger.debug(f"LOGIN     url = {self.authurl_login}")
            logger.debug(f"LOGIN payload = {payload}")
            logger.debug(f"LOGIN  header = {self.headers}")
            logger.debug(f"LOGIN  cookie = {self.cookies}")

            response = self.session.post(
                self.authurl_login,
                json=payload,
                headers=self.headers,
                cookies=self.cookies,
            )

            logger.debug(f"LOGIN  response(j) = {response.json()}")
            logger.debug(f"LOGIN  response(h) = {response.headers}")
            logger.debug(f"LOGIN  response(c) = {response.cookies}")

            self._unifi_update_cookies_headers(response)

            if response.json().get("meta", {}).get("rc") == "ok":
                return True

            if response.json().get("meta", {}).get("rc") == "error":
                if (
                    response.json().get("meta", {}).get("msg")
                    == "api.err.Ubic2faTokenRequired"
                ):
                    # self.twofa = True
                    data = response.json().get("data", [])
                    self.cookies.update({"UBIC_2FA": data[0]["mfa_cookie"]})

                    payload.update({"poll_login": "true"})
                    payload.pop("username")
                    payload.pop("password")
                    self.headers.update({"Referer": self.referer_twofa})

                    mfa_retry_count = self.mfa_retry
                    mfa_waiting_msg = True
                    while mfa_retry_count > 0 and mfa_waiting_msg:
                        logger.debug(
                            f"LOGIN MFA stage1             url = {self.authurl_twofa}"
                        )
                        logger.debug(f"LOGIN MFA stage1         payload = {payload}")
                        logger.debug(
                            f"LOGIN MFA stage1          header = {self.headers}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage1          cookie = {self.cookies}"
                        )

                        response = self.session.post(
                            self.authurl_twofa,
                            json=payload,
                            headers=self.headers,
                            cookies=self.cookies,
                        )

                        if (
                            response.json().get("meta", {}).get("msg")
                            != "api.err.WaitingForUiVerifyAuthenticator"
                        ):
                            mfa_waiting_msg = False

                        logger.debug(
                            f"LOGIN MFA stage1     response(j) = {response.json()}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage1     response(h) = {response.headers}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage1     response(c) = {response.cookies}"
                        )

                        logger.debug(
                            f"LOGIN MFA stage1         waiting = {self.mfa_wait}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage1 mfa_retry_count = {mfa_retry_count}"
                        )
                        time.sleep(self.mfa_wait)
                        mfa_retry_count -= 1

                    # if response.cookies['csrf_token'] and response.cookies['unifises']:
                    if set(["csrf_token", "unifises"]).issubset(
                        response.cookies.keys()
                    ):
                        self._unifi_update_cookies_headers(response)

                        logger.debug(
                            f"LOGIN MFA stage2             url = {self.authurl_twofaself}"
                        )
                        logger.debug(f"LOGIN MFA stage2         payload = {payload}")
                        logger.debug(
                            f"LOGIN MFA stage2          header = {self.headers}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage2          cookie = {self.cookies}"
                        )

                        response = self.session.get(
                            self.authurl_twofaself,
                            headers=self.headers,
                            cookies=self.cookies,
                        )

                        logger.debug(
                            f"LOGIN MFA stage2     response(j) = {response.json()}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage2     response(h) = {response.headers}"
                        )
                        logger.debug(
                            f"LOGIN MFA stage2     response(c) = {response.cookies}"
                        )

                        if response.json().get("meta", {}).get("rc") == "ok":
                            self.is_mfa_login = True
                            return True
                    else:
                        logger.debug(
                            f"LOGIN MFA stage1 exhausted number of retry {mfa_retry_count}"
                        )
                        raise api_exception.LoginExhausted(response)
                else:
                    raise api_exception.LoginFailed(response)
            else:
                raise api_exception.LoginFailed(response)
        except Exception as e:
            raise Exception(f"Login error: {e}")

    def logout(self) -> bool:
        """Close authentification on Unifi controller or ui web portal

        :returns: True on success
        :rtype: bool
        :raises Exception:
        """
        try:
            logger.debug(f"LOGOUT         url = {self.authurl_logout}")
            logger.debug(f"LOGOUT      header = {self.headers}")
            logger.debug(f"LOGOUT      cookie = {self.cookies}")

            self.session.verify = self.ssl_verify
            response = self.session.post(self.authurl_logout, cookies=self.cookies)
            logger.debug(f"LOGOUT response(j) = {response.json()}")
            if response.json().get("meta", {}).get("rc") == "ok":
                self.session.close()
                self.is_mfa_login = False
                return True
            else:
                return False
        except Exception as e:
            raise Exception(f"Logout error: {e}")

    def list_devices(self, macs: list[str] = []) -> dict[str, str]:
        """Fetch UniFi devices properties

        :param macs: List or String containing the MAC addresses (invalid mac format are discarded)
        :type macs: list | str
        :returns: List containing known UniFi device objects
        :rtype: dict
        :raises UnknownDevice: if device mac not found
        """
        payload = {"macs": self._get_valid_macs(macs)}
        return self._request_results("POST", f"/api/s/{self.site}/stat/device", payload)

    def list_guests(self, within: Optional[int] = 8760) -> dict[str, str]:
        """Fetch guests devices properties

        :param within: time frame in hours to go back to list guests with valid access (default = 24*365 hours)
        :type within: int
        :returns: Dictionary of guest device objects with valid access
        :rtype: dict
        """
        payload = {"within": within}
        return self._request_results("POST", f"/api/s/{self.site}/stat/guest", payload)

    def invite_admin(
        self,
        name: str,
        email: str,
        enable_sso: Optional[bool] = True,
        readonly: Optional[bool] = False,
        device_adopt: Optional[bool] = False,
        device_restart: Optional[bool] = False,
    ) -> bool:
        """Invite a new admin for access to the current site.

        :param name: name to assign to the new admin user
        :type name: str
        :param email: email address to assign to the new admin user
        :type email: str
        :param enable_sso: whether SSO is allowed for the new admin. Defaults to True
        :type enable_sso: Optional bool
        :param readonly: whether the new admin has readonly permissions. Defaults to False
        :type readonly: Optional bool
        :param device_adoption: whether the new admin has permissions to adopt devices. Defaults to False
        :type device_adoption: Optional bool
        :param device_restart: whether the new admin has permissions to restart devices. Defaults to False
        :type device_restart: Optional bool
        :returns: True on success
        :rtype: bool
        :raises EmailInvalidException: if email format is invalid
        :raises Exception:
        """
        if self._validate_email(email):
            payload = {
                "name": name.strip(),
                "email": email,
                "for_sso": enable_sso,
                "cmd": "invite-admin",
                "role": "readonly" if readonly is True else "admin",
                "permissions": [],
            }

            if device_adopt:
                payload["permissions"].append("API_DEVICE_ADOPT")
            if device_restart:
                payload["permissions"].append("API_DEVICE_RESTART")

            return self._request_results_boolean(
                "POST", f"/api/s/{self.site}/cmd/sitemgr", payload
            )
        raise api_exception.EmailInvalidFormatException(
            f"Invalid email address format for {email}"
        )

    # TODO: add MacInvalidException
    def reconnect_sta(self, mac: str) -> bool:
        """Reconnect a client device

        :param mac: MAC address
        :type mac:  str
        :returns: True on success
        :rtype: bool
        :raises MacInvalidException: if mac address format is invalid
        :raises Exception:
        """
        payload = {"mac": mac.lower().strip(), "cmd": "kick-sta"}

        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/cmd/stamgr", payload
        )

    def block_sta(self, mac: str) -> bool:
        """Block a client device

        :param mac: MAC address
        :type mac:  str
        :returns: True on success
        :rtype: bool
        :raises MacInvalidException: if mac address format is invalid
        :raises Exception:
        """
        payload = {"mac": mac.lower().strip(), "cmd": "block-sta"}

        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/cmd/stamgr", payload
        )

    def unblock_sta(self, mac: str) -> bool:
        """Unblock a client device

        :param mac: MAC address
        :type mac:  str
        :returns: True on success
        :rtype: bool
        :raises MacInvalidException: if mac address format is invalid
        :raises Exception:
        """
        payload = {"mac": mac.lower().strip(), "cmd": "unblock-sta"}

        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/cmd/stamgr", payload
        )

    def forget_sta(self, macs: list[str]) -> bool:
        """Forget a client device(s)

        :param macs: MAC addresses (invalid mac format are discarded)
        :type macs:  str
        :returns: True on success
        :rtype: bool
        :raises Exception:
        """
        payload = {"macs": self._get_valid_macs(macs), "cmd": "forget-sta"}

        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/cmd/stamgr", payload
        )

    # TODO test create_user it's not working on our setup (review payload datastructure first)
    # TODO change reter bool with boot_tuple
    # TODO rework return function to return bool,data
    # TODO raise MacInvalidException: invalid mac address format
    def create_user(
        self,
        mac: str,
        group_id: str,
        name: Optional[str],
        note: Optional[str],
        is_guest: bool = False,
        is_wired: bool = False,
    ) -> dict[str, str]:
        """Create a new user/client-device

        :param mac: MAC address
        :type mac: str
        :param group_id: _id value for the user group the new user/client-device should belong to
        :type group_id: str
        :param name: name to be given to the new user/client-device
        :type name: Optional str
        :param note: note to be applied to the new user/client-device
        :type note: Optional str
        :param is_guest: whether the new user/client-device is a guest. Defaults to False
        :type is_guest: bool
        :param is_wired: whether the new user/client-device is wired. Defaults to False
        :type is_wired: bool
        :returns: object containing details of the new user/client
        :rtype: dict
        :raises MacInvalidException: if mac address format is invalid
        :raises Exception:
        """
        payload = {
            "objects": {
                "data": {
                    "mac": mac.lower().strip(),
                    "usergroup_id": group_id.strip(),
                    "name": name.strip(),
                    "note": note.strip(),
                    "is_guest": is_guest,
                    "is_wired": is_wired,
                }
            }
        }
        print(payload)
        return self._request_results("POST", f"/api/s/{self.site}/group/user", payload)

    def set_sta_note(self, user_id: str, note: Optional[str] = "") -> bool:
        """Set a client-device note

        :param user_id: _id of the client-device
        :type user_id: str
        :param note: note to be applied to the client-device
        :type note: Optional str
        :returns: True on success
        :rtype: bool
        """
        payload = {"note": note.strip()}
        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/upd/user/{user_id.strip()}", payload
        )

    def set_sta_name(self, user_id: str, name: Optional[str]) -> bool:
        """Set a client-device name

        :param user_id: _id of the client-device
        :type user_id: str
        :param name: name to be applied to the client-device
        :type name: Optional str
        :returns: True on success
        :rtype: bool
        """
        payload = {"name": name.strip()}
        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/upd/user/{user_id.strip()}", payload
        )

    def set_sta_groupid(self, user_id: str, group_id: str) -> bool:
        """Set a client-device groupid

        :param user_id: _id of the client-device
        :type user_id: str
        :param group_id: _id value for the user group the new user/client-device should belong to
        :type group_id: str
        :returns: True on success
        :rtype: bool
        """
        payload = {"usergroup_id": group_id.strip()}
        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/upd/user/{user_id.strip()}", payload
        )

    ###################################
    # TODO raise Mac exception to validate mac and ap_mac
    # TODO revalidate with optional args now (up,down,megabytes,ap)
    def authorize_guest(
        self,
        mac: str,
        minutes: int,
        up: Optional[int] = 0,
        down: Optional[int] = 0,
        megabytes: Optional[int] = 0,
        ap_mac: Optional[str] = None,
    ) -> bool:
        """Authorize a client device.

        :param mac: MAC address
        :type mac: str
        :param minutes: minutes (from now) until authorization expires
        :type minutes: int
        :param up: upload speed limit in kbps
        :type up: Optional int
        :param down: download speed limit in kbps
        :type down: Optional int
        :param megabytes: data transfer limit in MB
        :type megabytes: Optional int
        :param ap_mac: AP MAC which client is connected. Should result in faster authorization for client device
        :type ap_mac: Optional str
        :returns: True on success
        :rtype: bool
        :raises MacInvalidException: if mac address format is invalid
        """
        payload = {
            "cmd": "authorize-guest",
            "mac": mac.lower().strip(),
            "minutes": minutes,
        }

        if up:
            payload.update({"up": up})
        if down:
            payload.update({"down": down})
        if megabytes:
            payload.update({"bytes": megabytes})
        if ap_mac:
            payload.update({"ap_mac": ap_mac.lower.strip()})

        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/cmd/stamgr", payload
        )

    # TODO raise mac exception
    def unauthorize_guest(self, mac: str) -> bool:
        """Unauthorize a client device.

        :param mac: MAC address
        :type mac: str
        :returns: True on success
        :rtype: bool
        :raises MacInvalidException: if mac address format is invalid
        """
        payload = {"cmd": "unauthorize-guest", "mac": mac.lower().strip()}

        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/cmd/stamgr", payload
        )

    # TODO query producet result without statss.....
    def stat_5minutes_site(
        self,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
        attributes: Optional[list] = None,
    ) -> dict[str, str]:
        """Fetch 5-minutes site statistics

        :param start: Unix timestamp in millisecond. Defaults to 43200*1000 (or 12 hours ago)
        :type start: Optional int
        :param end: Unix timestamp in millisecond. Defaults to (now)
        :type end: Optional int
        :param attributes: list of attributes to collect. Defaults list (see client.default_site_stats_attributes)
        :type attributes: Optional list
        :results: dictionary of 5-minutes stats objects for the current site
        :rtype: dict
        :raises Exception:
        """
        end = end if end else int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        start = start if start else end - (12 * 3600 * 1000)
        payload = {
            "end": end,
            "start": start,
            "attrs": (
                list(set(attributes + ["time"]))
                if attributes
                else self.default_site_stats_attributes
            ),
        }

        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/report/5minutes.site", payload
        )

    def stat_hourly_site(
        self,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
        attributes: Optional[list] = None,
    ) -> dict[str, str]:
        """Fetch hourly site statistics

        :param start: Unix timestamp in millisecond. Defaults to 604800*1000 (or last 7 days)
        :type start: Optional int
        :param end: Unix timestamp in millisecond. Defaults to (now)
        :type end: Optional int
        :param attributes: list of attributes to collect. Defaults list (see client.default_site_stats_attributes)
        :type attributes: Optional list
        :results: dictionary of hourly stats objects for the current site
        :rtype: dict
        :raises Exception:
        """
        end = end if end else int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        start = start if start else end - (7 * 24 * 3600 * 1000)
        payload = {
            "end": end,
            "start": start,
            "attrs": (
                list(set(attributes + ["time"]))
                if attributes
                else self.default_site_stats_attributes
            ),
        }

        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/report/hourly.site", payload
        )

    def stat_daily_site(
        self,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
        attributes: Optional[list] = None,
    ) -> dict[str, str]:
        """Fetch daily site statistics

        :param start: Unix timestamp in millisecond. Defaults to 31449600*1000 (or last 364 days)
        :type start: Optional int
        :param end: Unix timestamp in millisecond. Defaults to (now)
        :type end: Optional int
        :param attributes: list of attributes to collect. Defaults list (see client.default_site_stats_attributes)
        :type attributes: Optional list
        :results: dictionary of hourly stats objects for the current site
        :rtype: dict
        :raises Exception:
        """
        end = (
            end
            if end
            else int(
                (
                    datetime.now(tz=timezone.utc).timestamp()
                    - (datetime.now(tz=timezone.utc).timestamp() % 3600)
                )
                * 1000
            )
        )
        start = start if start else end - (52 * 7 * 24 * 3600 * 1000)
        payload = {
            "end": end,
            "start": start,
            "attrs": (
                list(set(attributes + ["time"]))
                if attributes
                else self.default_site_stats_attributes
            ),
        }

        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/report/daily.site", payload
        )

    def stat_monthly_site(
        self,
        start: Optional[int] = 0,
        end: Optional[int] = 0,
        attributes: Optional[list] = None,
    ) -> dict[str, str]:
        """Fetch monthly site statistics

        :param start: Unix timestamp in millisecond. Defaults to 31449600*1000 (or last 364 days)
        :type start: Optional int
        :param end: Unix timestamp in millisecond. Defaults to (now)
        :type end: Optional int
        :param attributes: list of attributes to collect. Defaults list (see client.default_site_stats_attributes)
        :type attributes: Optional list
        :results: dictionary of monthly stats objects for the current site
        :rtype: dict
        :raises Exception:
        """
        end = (
            end
            if end
            else int(
                (
                    datetime.now(tz=timezone.utc).timestamp()
                    - (datetime.now(tz=timezone.utc).timestamp() % 3600)
                )
                * 1000
            )
        )
        start = start if start else end - (52 * 7 * 24 * 3600 * 1000)
        payload = {
            "end": end,
            "start": start,
            "attrs": (
                list(set(attributes + ["time"]))
                if attributes
                else self.default_site_stats_attributes
            ),
        }

        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/report/monthly.site", payload
        )

    def stat_speedtest_results(
        self, start: Optional[int] = 0, end: Optional[int] = 0
    ) -> dict[str, str]:
        """Fetch speed test results

        :param start: Unix timestamp in milliseconds. Defaults to 86400*1000 (or 24 hours ago)
        :type start: Optional int
        :param end: Unix timestamp in milliseconds. Defaults to now
        :type end: Optional int
        :returns: Dictionary of speed test result objects
        :rtype: dict
        """
        end = end if end else int(datetime.now(tz=timezone.utc).timestamp() * 1000)
        start = start if start else end - (24 * 3600 * 1000)
        payload = {
            "end": end,
            "start": start,
            "attrs": ["xput_download", "xput_upload", "latency", "time"],
        }
        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/report/archive.speedtest", payload
        )

    def stat_allusers(self, hour: Optional[int] = 8760) -> dict[str, str]:
        """Fetch client devices that connected to the site within given timeframe

        :param hour: Number of hour(s) to go back. Default to 8760 (24*365 = 1 years)
        :type hour: Optional int
        :returns: dictionary of client device objects
        :rtype: dict
        """
        payload = {"type": "all", "conn": "all", "within": hour}
        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/alluser", payload
        )

    def set_usergroup(self, client_id: str, group_id: str) -> bool:
        """Assign a client device to another group

        :param client_id: _id value of the client device to be modified
        :type client_id: str
        :param group_id: _id value of the user group to assign client device to
        :type group_id: str
        :returns: True on success
        :rtype: bool
        """
        payload = {"usergroup_id": group_id.strip()}
        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/upd/user/{client_id.strip()}", payload
        )

    def create_usergroup(
        self,
        group_name: str,
        group_download: Optional[int] = -1,
        group_upload: Optional[int] = -1,
    ) -> dict[str, str]:
        """Create a user group

        :param group_name: name of the user group
        :type group_name: str
        :param group_download: Download bandwidth in Kbps. Defaults to -1 which sets bandwidth to unlimited
        :type group_download: Optional int
        :param group_upload: Upload bandwidth in Kbps. Defaults to -1 which sets bandwidth to unlimited
        :type group_upload: Optional int
        :returns: object with attributes of the new usergroup
        :rtype: dict
        """
        payload = {
            "name": group_name.strip(),
            "qos_rate_max_down": group_download,
            "qos_rate_max_up": group_upload,
        }
        return self._request_results(
            "POST", f"/api/s/{self.site}/rest/usergroup", payload
        )

    def edit_usergroup(
        self,
        group_id: str,
        site_id: str,
        group_name: str,
        group_download: Optional[int] = -1,
        group_upload: Optional[int] = -1,
    ) -> dict[str, str]:
        """Modify a user group

        :param group_id: _id value of the user group
        :type group_id: str
        :param site_id: _id value of the site
        :type site_id: str
        :param group_name: name of the user group
        :type group_name: str
        :param group_download: limit download bandwidth in Kbps. Defaults to -1 which sets bandwidth to unlimited
        :type group_download: Optional int
        :param group_upload: limit upload bandwidth in Kbps. Defaults to -1 which sets bandwidth to unlimited
        :type group_upload: Optional int
        :returns: a single object with attributes of the updated usergroup
        :type: dict
        """
        payload = {
            "_id": group_id.strip(),
            "name": group_name.strip(),
            "qos_rate_max_down": group_download,
            "qos_rate_max_up": group_upload,
            "site_id": site_id.strip(),
        }
        return self._request_results(
            "PUT", f"/api/s/{self.site}/rest/usergroup/{group_id.strip()}", payload
        )

    def create_apgroup(self, group_name: str, macs: list[str]) -> dict[str, str]:
        """Create an AP group

        :param group_name: name to assign to the AP group
        :type group_name: str
        :param macs: MAC addresses of the APs to add to the new group
        :type macs: list[str]
        :returns: a single object with attributes of the new AP group
        :rtype: dict
        """
        payload = {"macs": self._get_valid_macs(macs), "name": group_name.strip()}
        return self._request_results(
            "POST", f"/v2/api/site/{self.site}/apgroups", payload
        )

    def edit_apgroup(
        self, group_id: str, group_name: str, macs: list[str]
    ) -> dict[str, str]:
        """Modify an AP group

        :param group_id: id value of the AP group to modify
        :type group_id: str
        :param group_name: name to assign to the AP group
        :type group_name: str
        :param macs: MAC addresses of the APs to add to the new group
        :type macs: list[str]
        :returns: a single object with attributes of the updated AP group
        :rtype: dict
        """
        payload = {
            "_id": group_id.strip(),
            "attr_no_delete": False,
            "name": group_name.strip(),
            "macs": self._get_valid_macs(macs),
        }
        return self._request_results(
            "PUT", f"/v2/api/site/{self.site}/apgroups/{group_id.strip()}", payload
        )

    def create_firewallgroup(
        self, group_name: str, group_type: str, group_members: list = []
    ) -> dict[str, str]:
        """Create a firewall group

        :param group_name: name to assign to the firewall group
        :type group_name: str
        :param group_type: firewall group type. (see client.default_group_type_attributes)
        :type group_type: str
        :param group_members: array containing members of the new group. Defaults empty list
        :type group_members: list
        :returns: a single object with attributes of the new firewall group
        :rtype: dict
        """
        if group_type.strip() in self.default_group_type_attributes:
            payload = {
                "name": group_name.strip(),
                "group_type": group_type.strip(),
                "group_members": [x.strip() for x in group_members],
            }
            return self._request_results(
                "POST", f"/api/s/{self.site}/rest/firewallgroup", payload
            )
        else:
            raise Exception(
                f"ERROR: create_firewallgroup - group_type {group_type} not valid"
            )

    def edit_firewallgroup(
        self,
        group_id: str,
        site_id: str,
        group_name: str,
        group_type: str,
        group_members: list = [],
    ) -> dict[str, str]:
        """Modify a firewall group

        :param group_id: _id value of the firewall group to modify
        :type group_id: str
        :param site_id: site_id value of the firewall group to modify
        :type site_id: str
        :param group_name: name of the firewall group
        :type group_name: str
        :param group_type: firewall group type. (see client.default_group_type_attributes)
        :type group_type: str
        :param group_members: (Default: [])
        :type group_members: list
        :returns: a single object with attributes of the updated firewall group
        :rtype: dict
        """
        if group_type.strip() in self.default_group_type_attributes:
            payload = {
                "_id": group_id.strip(),
                "name": group_name.strip(),
                "group_type": group_type.strip(),
                "group_members": [x.strip() for x in group_members],
                "site_id": site_id,
            }
            return self._request_results(
                "PUT",
                f"/api/s/{self.site}/rest/firewallgroup/{group_id.strip()}",
                payload,
            )
        else:
            raise Exception(
                f"ERROR: edit_firewallgroup - group_type {group_type} not valid"
            )

    def create_tag(self, name: str, macs: Optional[list] = []) -> bool:
        """Create a device tag

        :param name: the tag name to add
        :type name: str
        :param macs: MAC address(es) for the device(s). Defaults to empty list
        :type macs: Optional list[str]
        :returns: True on success
        :rtype: bool
        """
        payload = {"member_table": self._get_valid_macs(macs), "name": name.strip()}
        return self._request_results_boolean(
            "POST", f"/api/s/{self.site}/rest/tag", payload
        )

    def set_tagged_devices(self, macs: list[str], tag_id: str) -> bool:
        """Set tagged devices

        :param macs: list of the MAC address(es) for the device(s) to tag. Invalid MAC will be removed from the list
        :type macs: list[str]
        :param tag_id: _id value of the tag
        :type tag_id: str
        :returns: True on success
        :rtype: bool
        """
        payload = {
            "member_table": self._get_valid_macs(macs),
        }
        return self._request_results_boolean(
            "PUT", f"/api/s/{self.site}/rest/tag/{tag_id.strip()}", payload
        )

    def list_rogueaps(self, within: Optional[int] = 24) -> dict[str, str]:
        """Fetch rogue/neighboring access points

        :param within: hours to go back to list discovered "rogue" access points. Defaults to 24 (24 hours)
        :type within: Optional int
        :returns: rogue/neighboring access point objects
        :rtype: dict
        """
        payload = {"within": within}
        return self._request_results(
            "POST", f"/api/s/{self.site}/stat/rogueap", payload
        )

    def generate_backup(self, days: int = -1) -> dict[str, str]:
        """Generate a backup

        :param days: number of days for which the backup must be generated. Defaults to -1
        :type days: int
        :returns:  URL from where the backup file can be downloaded once generated
        :rtype: dict
        :raises ApiErrorNoPermission: if Permission is denied
        """
        payload = {"cmd": "backup", "days": days}
        return self._request_results("POST", f"/api/s/{self.site}/cmd/backup", payload)

    def list_backups(self) -> dict[str, str]:
        """Fetch auto backups

        :returns: objects with backup details
        :rtype: dict[str, str]
        :raises ApiErrorNoPermission: if Permission is denied
        """
        payload = {
            "cmd": "list-backups",
        }
        return self._request_results("POST", f"/api/s/{self.site}/cmd/backup", payload)

    # NOTE site_decription is the name seen by user.
    # site structure is composed of {}"anonymous_id": "fulluuid","desc": "usersitename",
    # "name": "internal_name","external_id": "fulluuid","_id": "uuid"}

    def create_site(self, site_description: str) -> tuple:
        """Create a site
        NOTE: name seen by user not the site_name. No validation for duplicate site

        :param site_description: long name for the new site.
        :type site_description: str
        :returns: (bool,dict) object with attributes of the new site ("_id", "desc", "name")
        :rtype: tuple
        :raises ApiErrorNoPermission: if Permission is denied
        """
        payload = {"desc": site_description.strip(), "cmd": "add-site"}
        return self._request_results_boolean_tuple(
            "POST", f"/api/s/{self.site}/cmd/sitemgr", payload
        )

    def create_unique_site(self, site_description: str) -> tuple:
        """Create a unique site
        NOTE: name seen by user not the site_name. Validate for duplicate site

        :param site_description: long name for the new site
        :type site_description: str
        :returns: (bool,dict) object with attributes of the new or existing site if already exist.
        :rtype: tuple
        :raises ApiErrorNoPermission: if Permission is denied
        """
        sites = self.list_sites()

        if sites.get("meta", {}).get("rc") == "ok":
            for data in sites.get("data", []):
                if data["desc"] == site_description:
                    reshape = json.loads(self.reshape_str)
                    reshape.update({"data": data})
                    return (True, reshape)
            return self.create_site(site_description)
        else:
            return (False, {})

    def list_sites_without_device(self) -> tuple:
        sites = self.list_sites()
        if sites.get("meta", {}).get("rc") == "ok":
            data = []
            for site in sites.get("data", []):
                if site["device_count"] == 0:
                    data.append(site)
            if len(data) > 0:
                reshape = json.loads(self.reshape_str)
                reshape.update({"data": data})
                return (True, reshape)
            else:
                return (False, {})
        else:
            return (False, {})

    # Raise ApiErrorNoDelete
    def delete_site(self, site_id: str) -> tuple:
        payload = {"site": site_id.strip(), "cmd": "delete-site"}
        return self._request_results_boolean_tuple(
            "POST", f"/api/s/{self.site}/cmd/sitemgr", payload
        )

    # return deleted sites
    # we are aware of default site so we will not be deleted
    def delete_sites_without_device(self) -> tuple:
        rc, sites = self.list_sites_without_device()
        if rc:
            if sites.get("meta", {}).get("rc") == "ok":
                data = []
                for site in sites.get("data", []):
                    if not set(["attr_no_delete", "attr_hidden_id"]).issubset(site):
                        self.delete_site(site["_id"])
                        data.append(site)
                if len(data) > 0:
                    reshape = json.loads(self.reshape_str)
                    reshape.update({"data": data})
                    return (True, reshape)
        return (False, {})

    def set_site_description(
        self, site_description: str, site_name: Optional[str]
    ) -> bool:
        payload = {"desc": site_description.strip(), "cmd": "update-site"}
        if not site_name:
            site_name = self.site
        return self._request_results_boolean(
            "POST", f"/api/s/{site_name}/cmd/sitemgr", payload
        )

    def list_firmware(self, type: Optional[str] = "available") -> tuple:
        payload = {"cmd": "list-" + type}
        if type not in ["available", "cached"]:
            return False
        else:
            return self._request_results_boolean_tuple(
                "POST", f"/api/s/{self.site}/cmd/firmware", payload
            )

    def create_network(self, payload: dict[str, str]) -> tuple:
        if payload:
            return self._request_results_boolean_tuple(
                "POST", f"/api/s/{self.site}/rest/networkconf", payload
            )
        return (False, {})

    def delete_network(self, network_id: str) -> bool:
        return self._request_results_boolean(
            "DELETE", f"/api/s/{self.site}/rest/networkconf/{network_id.strip()}"
        )

    def delete_network_by_vlan(self, vlan_name: str, vlan_id: int) -> bool:
        network = self.list_networkconf()

        for net in network.get("data", []):
            if set(["vlan", "purpose", "name", "_id"]).issubset(net):
                if (
                    net["vlan"] == vlan_id
                    and net["name"] == vlan_name
                    and net["purpose"] == "vlan-only"
                ):
                    self.delete_network(net["_id"])
        return False

    def get_network_by_vlan_name(self, vlan_name: str) -> tuple:
        networkconf = self.list_networkconf()

        for net in networkconf.get("data", []):
            if set(["vlan", "name", "_id"]).issubset(net):
                if net["name"] == vlan_name:
                    return (True, net)
        return (False, {"name": "", "_id": ""})

    def get_network_by_vlan_id(self, vlan_id: int) -> tuple:
        networkconf = self.list_networkconf()

        for net in networkconf.get("data", []):
            if set(["vlan", "name", "_id"]).issubset(net):
                if net["vlan"] == vlan_id:
                    return (True, net)
        return (False, {"name": "", "_id": ""})

    def create_network_vlan(self, vlan_name: str, vlan_id: int) -> tuple:
        payload = {
            "vlan_enabled": "true",
            "purpose": "vlan-only",
            "name": vlan_name.strip(),
            "vlan": vlan_id,
            "enabled": "true",
            "igmp_snooping": "false",
            "dhcpguard_enabled": "false",
            "network_isolation_enabled": "false",
            "is_nat": "true",
        }
        return self.create_network(payload)

    def create_wlan(
        self,
        name: str,
        x_passphrase: str,
        ap_group_ids: Optional[str] = "",
        security: Optional[str] = "wpapsk",
        wpa_mode: Optional[str] = "wpa2",
        wpa_enc: Optional[str] = "ccmp",
        setting_preference: Optional[str] = "auto",
        payload: Optional[dict[str, str]] = dict(),
    ) -> tuple:

        if not name:
            print("ERROR you need to specify name")
        else:
            rc, wlan = self.get_wlan_by_name(name)
            if rc:
                raise Exception(
                    f"create_wlan error: wlan_name={name} id={wlan['_id']} already exist"
                )

        if setting_preference not in ["auto", "manual"]:
            print("ERROR not valid preference")

        if not x_passphrase:
            print("ERROR you need to specify pass")

        if not self._validate_passphrase(x_passphrase):
            print("ERROR Password must be between 8-63 characters")

        # INFO: Try to find default ap_group_ids if not specified by user
        if not ap_group_ids:
            for apg in self.list_apgroups():
                if set(["_id", "attr_hidden_id", "device_macs"]).issubset(apg):
                    if (
                        len(apg["device_macs"]) > 0
                        and apg["attr_hidden_id"] == "default"
                    ):
                        payload.update({"ap_group_ids": [apg["_id"]]})

        for arg in [
            "name",
            "x_passphrase",
            "security",
            "wpa_mode",
            "wpa_enc",
            "setting_preference",
        ]:
            if arg in locals():
                payload.update({arg: locals()[arg].strip()})
            else:
                raise Exception(
                    f"create_vlan error: {arg} is an invalid method parameter"
                )

        return self._request_results_boolean_tuple(
            "POST", f"/api/s/{self.site}/add/wlanconf", payload
        )

    def delete_wlan(self, wlan_id: str) -> bool:
        return self._request_results_boolean(
            "DELETE", f"/api/s/{self.site}/rest/wlanconf/{wlan_id.strip()}"
        )

    def delete_wlan_by_name(self, wlan_name: str) -> bool:
        rc, wlan = self.get_wlan_by_name(wlan_name)
        if rc:
            if wlan["enabled"]:
                raise Exception(
                    f"delete_wlan_name error: wlan_name={wlan_name} enabled={wlan['enabled']}, please disable first"
                )
            else:
                self.delete_wlan(wlan["_id"])
        return False

    def set_wlan_password(self, wlan_id: str, x_passphrase: str) -> bool:
        if self._validate_passphrase(x_passphrase):
            return self.set_wlanconf(wlan_id, {"x_passphrase": x_passphrase})
        return False

    def set_wlan_password_by_name(self, wlan_name: str, x_passphrase: str) -> bool:
        if self._validate_passphrase(x_passphrase):
            rc, wlan = self.get_wlan_by_name(wlan_name)
            if rc:
                return self.set_wlanconf(wlan["_id"], {"x_passphrase": x_passphrase})
        return False

    def set_wlanconf(self, wlan_id: str, payload: str) -> bool:
        return self._request_results_boolean(
            "PUT", f"/api/s/{self.site}/rest/wlanconf/{wlan_id.strip()}", payload
        )

    def set_wlanconf_by_name(self, wlan_name: str, payload: str) -> bool:
        rc, wlan = self.get_wlan_by_name(wlan_name)
        if rc:
            return self.set_wlanconf(wlan["_id"], payload)
        return False

    def disable_wlan_by_name(self, wlan_name: str) -> bool:
        return self.set_wlanconf_by_name(wlan_name, {"enabled": False})

    def enable_wlan_by_name(self, wlan_name: str) -> bool:
        return self.set_wlanconf_by_name(wlan_name, {"enabled": True})

    def get_wlan_by_name(self, wlan_name: str) -> tuple:
        wlanconf = self.list_wlanconf()

        for wlan in wlanconf.get("data", []):
            if set(["enabled", "name", "_id"]).issubset(wlan):
                if wlan["name"] == wlan_name:
                    return (True, wlan)
        return (False, {"enabled": False, "name": "", "_id": ""})

    # {"attr_no_delete":false,"attr_hidden_id":"","name":"test","use_usg_auth_server":false,
    # "auth_servers":[{"ip":"172.17.0.1","port":1812,"x_secret":"waza123"}],
    # "acct_servers":[{"ip":"172.17.0.1","port":1813,"x_secret":"waza4321"}],
    # "vlan_enabled":false,"vlan_wlan_mode":"disabled","accounting_enabled":true,"interim_update_enabled":false,"interim_update_interval":"3600","x_ca_crts":[]}
    def create_radius_profile(
        self,
        name: str,
        auth_ip: str,
        acct_ip: str,
        auth_secret: str,
        acct_secret: str,
        auth_port: Optional[int] = 1812,
        acct_port: Optional[int] = 1813,
    ) -> tuple:
        payload = {
            "name": name,
            "accounting_enabled": True,
            "auth_servers": [
                {"ip": auth_ip, "port": auth_port, "x_secret": auth_secret}
            ],
            "acct_servers": [
                {"ip": acct_ip, "port": acct_port, "x_secret": acct_secret}
            ],
        }
        return self._request_results_boolean_tuple(
            "POST", f"/api/s/{self.site}/rest/radiusprofile", payload
        )

    def create_radius_account(
        self,
        name: str,
        x_password: str,
        tunnel_type: Optional[int] = 0,
        tunnel_medium_type: Optional[int] = 0,
        vlan_id: Optional[int] = 0,
    ) -> tuple:
        payload = {
            "name": name.strip(),
            "x_password": x_password.strip(),
        }

        tunnel_type_values = list(range(1, 13 + 1))
        tunnel_medium_type_values = list(range(1, 15 + 1))

        if (tunnel_type not in tunnel_type_values) or (
            tunnel_medium_type not in tunnel_medium_type_values
        ):
            return (False, {})
        else:
            if tunnel_type:
                payload.update({"tunnel_type": tunnel_type})
            if tunnel_medium_type:
                payload.update({"tunnel_medium_type": tunnel_medium_type})
        if vlan_id:
            payload.update({"vlan": vlan_id})
        return self._request_results_boolean_tuple(
            "POST", f"/api/s/{self.site}/rest/account", payload
        )

    def get_radius_account_by_name(self, account_name: str) -> tuple:
        radius_account = self.list_radius_accounts()
        for account in radius_account.get("data", []):
            if set(["name", "_id"]).issubset(account):
                if account["name"] == account_name:
                    return (True, account)
        return (False, {"name": "", "_id": ""})

    def set_radius_account(self, account_id: str, payload: dict[str, str]) -> tuple:
        return self._request_results_boolean_tuple(
            "PUT", f"/api/s/{self.site}/rest/account/{account_id.strip()}", payload
        )

    def set_radius_account_by_name(
        self, account_name: str, payload: dict[str, str]
    ) -> tuple:
        rc, account = self.get_radius_account_by_name(account_name)
        if rc:
            return self.set_radius_account(account["_id"], payload)
        return (False, {})

    def set_radius_account_password_by_name(
        self, account_name: str, x_password: str
    ) -> bool:
        return self.set_radius_account_by_name(account_name, {"x_password": x_password})

    def delete_radius_account_by_name(self, account_name: str) -> tuple:
        rc, account = self.get_radius_account_by_name(account_name)
        if rc:
            return self.delete_radius_account(account["_id"])
        return (False, {})

    def restart_device(
        self, macs: list[str], reboot_type: Optional[str] = "soft"
    ) -> bool:
        payload = {"cmd": "restart", "macs": self._get_valid_macs(macs)}

        if reboot_type in ["soft", "hard"]:
            return self._request_results_boolean(
                "POST", f"/api/s/{self.site}/cmd/devmgr", payload
            )
        else:
            return False

    def enable_logging(self, level: Optional[int] = logging.DEBUG):
        """Enable diagnostic logging

        :param level: integer value (use perdefined numeric values from logging levels). Defaults to logging.DEBUG
        :type level: Optional[int]
        """
        logger.setLevel(level)

    def disable_logging(self, level: Optional[int] = logging.NOTSET):
        """Disable diagnostic logging

        :param level: integer value (use perdefined numeric values from logging levels). Defaults to logging.NOTSET
        :type level: Optional[int]
        """
        logger.setLevel(level)
