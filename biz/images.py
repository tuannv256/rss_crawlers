import logging
import uuid
from io import BytesIO

import requests
from PIL import Image

from shared_components.domains.music_monster.models.enum.rss_news import RSSNewsSource
from shared_components.domains.music_monster.utilities.cdn import get_media_cdn_url
from shared_components.services.aws.aws_client import AWSClient
from shared_components.utilities.design_patterns.singleton_registry import Si

MOBILE_IMAGE_SIZE = (144, 144)
DEFAULT_BBC_NEWS_S3_KEY = "rss_news_resized_images/default_bbc_news.jpg"
DEFAULT_YAHOO_NEWS_S3_KEY = "rss_news_resized_images/default_yahoo_news.jpg"


async def download_resize_and_upload_image(image_url: str) -> str | None:
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail(MOBILE_IMAGE_SIZE, Image.Resampling.LANCZOS)
        file_id = uuid.uuid4()
        s3_key = f"rss_news_resized_images/{file_id}.jpg"
        in_mem_file = BytesIO()
        img.save(in_mem_file, format="JPEG")
        in_mem_file.seek(0)
        await Si(AWSClient).s3_upload_file(in_mem_file, s3_key)
        return get_media_cdn_url(s3_key)
    except Exception as e:
        logging.error(f"Error when download_resize_and_upload_image: {e}. Use default image.")
        return None


def get_default_image_url(source_id: int) -> str | None:
    if source_id == RSSNewsSource.BBC:
        return get_media_cdn_url(DEFAULT_BBC_NEWS_S3_KEY)
    elif source_id == RSSNewsSource.YAHOO:
        return get_media_cdn_url(DEFAULT_YAHOO_NEWS_S3_KEY)
    return None
