import os

from dynaconf import Dynaconf
from dynaconf.base import LazySettings

SETTING_ENV_FILE = os.getenv("SETTING_ENV_FILE", "settings.local.yaml")
settings: LazySettings = Dynaconf(settings_files=[SETTING_ENV_FILE])


# setting sentry
SENTRY_ACTIVE = False  # Disable sentry by default
SENTRY_DNS_PUBLIC = settings.services.sentry.dns_public
SENTRY_DNS_AI = settings.services.sentry.dns_ai
SENTRY_ENV = settings.services.sentry.environment
SENTRY_TRACE_SAMPLE_RATE = float(settings.services.sentry.traces_sample_rate)
