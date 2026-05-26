from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from PyQt6.QtCore import QSettings

from app_startup_lib import is_windows_startup_enabled, set_windows_startup_enabled


APP_ORG = "PLKHealth"
APP_NAME = "ICU-Sync"
DEFAULT_HOSXP_HOST = "192.168.10.118"
DEFAULT_HOSXP_PORT = 3306
DEFAULT_ICUCONS_BASE_URL = "https://icucons.plkhealth.go.th"
DEFAULT_ICUCONS_API_PATH = "/api/icu"
DEFAULT_ICUCONS_API_ENDPOINT = f"{DEFAULT_ICUCONS_BASE_URL}{DEFAULT_ICUCONS_API_PATH}"
LEGACY_HOSXP_HOST = "localhost"
LEGACY_HOSXP_PORT = 3306
INVALID_HOSXP_HOSTS = {"hos-192.168.10.118"}


@dataclass(slots=True)
class AppSettings:
    hosxp_host: str = DEFAULT_HOSXP_HOST
    hosxp_port: int = DEFAULT_HOSXP_PORT
    hosxp_database: str = "hos"
    hosxp_user: str = ""
    hosxp_password: str = ""
    icucons_api_endpoint: str = DEFAULT_ICUCONS_API_ENDPOINT
    icucons_base_url: str = DEFAULT_ICUCONS_BASE_URL
    icucons_api_path: str = DEFAULT_ICUCONS_API_PATH
    icucons_api_token: str = ""
    icucons_timeout: int = 30
    icucons_post_interval_minutes: int = 0
    run_on_windows_boot: bool = False


def split_icucons_api_endpoint(endpoint: str) -> tuple[str, str]:
    endpoint = (endpoint or DEFAULT_ICUCONS_API_ENDPOINT).strip()
    if not endpoint:
        endpoint = DEFAULT_ICUCONS_API_ENDPOINT

    parsed = urlsplit(endpoint)
    if not parsed.scheme or not parsed.netloc:
        api_path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        return DEFAULT_ICUCONS_BASE_URL, api_path

    base_url = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    api_path = urlunsplit(
        ("", "", parsed.path or DEFAULT_ICUCONS_API_PATH, parsed.query, "")
    )
    return base_url, api_path


def normalize_icucons_api_endpoint(endpoint: str) -> str:
    base_url, api_path = split_icucons_api_endpoint(endpoint)
    return f"{base_url.rstrip('/')}/{api_path.lstrip('/')}"


class SettingsLogic:
    def __init__(self) -> None:
        self._settings = QSettings(APP_ORG, APP_NAME)

    def load(self) -> AppSettings:
        hosxp_host = self._settings.value("hosxp/host", DEFAULT_HOSXP_HOST, str)
        hosxp_port = self._settings.value("hosxp/port", DEFAULT_HOSXP_PORT, int)
        if (
            hosxp_host in INVALID_HOSXP_HOSTS
            or (hosxp_host == LEGACY_HOSXP_HOST and hosxp_port == LEGACY_HOSXP_PORT)
        ):
            hosxp_host = DEFAULT_HOSXP_HOST
            hosxp_port = DEFAULT_HOSXP_PORT
            self._settings.setValue("hosxp/host", hosxp_host)
            self._settings.setValue("hosxp/port", hosxp_port)
            self._settings.sync()

        legacy_base_url = self._settings.value(
            "icucons/base_url",
            DEFAULT_ICUCONS_BASE_URL,
            str,
        )
        legacy_api_path = self._settings.value(
            "icucons/api_path",
            DEFAULT_ICUCONS_API_PATH,
            str,
        )
        api_endpoint = self._settings.value(
            "icucons/api_endpoint",
            f"{legacy_base_url.rstrip('/')}/{legacy_api_path.lstrip('/')}",
            str,
        )
        api_endpoint = normalize_icucons_api_endpoint(api_endpoint)
        icucons_base_url, icucons_api_path = split_icucons_api_endpoint(api_endpoint)

        return AppSettings(
            hosxp_host=hosxp_host,
            hosxp_port=hosxp_port,
            hosxp_database=self._settings.value("hosxp/database", "hos", str),
            hosxp_user=self._settings.value("hosxp/user", "", str),
            hosxp_password=self._settings.value("hosxp/password", "", str),
            icucons_api_endpoint=api_endpoint,
            icucons_base_url=icucons_base_url,
            icucons_api_path=icucons_api_path,
            icucons_api_token=self._settings.value("icucons/api_token", "", str),
            icucons_timeout=self._settings.value("icucons/timeout", 30, int),
            icucons_post_interval_minutes=self._settings.value(
                "icucons/post_interval_minutes",
                0,
                int,
            ),
            run_on_windows_boot=is_windows_startup_enabled(),
        )

    def save(self, values: AppSettings) -> None:
        self._settings.setValue("hosxp/host", values.hosxp_host)
        self._settings.setValue("hosxp/port", values.hosxp_port)
        self._settings.setValue("hosxp/database", values.hosxp_database)
        self._settings.setValue("hosxp/user", values.hosxp_user)
        self._settings.setValue("hosxp/password", values.hosxp_password)
        api_endpoint = normalize_icucons_api_endpoint(values.icucons_api_endpoint)
        base_url, api_path = split_icucons_api_endpoint(api_endpoint)
        self._settings.setValue("icucons/api_endpoint", api_endpoint)
        self._settings.setValue("icucons/base_url", base_url)
        self._settings.setValue("icucons/api_path", api_path)
        self._settings.setValue("icucons/api_token", values.icucons_api_token)
        self._settings.setValue("icucons/timeout", values.icucons_timeout)
        self._settings.setValue(
            "icucons/post_interval_minutes",
            values.icucons_post_interval_minutes,
        )
        self._settings.setValue("app/run_on_windows_boot", values.run_on_windows_boot)
        set_windows_startup_enabled(values.run_on_windows_boot)
        self._settings.sync()
