import sentry_sdk
from fastapi import FastAPI

from apps.lifespan import api_lifespan
from apps.root_router import router
from config import SENTRY_ACTIVE, SENTRY_DNS_PUBLIC, SENTRY_ENV, SENTRY_TRACE_SAMPLE_RATE
from shared_components.biz.app_base.health_check_route import health_check_route

app = FastAPI(title="Web crawlers worker", routes=[health_check_route], lifespan=api_lifespan)

if SENTRY_ACTIVE == "true" or SENTRY_ACTIVE is True:
    sentry_sdk.init(
        dsn=SENTRY_DNS_PUBLIC,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=float(SENTRY_TRACE_SAMPLE_RATE),
        environment=SENTRY_ENV,
    )

app.include_router(router, prefix="/api")
