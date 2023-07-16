import sys
from contextlib import contextmanager

from . import *

# -------------------------------------------------------------------------------------------------|
# Ignore import errors inside BrokenImports context, replace the module with BrokenImportError class
#
# Usage:
# | while True:
# |     with BrokenImports():
# |         import A
# |         import B
# |         import C
# |         break


class BrokenImportError:
    LAST_ERROR = None
    ...

@contextmanager
def BrokenImports():
    try:
        yield
    except (ModuleNotFoundError, ImportError) as error:

        # ERROR: Same error as last time, raise it (import loop?)
        if BrokenImportError.LAST_ERROR == str(error):
            raise error

        # Save last error (see above)
        BrokenImportError.LAST_ERROR = str(error)

        # Module and its spec import error class
        import_error = BrokenImportError()

        # Patch system.modules for no re-importing
        sys.modules[error.name] = import_error

        # "spec is not None" -> make it something, might break stuff
        sys.modules[error.name].__spec__ = import_error

        # Make it available on local globals() else name not found
        globals()[error.name] = import_error

    except Exception as error:
        raise error

# -------------------------------------------------------------------------------------------------|

while True:
    with BrokenImports():
        import configparser
        import ctypes
        import datetime
        import hashlib
        import importlib
        import inspect
        import itertools
        import json
        import operator
        import os
        import platform
        import random
        import re
        import shutil
        import subprocess
        import tempfile
        import warnings
        import zipfile
        from abc import ABC
        from abc import abstractmethod
        from contextlib import suppress
        from copy import deepcopy
        from dataclasses import dataclass
        from enum import Enum
        from functools import lru_cache
        from functools import wraps
        from io import BytesIO
        from math import *
        from os import PathLike
        from pathlib import Path
        from shutil import which as find_binary
        from subprocess import DEVNULL
        from subprocess import PIPE
        from subprocess import Popen
        from subprocess import check_output
        from subprocess import run
        from sys import argv
        from threading import Thread
        from time import sleep
        from time import time as now
        from typing import Any
        from typing import Dict
        from typing import Iterable
        from typing import List
        from typing import Tuple
        from typing import Union
        from uuid import uuid4 as uuid

        import aenum
        import arrow
        import diffusers
        import distro
        import forbiddenfruit
        import gradio
        import halo
        import intervaltree
        import loguru
        import moderngl
        import numpy
        import openai
        import PIL
        import PIL.Image
        import requests
        import requests_cache
        import rich
        import rich.prompt
        import schedule
        import toml
        import torch
        import transformers
        import typer
        import yaml
        from appdirs import AppDirs
        from dotmap import DotMap
        from tqdm import tqdm

        break

# -------------------------------------------------------------------------------------------------|

def BrokenNeedImport(*packages: Union[str, List[str]]):
    """Check if a package is imported (required for project), else exit with error"""
    for name in packages:
        if isinstance(sys.modules[name], BrokenImportError):
            error(f"• Dependency {name} is required for this project")
            exit(1)

# -------------------------------------------------------------------------------------------------|

# # Custom types, some Rust inspiration

# PIL.Image is a module, PIL.Image.Image is the class
PilImage  = PIL.Image.Image

# Stuff that accepts "anything that can be converted to X"
URL       = str

# def divide(a, b) -> Option[float, ZeroDivisionError]:
Option = Union
Self   = Any
