import os
import sys
import typing
from pathlib import Path

import pretty_errors

pretty_errors.configure(
    filename_display  = pretty_errors.FILENAME_EXTENDED,
    line_color        = pretty_errors.RED + "> \033[1;37m",
    code_color        = '  \033[1;37m',
    line_number_first = True,
    lines_before      = 10,
    lines_after       = 10,
)

# https://github.com/numpy/numpy/issues/18669#issuecomment-820510379
os.environ["OMP_NUM_THREADS"] = "1"

# https://forums.developer.nvidia.com/t/glxswapbuffers-gobbling-up-a-full-cpu-core-when-vsync-is-off/156635
# https://forums.developer.nvidia.com/t/gl-yield-and-performance-issues/27736
# High CPU usage on glfw.swap_buffers when vsync is off and the GPU is wayy behind own vblank
os.environ["__GL_YIELD"] = "USLEEP"

# Keep repository clean of __pycache__ and .pyc files by writing to .venv
if (_venv := Path(__file__).parent.parent/".venv").exists():
    sys.pycache_prefix = str(_venv/"pycache")

# Fix: typing.Self was implemented on Python >= 3.11
if sys.version_info < (3, 11):
    typing.Self = typing.Any

# PyAPP isn't passing the argument on Linux
if bool(os.environ.get("PYAPP", False)) and (os.name != "nt"):
    sys.argv.insert(0, sys.executable)

# As a safety measure, make all relative and strings with suffix ok paths absolute. We might run
# binaries from other cwd, so make sure to always use non-ambiguous absolute paths if found
# • File name collisions are unlikely with any Monorepo path (?)
for _index, _arg in enumerate(sys.argv):
    if any((
        any((_arg.startswith(x) for x in ("./", "../", ".\\", "..\\"))),
        bool(Path(_arg).suffix) and Path(_arg).exists(),
    )):
        sys.argv[_index] = str(Path(_arg).expanduser().resolve())

# Safer measures: Store the first cwd that Broken is run, always start from there
os.chdir(os.environ.setdefault("BROKEN_PREVIOUS_WORKING_DIRECTORY", os.getcwd()))

# -------------------------------------------------------------------------------------------------|

import importlib.metadata
import importlib.resources

# Information about the release and version
PYINSTALLER: bool = bool(getattr(sys, "frozen", False))
PYAPP:       bool = bool(os.environ.get("PYAPP", False))
NUITKA:      bool = ("__compiled__" in globals())
PYPI:        bool = ("site-packages" in __file__.lower())
RELEASE:     bool = (NUITKA or PYINSTALLER or PYAPP or PYPI)
DEVELOPMENT: bool = (not RELEASE)
VERSION:     str  = importlib.metadata.version("broken-source")

import Broken.Resources as BrokenResources
from Broken.Core import (
    BIG_BANG,
    apply,
    clamp,
    denum,
    dunder,
    extend,
    flatten,
    have_import,
    image_hash,
    last_locals,
    nearest,
    shell,
)
from Broken.Core.BrokenEnum import BrokenEnum
from Broken.Core.BrokenLogging import BrokenLogging
from Broken.Core.BrokenPath import BrokenPath
from Broken.Core.BrokenPlatform import BrokenPlatform
from Broken.Core.BrokenProfiler import BrokenProfiler, BrokenProfilerEnum
from Broken.Core.BrokenProject import BrokenApp, BrokenProject
from Broken.Core.BrokenResolution import BrokenResolution
from Broken.Core.BrokenScheduler import BrokenScheduler, BrokenTask
from Broken.Core.BrokenSpinner import BrokenSpinner
from Broken.Core.BrokenThread import BrokenThread, BrokenThreadPool
from Broken.Core.BrokenTorch import BrokenTorch, TorchFlavor
from Broken.Core.BrokenTyper import BrokenTyper
from Broken.Core.BrokenUtils import (
    BrokenAttrs,
    BrokenFluentBuilder,
    BrokenRelay,
    BrokenSingleton,
    BrokenWatchdog,
    Ignore,
    SameTracker,
)

BROKEN = BrokenProject(
    PACKAGE=__file__,
    APP_NAME="Broken",
    APP_AUTHOR="BrokenSource",
    RESOURCES=BrokenResources,
)

PROJECT = BROKEN
"""
The Broken.PROJECT variable points to the first project set on Broken.set_project, else BROKEN.
It is useful to use current project pathing and resources on common parts of the code
"""

def set_project(project: BrokenProject):
    global PROJECT
    if not isinstance(project, BrokenProject):
        raise TypeError(f"Project must be an instance of BrokenProject, not {type(project)}")
    if PROJECT is not BROKEN:
        return
    PROJECT = project
