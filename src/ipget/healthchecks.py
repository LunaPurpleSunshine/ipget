import logging
import socket
import urllib.request as req
from http.client import HTTPResponse
from os import environ
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from uuid import UUID, uuid4

from ipget.errors import ConfigurationError

log = logging.getLogger(__name__)


class HealthCheck:
    def __init__(self) -> None:
        log.debug("Creating HealthCheck object using UUID")
        self._run_id: UUID = self.regen_uuid()
        self._server: str = environ.get(
            "IPGET_HEALTHCHECK_SERVER", "https://hc-ping.com"
        )

        if uuid := environ.get("IPGET_HEALTHCHECK_UUID"):
            self._check_uuid = uuid
        else:
            raise ConfigurationError("IPGET_HEALTHCHECK_UUID")

        self._url: str = ""

    def get_rid(self) -> UUID:
        return self._run_id

    def regen_uuid(self) -> UUID:
        self._run_id = uuid4()
        return self._run_id

    def _get_base_url(self) -> str:
        base_url = urljoin(self._server, self._check_uuid)
        log.debug(f"Base url: {base_url}")
        return base_url

    def _get_ping_url(self, ping_type: str | int) -> str:
        valid_ping_types = ["success", "start", "fail", "log"]
        if isinstance(ping_type, str) and ping_type not in valid_ping_types:
            raise ValueError(f"Ping type should be one of {valid_ping_types}")
        else:
            ping_type = str(ping_type)
        base = self._get_base_url()
        query = urlencode({"rid": self.get_rid()})
        if ping_type.lower() == "success":
            self._url = f"{base}?{query}"
        else:
            self._url = f"{base}/{ping_type}?{query}"
        log.debug(f"Pinging: {self._url}")
        return self._url

    @staticmethod
    def _encode_payload_data(data: dict | bytes | None) -> bytes | None:
        """Returns result from urlencode as bytes,
        ready for use as the payload for a POST request
        """
        if data is None or isinstance(data, bytes):
            return data
        log.debug("Encoding data for POST")
        return urlencode(data).encode("ascii")

    def _request(
        self,
        timeout: int = 10,
        ping_type: str | int = "success",
        post_data: bytes | dict | None = None,
    ) -> HTTPResponse | HTTPError | None:
        url = self._get_ping_url(ping_type)
        try:
            return req.urlopen(
                url,
                timeout=timeout,
                data=self._encode_payload_data(post_data),
            )
        except (HTTPError, socket.error) as e:
            log.exception(f"Ping to '{url}' of type: {ping_type} failed:\n{e}")
            return None

    def success(
        self, payload: bytes | dict | None = None, timeout: int = 10
    ) -> HTTPResponse | HTTPError | None:
        """Send a 'Success' ping"""
        log.info("Sending 'success' ping")
        return self._request(ping_type="success", timeout=timeout, post_data=payload)

    def start(
        self, payload: bytes | dict | None = None, timeout: int = 10
    ) -> HTTPResponse | HTTPError | None:
        """Send a 'Start' ping"""
        log.info("Sending 'start' ping")
        return self._request(ping_type="start", timeout=timeout, post_data=payload)

    def fail(
        self, payload: bytes | dict | None = None, timeout: int = 10
    ) -> HTTPResponse | HTTPError | None:
        """Send a 'fail' ping"""
        log.info("Sending 'fail' ping")
        return self._request(ping_type="fail", timeout=timeout, post_data=payload)

    def log(
        self,
        payload: bytes | dict | None = None,
        timeout: int = 10,
        ping_body_limit: int = 100,
    ) -> HTTPResponse | HTTPError | None:
        """Send a 'log' ping"""
        log.info("Sending 'log' ping, check status will not change")
        raise NotImplementedError

    def returncode(
        self, returncode: int, payload: bytes | dict | None = None, timeout: int = 10
    ) -> HTTPResponse | HTTPError | None:
        """Send a ping reporting script's exit status"""
        log.info(f"Sending returncode ping: {returncode}")
        return self._request(ping_type=returncode, timeout=timeout, post_data=payload)


def get_healthcheck() -> HealthCheck | None:
    try:
        return HealthCheck()
    except ConfigurationError as e:
        log.exception(f"{e}, Healthchecks integration disabled")
        return None
