import os
import tempfile
from pathlib import Path
from typing import Any, Self

from attrs import define
from loguru import logger as log

from Broken import BrokenEnum, shell


class BrokenProfilerEnum(BrokenEnum):
    """List of profilers"""
    cprofile      = "cprofile"
    # imports       = "imports"
    # pyinstrument  = "pyinstrument"

@define
class BrokenProfiler:
    name: str = "NONE"
    profiler: BrokenProfilerEnum = BrokenProfilerEnum.cprofile

    def __attrs_post_init__(self):
        profiler = os.environ.get(f"{self.name}_PROFILER", self.profiler)
        self.profiler = BrokenProfilerEnum.get(profiler)

    # Base properties

    @property
    def enabled(self) -> bool:
        return os.environ.get(f"{self.name}_PROFILE", "0") == "1"

    @property
    def output(self) -> Path:
        return Path(tempfile.gettempdir())/f"{self.name}.prof"

    # The actual profiler object
    __profiler__: Any = None

    def __enter__(self) -> Self:
        if not self.enabled:
            return self

        match self.profiler:
            case BrokenProfilerEnum.cprofile:
                log.trace("Profiling with cProfile")
                import cProfile
                self.__profiler__ = cProfile.Profile()
                self.__profiler__.enable()
                return self

    def __exit__(self, *args) -> None:
        if not self.enabled:
            return

        match self.profiler:
            case BrokenProfilerEnum.cprofile:
                log.trace("Finishing cProfile")
                output = self.output.with_suffix(".prof")
                self.__profiler__.disable()
                self.__profiler__.dump_stats(output)
                shell("snakeviz", output)
                return
