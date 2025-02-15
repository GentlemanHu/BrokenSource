from __future__ import annotations

import contextlib
import hashlib
import os
import pathlib
import shutil
import sys
from pathlib import Path
from typing import Generator, List, Optional, Union

import click
import tqdm
import validators
from loguru import logger as log

import Broken
from Broken import apply, denum, flatten, shell
from Broken.Core.BrokenEnum import BrokenEnum
from Broken.Core.BrokenPlatform import BrokenPlatform
from Broken.Core.BrokenSpinner import BrokenSpinner
from Broken.Types import FileExtensions


class ShutilFormat(BrokenEnum):
    Zip   = "zip"
    Tar   = "tar"
    GzTar = "tar.gz"
    BzTar = "tar.bz2"
    XzTar = "tar.xz"

class BrokenPath(pathlib.Path):
    """
    Extended pathlib.BrokenPath with utilities and always use absolute expanded user paths.

    - Clever mechanism: Functions aren't staticmethods but still can be called from the outside,
        they just imply self. For example: Both BrokenPath("/tmp").valid() or BrokenPath.valid("/tmp") works

    - Convenience: Can use BrokenPath(None), BrokenPath("/ok/stuff", None, "file.mp4")
    """
    _flavour = type(pathlib.Path())._flavour

    def __new__(cls, *args, **kwargs):

        # Return None if all args are falsy
        if not (args := list(filter(None, args))):
            return None

        # Use absolute expanded user always. Note that we do not want
        # to .resolve() as having symlink paths _can_ be wanted
        instance = super().__new__(cls, *args, **kwargs)
        return instance.expanduser().absolute()

    def pathlib(self) -> pathlib.Path:
        """Some packages test `var == pathlib.Path` instead of `isinstance(var, pathlib.Path)`"""
        return pathlib.Path(self)

    def str(self) -> str:
        return str(self)

    def valid(path: BrokenPath) -> Optional[BrokenPath]:
        """Returns the BrokenPath if it exists, else None"""
        if (path := BrokenPath(path)) is None:
            return None
        if path.exists():
            return path
        return None

    @staticmethod
    def copy(src: Path, dst: Path, *, echo=True) -> Path:
        src, dst = BrokenPath(src, dst)
        BrokenPath.mkdirs(dst.parent, echo=False)
        if src.is_dir():
            log.info(f"Copying Directory ({src})\n → ({dst})", echo=echo)
            shutil.copytree(src, dst)
        else:
            log.info(f"Copying File ({src})\n → ({dst})", echo=echo)
            shutil.copy2(src, dst)
        return dst

    @staticmethod
    def move(src: Path, dst: Path, *, echo=True) -> Path:
        src, dst = BrokenPath(src, dst)
        log.info(f"Moving ({src})\n → ({dst})", echo=echo)
        shutil.move(src, dst)
        return dst

    @staticmethod
    def remove(path: Path, *, confirm=False, echo=True) -> Path:

        # Already removed or doesn't exist
        if not (path := BrokenPath(path).valid()):
            return path

        log.info(f"Removing Path ({path})", echo=echo)

        # Safety: Must not be common
        if path in (Path.cwd(), Path.home()):
            log.error(f"Avoided catastrophic failure by not removing ({path})")
            exit(1)

        # Symlinks are safe to remove
        if path.is_symlink():
            path.unlink()
            return path

        # Confirm removal: directory contains data
        if confirm and (not click.confirm(f"• Confirm removing path ({path})")):
            return path

        # Remove the path
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink()

        return path

    def touch(path: Path, *, echo=True) -> Path:
        """Creates a file, fail safe™"""
        if (path := BrokenPath(path)).exists():
            log.success(f"File ({path}) already touched", echo=echo)
            return
        log.info(f"Touching file {path}", echo=echo)
        path.touch()
        return path

    def mkdirs(path: Path, parent: bool=False, *, echo=True) -> Path:
        """Creates a directory and its parents, fail safe™"""
        path = BrokenPath(path)
        path = path.parent if parent else path
        if path.exists():
            log.success(f"Directory ({path}) already exists", echo=echo)
            return path
        log.info(f"Creating directory {path}", echo=echo)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resetdir(path: Path, *, echo=True) -> Path:
        """Creates a directory and its parents, fail safe™"""
        BrokenPath.remove(path, echo=echo)
        return BrokenPath.mkdirs(path, echo=echo)

    @contextlib.contextmanager
    def pushd(path: Path, *, echo: bool=True) -> Generator[Path, None, None]:
        """Change directory, then change back when done"""
        path = BrokenPath(path)
        cwd = os.getcwd()
        log.info(f"Pushd ({path})", echo=echo)
        os.chdir(path)
        yield path
        log.info(f"Popd  ({path})", echo=echo)
        os.chdir(cwd)

    @staticmethod
    def symlink(virtual: Path, real: Path, *, echo: bool=True) -> Path:
        """
        Symlink [virtual] -> [real], `virtual` being the symlink file and `real` the target

        Args:
            virtual (Path): Symlink path (file)
            real (Path): Target path (real path)

        Returns:
            None if it fails, else `virtual` Path
        """
        log.info(f"Symlinking ({virtual})\n → ({real})", echo=echo)

        # Return if already symlinked
        if (BrokenPath(virtual) == BrokenPath(real)):
            return virtual

        # Make Virtual's parent directory
        BrokenPath.mkdirs(virtual.parent, echo=False)

        # Remove old symlink if it points to a non existing directory
        if virtual.is_symlink() and (not virtual.resolve().exists()):
            virtual.unlink()

        # Virtual doesn't exist, ok to create
        elif not virtual.exists():
            pass

        # File exists and is a symlink - safe to remove
        elif virtual.is_symlink():
            virtual.unlink()

        # Virtual is a directory and not empty
        elif virtual.is_dir() and (not os.listdir(virtual)):
            BrokenPath.remove(virtual, echo=False)

        else:
            if click.confirm(f"• Path ({virtual}) exists, but Broken wants to create a symlink to ({real})\nConfirm removing the 'virtual' path and continuing? (It might contain data or be a important symlink)"):
                BrokenPath.remove(virtual, echo=False)
            else:
                return

        # Actually symlink
        virtual.symlink_to(real)
        return virtual

    def make_executable(path: Path, *, echo=False) -> Path:
        """Make a file executable"""
        path = BrokenPath(path)
        if BrokenPlatform.OnUnix:
            shell("chmod", "+x", path, echo=echo)
        elif BrokenPlatform.OnWindows:
            shell("attrib", "+x", path, echo=echo)
        return path

    def zip(path: Path, output: Path=None, *, format: ShutilFormat=ShutilFormat.Zip, echo: bool=True) -> Path:
        format = ShutilFormat(format)
        output = BrokenPath(output or path).with_suffix(f".{format}")
        path   = BrokenPath(path)
        BrokenPath.remove(output, echo=echo)
        log.info(f"Zipping ({path})\n → ({output})", echo=echo)
        shutil.make_archive(output.with_suffix(""), format, path)
        return output

    def stem(path: Path) -> str:
        """
        Get the "true stem" of a path, as pathlib's only gets the last dot one
        • "/path/with/many.ext.ens.ions" -> "many" instead of "many.ext.ens"
        """
        stem = Path(Path(path).stem)
        while (stem := Path(stem).with_suffix("")).suffix:
            continue
        return str(stem)

    def sha256sum(data: Union[Path, str, bytes]) -> Optional[str]:
        """Get the sha256sum of a file, directory or bytes"""

        # Nibble the bytes !
        if isinstance(data, bytes):
            return hashlib.sha256(data).hexdigest()

        # String or Path is a valid path
        elif (path := BrokenPath(data).valid()):
            with BrokenSpinner(log.info(f"Calculating sha256sum of ({path})")):
                if path.is_file():
                    return hashlib.sha256(path.read_bytes()).hexdigest()

                # Iterate on all files for low memory footprint
                feed = hashlib.sha256()
                for file in path.rglob("*"):
                    if not file.is_file():
                        continue
                    with open(file, "rb") as file:
                        while (chunk := file.read(8192)):
                            feed.update(chunk)
                return feed.hexdigest()

        elif isinstance(data, str):
            return hashlib.sha256(data.encode("utf-8")).hexdigest()

        return

    def extract(
        path: Path,
        output: Path=None,
        *,
        overwrite: bool=False,
        PATH: bool=False,
        echo: bool=True
    ) -> Path:
        path, output = BrokenPath(path), BrokenPath(output)

        # Output is input without suffix if not given
        if (output is None):
            output = path.parent/BrokenPath.stem(path)

        # Add stem to the output as some archives might be flat
        output /= BrokenPath.stem(path)

        # Re-extract on order
        if overwrite:
            BrokenPath.remove(output)

        # A file to skip if it exists, created after successful extraction
        if (extract_flag := (output/"BrokenPath.extract.ok")).exists():
            log.minor(f"Already extracted ({output})", echo=echo)
            if PATH: BrokenPath.add_to_path(path=output, recursively=True, echo=echo)
            return output

        # Show progress as this might take a while on slower IOs
        log.info(f"Extracting ({path})\n → ({output})", echo=echo)
        with BrokenSpinner("Extracting archive.."):
            shutil.unpack_archive(path, output)

        extract_flag.touch()
        if PATH: BrokenPath.add_to_path(path=output, recursively=True, echo=echo)
        return output/BrokenPath.stem(path)

    def download(
        url: str,
        output: Path=None,
        *,
        size_check: bool=True,
        chunk: int=1024,
        echo: bool=True
    ) -> Optional[Path]:

        # Link must be valid
        if not validators.url(url):
            log.error(f"The string ({url}) doesn't look like a valid URL", echo=echo)
            return

        import requests

        # Default to Broken's Download directory
        if (output is None):
            output = Broken.BROKEN.DIRECTORIES.DOWNLOADS

        # Append url's file name to the output path
        if (output := BrokenPath(output)).is_dir():
            output /= Path(url.split("#")[0].split("?")[0].split("/")[-1])

        # Without size check, the existence of the file is enough
        if output.exists() and (not size_check):
            log.info(f"Already Downloaded ({output})", echo=echo)
            log.minor("• Size check was skipped, the file might be incomplete", echo=echo)
            return

        # Send the GET request, we might be offline!
        try:
            response = requests.get(url, stream=True)
        except requests.exceptions.RequestException as error:
            log.error(f"Failed to download file ({url}) → ({output}): {error}", echo=echo)
            return output

        size = int(response.headers.get('content-length', 0))

        # The file might already be (partially) downloaded
        if output.exists():
            A, B = (output.stat().st_size, size)
            if (A == B):
                log.info(f"Already Downloaded ({output})", echo=echo)
                return output
            else:
                log.warning(f"Wrong Download at ({output})", echo=echo)

        log.info(f"Downloading file at ({url}):", echo=echo)
        log.info(f"• Output: ({output})", echo=echo)

        # It is binary prefix, right? kibi, mebi, gibi, etc. as we're dealing with raw bytes
        with open(output, "wb") as file, tqdm.tqdm(
            desc=f"Downloading ({output.name})",
            total=size, unit="iB", unit_scale=True, unit_divisor=1024,
            mininterval=1/30, maxinterval=0.5, leave=False
        ) as progress:
            for data in response.iter_content(chunk_size=chunk):
                progress.update(file.write(data))

        # Url was invalid
        if (response.status_code != 200):
            log.error(f"Failed to Download File at ({url}):", echo=echo)
            log.error(f"• HTTP Error: {response.status_code}", echo=echo)
            return

        # Wrong downloaded and expected size
        elif (output.stat().st_size != size):
            log.error(f"File ({output}) was not downloaded correctly", echo=echo)
            return

        log.success(f"Downloaded file ({output}) from ({url})", echo=echo)
        return output

    @staticmethod
    def get_external(url: str, *, subdir: str="", echo: bool=True) -> Path:
        file = BrokenPath.download(denum(url), echo=echo)

        # File is a Archive, extract
        if any((str(file).endswith(ext) for ext in ShutilFormat.values)):
            directory = Broken.BROKEN.DIRECTORIES.EXTERNAL_ARCHIVES
            return BrokenPath.extract(file, directory, PATH=True, echo=echo)

        # File is some known type, move to their own external directory
        if bool(subdir):
            directory = Broken.BROKEN.DIRECTORIES.EXTERNALS/subdir
        elif file.suffix in FileExtensions.Audio:
            directory = Broken.BROKEN.DIRECTORIES.EXTERNAL_AUDIO
        elif file.suffix in FileExtensions.Image:
            directory = Broken.BROKEN.DIRECTORIES.EXTERNAL_IMAGES
        elif file.suffix in FileExtensions.Font:
            directory = Broken.BROKEN.DIRECTORIES.EXTERNAL_FONTS
        elif file.suffix in FileExtensions.Soundfont:
            directory = Broken.BROKEN.DIRECTORIES.EXTERNAL_SOUNDFONTS
        elif file.suffix in FileExtensions.Midi:
            directory = Broken.BROKEN.DIRECTORIES.EXTERNAL_MIDIS
        else:
            directory = Broken.BROKEN.DIRECTORIES.EXTERNALS
        return BrokenPath.move(file, directory/subdir, echo=echo)

    @staticmethod
    def which(name: str) -> Optional[Path]:
        BrokenPath.update_externals_path()
        return BrokenPath(shutil.which(name))

    @staticmethod
    def update_externals_path(path: Path=None, *, echo: bool=True) -> Optional[Path]:
        path = path or Broken.BROKEN.DIRECTORIES.EXTERNALS
        return BrokenPath.add_to_path(path, recursively=True, echo=echo)

    @staticmethod
    def on_path(path: Path) -> bool:
        """Check if a path is on PATH, works with symlinks"""
        return BrokenPath(path) in map(BrokenPath, os.environ.get("PATH", "").split(os.pathsep))

    @staticmethod
    def add_to_path(
        path: Path,
        *,
        recursively: bool=False,
        persistent: bool=False,
        preferential: bool=True,
        echo: bool=True
    ) -> Path:
        """
        Add a path, recursively or not, to System's Path or this Python process's Path

        Args:
            recursively: Also add all subdirectories of the given path
            persistent: Use 'userpath' package to add to the Shell's or Registry PATH
            preferential: Prepends the path for less priority on system binaries

        Returns:
            The Path argument itself
        """
        path = BrokenPath(path)

        # Can't recurse on file or non existing directories
        if (not path.exists()) and path.is_file() and recursively:
            log.warning(f"Can't add non existing path or file recursively to Path ({path})", echo=echo)
            return path

        log.debug(f"Adding to Path (Recursively: {recursively}, Persistent: {persistent}): ({path})", echo=echo)

        for other in (path.rglob("*") if recursively else [path]):
            if other.is_file():
                continue
            if BrokenPath.on_path(other):
                continue
            if persistent:
                import userpath
                userpath.append(str(other))
            else:
                if preferential:
                    os.environ["PATH"] = (str(other)+os.pathsep+os.environ["PATH"])
                    sys.path.insert(0, str(other))
                else:
                    os.environ["PATH"] = (os.environ["PATH"]+os.pathsep+str(other))
                    sys.path.append(str(other))
        return path

    # # Specific / "Utils"

    @staticmethod
    def open_in_file_explorer(path: Path):
        """Opens a path in the file explorer"""
        path = BrokenPath(path)
        if BrokenPlatform.OnWindows:
            os.startfile(str(path))
        elif BrokenPlatform.OnLinux:
            shell("xdg-open", path)
        elif BrokenPlatform.OnMacOS:
            shell("open", path)

    # Fixme: Untested functions, needs better name; are these useful?

    @staticmethod
    def non_empty_file(path: Path) -> bool:
        return path.exists() and path.is_file() and path.stat().st_size > 0

    @staticmethod
    def empty_file(path: Path, create: bool=True) -> bool:
        if create and not path.exists():
            path.parent.mkdirs(parents=True, exist_ok=True)
            path.touch()
        return path.exists() and path.is_file() and len(path.read_text()) == 0

    @contextlib.contextmanager
    def PATH(*,
        directories: List[Path],
        recursive: bool=True,
        prepend: bool=True,
        clean: bool=False,
        restore: bool=True,
    ):
        """
        Temporarily limits the PATH to given directories
        - directories: List of directories to add to PATH
        - recursive: Whether to add subdirectories of given directories to PATH
        - prepend: Prioritize binaries found in input directories
        - restricted: Do not include current PATH in the new PATH
        """

        # Make Path objects
        directories = apply(Path, flatten(directories))

        # Get current PATH
        old = os.environ["PATH"]

        # List of all directories in PATH
        PATH = [] if clean else os.environ["PATH"].split(os.pathsep)

        # Add directories to PATH
        for directory in directories:
            PATH.append(directory)

            # Do not recurse if so
            if not recursive:
                continue

            # WARN: This could be slow on too many directories (wrong input?)
            # Find all subdirectories of a path
            for path in directory.rglob("*"):
                if path.is_dir():
                    if prepend:
                        PATH.insert(0, path)
                    else:
                        PATH.append(path)

        # Set new PATH
        os.environ["PATH"] = os.pathsep.join(map(str, PATH))

        yield os.environ["PATH"]

        # Restore PATH
        os.environ["PATH"] = old