import os
import subprocess
from pathlib import WindowsPath
from time import sleep

from click import ClickException
from rich.progress import Progress

from console import print_, style_path


def get_tree_size(path: WindowsPath) -> int:
    """Return total size of files in given path and subdirs."""
    # https://www.python.org/dev/peps/pep-0471/
    if not WindowsPath(path).exists():
        # Avoid race with file creation
        return 0
    total = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)  # type: ignore
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total


def run_robocopy(source: WindowsPath, target: WindowsPath):
    print_(f"Copying data from {style_path(source)} to {style_path(target)}")
    source_size_bytes = get_tree_size(source)

    robocopy_exe = (
        WindowsPath(os.environ["SystemRoot"])
        .joinpath("system32/robocopy.exe")
        .resolve()
    )
    robocopy_args = [
        str(robocopy_exe),
        str(source),
        str(target),
        "/E",  # copy subdirectories, including Empty ones.
        "/MT",  # Do multi-threaded copies with n threads (default 8).
        "/R:0",  # number of Retries on failed copies: default 1 million.
        "/NDL",  # No Directory List - don't log directory names.
        "/NFL",  # No File List - don't log file names.
        "/NP",  # No Progress - don't display percentage copied.
    ]
    if target.exists():
        raise ClickException("{target} already exists")

    proc = subprocess.Popen(
        executable=robocopy_exe,
        args=robocopy_args,
        stdout=subprocess.PIPE,
        # stderr included for completeness, robocopy doesn't seem to use it
        stderr=subprocess.STDOUT,
        text=True,
    )
    with Progress(auto_refresh=False, transient=True) as progress:
        copy_progress = progress.add_task(
            "[green]Copying data...", total=source_size_bytes
        )
        while proc.poll() is None:
            # == None so that returncode 0 breaks loop
            progress.update(copy_progress, completed=get_tree_size(target))
            progress.refresh()
            sleep(2)

    if proc.returncode not in [0, 1]:
        # 0: No errors occurred, and no copying was done.
        #    The source and destination directory trees are completely synchronized.
        # 1: One or more files were copied successfully (that is, new files have arrived).
        # https://ss64.com/nt/robocopy-exit.html
        output = proc.stdout.read()  # type: ignore
        output = output.split("\n")
        output = [line for line in output if line]
        error_line = next((line for line in output if "ERROR" in line), None)
        if error_line:
            # Get all lines that appear after ERROR
            error = output[output.index(error_line) :]
        else:
            error = None
        raise ClickException(f"Robocopy: {error}")
