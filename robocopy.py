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
    source_size_bytes: int,
    dry_run: bool = False,
    copy_permissions: bool = False,
):
    msg = f"Copying data from {con.style_path(source)} to {con.style_path(target)}"
    if target.exists():
        con.print_(msg)
        raise ClickException("{target} already exists")
    if dry_run:
        con.print_(msg, end="")
        con.print_skipped()
        return
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
    with Progress(auto_refresh=False, transient=True) as progress:
        task_id = progress.add_task(
            "[green]Copying data...[/green]", total=source_size_bytes
        )
        while proc.poll() is None:
            # "is None" so that returncode 0 breaks loop
            progress.update(task_id, completed=filesystem.get_dir_size(target))
            progress.refresh()
            sleep(5)

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
            # Get ERROR and all following lines
            error = output[output.index(error_line) :]
        else:
            error = None
        raise ClickException(f"Robocopy: {error}")

    con.print_("[green]Data copy complete[/green]")
