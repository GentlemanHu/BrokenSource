import io
from pathlib import Path
from typing import Any, Optional, Union

import numpy
import PIL
import validators
from attr import define
from loguru import logger as log
from PIL.Image import Image

import Broken
from Broken.Loaders import BrokenLoader
from Broken.Types import URL


@define
class LoaderImage(BrokenLoader):
    _cache = None

    @staticmethod
    def cache() -> Any:
        try:
            import requests_cache
            if not LoaderImage._cache:
                LoaderImage._cache = requests_cache.CachedSession(
                    Broken.BROKEN.DIRECTORIES.CACHE/"LoaderImage.sqlite",
                )
        except ImportError:
            return None

        return LoaderImage._cache

    @staticmethod
    def load(value: Any=None, **kwargs) -> Optional[Image]:

        if value is None:
            return None

        elif isinstance(value, Image):
            log.debug("Loading already an Instance of Image")
            return value

        elif value is Image:
            log.debug("Loading already an Class of Image")
            return value

        elif isinstance(value, numpy.ndarray):
            log.debug("Loading Image from Numpy Array")
            return PIL.Image.fromarray(value, **kwargs)

        elif (path := Path(value)).exists():
            log.debug(f"Loading Image from Path ({path})")
            return PIL.Image.open(path, **kwargs)

        elif validators.url(value):
            log.debug(f"Loading Image from URL ({value})")

            if LoaderImage.cache():
                return PIL.Image.open(io.BytesIO(LoaderImage.cache().get(value).content), **kwargs)

            import requests
            return PIL.Image.open(io.BytesIO(requests.get(value).content), **kwargs)

        elif isinstance(value, bytes):
            log.debug("Loading Image from Bytes")
            return PIL.Image.open(io.BytesIO(value), **kwargs)

        return None

LoadableImage = Union[Image, Path, URL, numpy.ndarray, bytes, None]
