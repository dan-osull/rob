import os
import subprocess
from pathlib import WindowsPath
from time import sleep

from click import ClickException
from rich.progress import Progress

import console as con
import filesystem


def run_robocopy(
    source: WindowsPath,
    target: WindowsPath,
    dir_size_bytes: int = None,
    dry_run: bool = False,
    copy_permissions: bool = False,
    quiet=False,
):
    msg = f"Copying data from {con.style_path(source)} to {con.style_path(target)}"
    if not dir_size_bytes:
        dir_size_bytes = filesystem.get_dir_size(source)
    if target.exists():
        con.print_(msg)
        raise ClickException("{target} already exists")
    if dry_run:
        con.print_(msg, end="")
        con.print_skipped()
        return
    if not quiet:
        con.print_(msg)

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
    if copy_permissions:
        robocopy_args.append(
            "/SEC"  # copy files with SECurity (equivalent to /COPY:DATS) (S=Security=NTFS ACLs)
        )

    proc = subprocess.Popen(
        args=robocopy_args,
        stdout=subprocess.PIPE,
        # stderr included for completeness, robocopy doesn't seem to use it
        stderr=subprocess.STDOUT,
        text=True,
    )
    while proc.poll() is None:
        # "is None" so that returncode 0 breaks loop
        # 0: No errors occurred, and no copying was done.
        #    The source and destination directory trees are completely synchronized.
        # 1: One or more files were copied successfully (that is, new files have arrived).
        # https://ss64.com/nt/robocopy-exit.html
        if not quiet:
            with Progress(auto_refresh=False, transient=True) as progress:
                task_id = progress.add_task(
                    "[green]Copying data...[/green]", total=dir_size_bytes
                )
                progress.update(task_id, completed=filesystem.get_dir_size(target))
                progress.refresh()
                sleep(5)

    output = proc.stdout.read()  # type: ignore
    output = output.split("\n")
    output = [line for line in output if line]
    # Exit code cannot be trusted as, for example, this error:
    # ERROR 5 (0x00000005) Copying NTFS Security to Destination Directory
    # can be present despite returncode 0, so let's look for the error ourselves
    # Looking for " (0x000" in case there's a folder called ERROR!
    error_line = next(
        (line for line in output if " ERROR " in line and " (0x000" in line), None
    )
    if error_line:
        # Get ERROR and all following lines
        error = output[output.index(error_line) :]
        raise ClickException(f"Robocopy: {str(error)}")

    if not dir_size_bytes == 0 and filesystem.get_dir_size(target) == 0:
        # Source was not empty but target is empty
        raise ClickException("Target folder is empty after data copy. Aborting.")

    if not quiet:
        con.print_("[green]Data copy complete[/green]")
