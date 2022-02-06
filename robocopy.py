import os
import subprocess
from dataclasses import dataclass
from pathlib import WindowsPath
from time import sleep
from typing import Optional, Sequence

from click import ClickException
from rich.progress import Progress

import console as con
import filesystem


@dataclass
class RobocopyResults:
    options: list[str]
    # Using Sequence because "list" and other mutable container types are
    # considered "invariant", so the contained type needs to match exactly.
    # https://github.com/microsoft/pyright/issues/130
    errors: Sequence[Optional[str]]
    stats: Sequence[Optional[str]]


def parse_robocopy_output(
    output: str,
) -> RobocopyResults:
    output_list = output.split("\n")
    output_list = [line for line in output_list if line]
    divider_idx = []
    for index, line in enumerate(output_list):
        # 50 chars long. Finds dividers in output, which are 78/79 chars.
        if "--------------------------------------------------" in line:
            divider_idx.append(index)

    options = output_list[divider_idx[1] + 1 : divider_idx[2]]
    if len(divider_idx) == 3:
        errors = output_list[divider_idx[2] + 1 :]
        stats = []
    else:
        errors = output_list[divider_idx[2] + 1 : divider_idx[3]]
        stats = output_list[divider_idx[3] + 1 :]

    return RobocopyResults(
        options=options,
        errors=errors,
        stats=stats,
    )


def run_robocopy(
    source: WindowsPath,
    target: WindowsPath,
    dir_size_bytes: Optional[int] = None,
    dry_run: bool = False,
    copy_permissions: bool = False,
    quiet=False,
) -> None:
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
            # /COPY flags: D=Data, A=Attributes, T=Timestamps, X=Skip alt data streams,
            # S=Security=NTFS ACLs, O=Owner info, U=aUditing info
            "/COPY:DATSO"
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
                # Don't display 100% while final transfers complete
                total = dir_size_bytes / 100 * 95
                task_id = progress.add_task(
                    "[green]Copying data...[/green]", total=total
                )
                progress.update(task_id, completed=filesystem.get_dir_size(target))
                progress.refresh()
                sleep(2)

    output = proc.stdout.read()  # type: ignore
    # Exit code cannot be trusted as, for example, this error:
    # ERROR 5 (0x00000005) Copying NTFS Security to Destination Directory
    # ...can be present despite returncode 0, so let's look for errors ourselves
    robocopy_results = parse_robocopy_output(output)
    if robocopy_results.errors:
        raise ClickException(f"Robocopy: {str(robocopy_results.errors)}")

    if dir_size_bytes != filesystem.get_dir_size(target):
        raise ClickException("Source and target folder sizes do not match. Aborting.")

    if not quiet:
        con.print_("[green]Data copy complete[/green]")
