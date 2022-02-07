from click import secho


def echo_red_error(message, *args, **kwargs):
    """Patch for `click.exceptions.echo`"""
    if str(message).startswith("Error: "):
        return secho(message, *args, **kwargs, fg="red")
    return secho(message, *args, **kwargs)
