import click
from trogon import tui

# from pfund_plot.cli.commands.PLACEHOLDER import ...


@tui(command='tui', help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option()
def pfund_plot_group(ctx):
    """PFundPlot's CLI"""
    ctx.ensure_object(dict)
    # ctx.obj['config'] = 


# pfund_plot_group.add_command(...)