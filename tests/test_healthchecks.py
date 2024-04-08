from datetime import datetime, timezone
from http.client import HTTPResponse
from os import environ
from urllib.error import HTTPError
from uuid import UUID

import pytest
from pytest import MonkeyPatch

from ipget.environment import HEALTHCHECK_SERVER_ENV, HEALTHCHECK_UUID_ENV
from ipget.errors import ConfigurationError
from ipget.healthchecks import HealthCheck
from ipget.settings import HealthcheckSettings

HEALTHCHECK_REQUIRES = [
    environ.get("IPGET_TEST_HEALTHCHECK_SERVER"),
    environ.get("IPGET_TEST_HEALTHCHECK_UUID"),
]


def test_encode_payload_data():
    payload = {"test": 123, "ip": "10.10.10.0"}
    result = HealthCheck._encode_payload_data(payload)
    assert result is not None
    assert result.decode("ascii") == "test=123&ip=10.10.10.0"


@pytest.mark.skipif(
    condition=not all(HEALTHCHECK_REQUIRES),
    reason="Healthcheck requirements not given in .env.test",
)
class HealthcheckRequirements: ...


class TestHealthCheckConfig:
    def test_load_settings(self):
        test_server = "http://test.server"
        test_uuid = "abc"
        conf = HealthcheckSettings(server=test_server, uuid=test_uuid)
        hc = HealthCheck(conf)
        assert hc._server == test_server
        assert hc._check_uuid == test_uuid

    def test_no_uuid(self, monkeypatch: MonkeyPatch):
        monkeypatch.setenv(HEALTHCHECK_SERVER_ENV, "test_no_uuid")
        monkeypatch.delenv(HEALTHCHECK_UUID_ENV, raising=False)
        with pytest.raises(ConfigurationError):
            HealthCheck()

    def test_default_server(self, monkeypatch: MonkeyPatch):
        monkeypatch.delenv(HEALTHCHECK_SERVER_ENV, raising=False)
        monkeypatch.setenv(HEALTHCHECK_UUID_ENV, "test_default_server")
        assert HealthCheck()._server == "https://hc-ping.com"

    def test_get_rid(self, dummy_healthcheck):
        assert isinstance(dummy_healthcheck.get_rid(), UUID)

    def test_regen_uuid(self, dummy_healthcheck):
        id1 = dummy_healthcheck.get_rid()
        id2 = dummy_healthcheck.regen_uuid()
        assert id1 != id2


class TestHealthCheckPings:
    def test_start(self, mock_healthcheck_with_response):
        hc = HealthCheck()
        hc.start(payload={"test": "Start"})
        assert "/start?" in hc._url

    def test_success(self, mock_healthcheck_with_response):
        hc = HealthCheck()
        data = {"test": "Success", "ip": "10.10.10.0"}
        hc.success(payload=data)
        assert hc._url.endswith(f"{hc._check_uuid}?rid={hc.get_rid()}")

    def test_fail(self, mock_healthcheck_with_response):
        hc = HealthCheck()
        hc.fail(payload={"test": "Failure"})
        assert "/fail?" in hc._url

    def test_returncode(self, mock_healthcheck_with_response):
        hc = HealthCheck()
        hc.returncode(0, payload={"test": "returncode"})
        assert "/0?" in hc._url

    @pytest.mark.skipif(
        condition=not environ.get("IPGET_TEST_HEALTHCHECK_UUID"),
        reason="Healthcheck UUID not given in .env.test",
    )
    def test_real_healthcheck(self, env_testing_healthcheck_settings):
        hc = HealthCheck(env_testing_healthcheck_settings)
        try:
            response = hc.success(
                payload={
                    "test": datetime.now(timezone.utc).isoformat(timespec="minutes")
                }
            )
        except HTTPError as e:
            pytest.skip(reason=f"Encountered HTTP Error {e.getcode()} {e.name}")
        assert isinstance(response, HTTPResponse)
        assert response.getcode() == 200
