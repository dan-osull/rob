from config import PROJECT_NAME


def style_project_name() -> str:
    # https://rich.readthedocs.io/en/stable/appendix/colors.html#appendix-colors
    return f"[purple]{PROJECT_NAME}[/purple]"
