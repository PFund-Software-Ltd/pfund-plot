import click
import subprocess
import sys


@click.command(
    add_help_option=False,
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.pass_context
def serve(ctx):
    """Serve a Panel application.

    Passes all arguments directly to 'panel serve'.
    """
    result = subprocess.run(['panel', 'serve', *ctx.args], check=False)
    sys.exit(result.returncode)
