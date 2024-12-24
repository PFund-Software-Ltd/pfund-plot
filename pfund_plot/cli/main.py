import click
from trogon import tui

from pfund_plot.config_handler import get_config
from pfund_plot.cli.commands.plot import plot
from pfund_plot.cli.commands.config import config


@tui(command='tui', help="Open terminal UI")
@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.pass_context
@click.version_option()
def pfund_plot_group(ctx):
    """PFundPlot's CLI"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = get_config(verbose=False)


pfund_plot_group.add_command(plot)
pfund_plot_group.add_command(config)