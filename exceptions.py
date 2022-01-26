from gettext import gettext

from click import secho


def show_red_error(self, file=None) -> None:
    """Monkey patch for click.exceptions.ClickException.show"""
    secho(gettext("Error: {message}").format(message=self.format_message()), fg="red")
