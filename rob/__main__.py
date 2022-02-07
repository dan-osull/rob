from rob.cli import cli
from rob.console import print_

if __name__ == "__main__":
    # Entry point for application
    cli()  # pylint: disable=no-value-for-parameter
    # TODO: should we try to clean up library and filesystem if left in an inconsistent state?
    print_("")
