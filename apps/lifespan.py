import asyncio
from contextlib import asynccontextmanager

import crochet
from fastapi import FastAPI

from config import settings
from services.scylladb.mm_scylla_db import MMScyllaDB
from shared_components.services.aws.aws_client import AWSClient
from shared_components.services.db.app_scylla_db import AppScyllaDB
from shared_components.utilities.design_patterns.singleton_registry import Si


@asynccontextmanager
async def api_lifespan(app: FastAPI):  # noqa
    crochet.setup()
    await asyncio.gather(
        Si(MMScyllaDB).connect(settings.services.scylladb.music_monster),
    )
    Si(AppScyllaDB).inject_from_other(Si(MMScyllaDB))
    Si(AWSClient).connect(
        settings.services.aws.access_key_id,
        settings.services.aws.secret_access_key,
        settings.services.aws.region,
        settings.services.aws.kms_key_id,
        settings.services.aws.s3_default_bucket,
    )
    yield
    Si(MMScyllaDB).disconnect()
