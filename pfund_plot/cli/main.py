from pfund_kit.cli import create_cli_group
from pfund_kit.cli.commands import config, docker_compose, remove
from pfund_plot.cli.commands.serve import serve


def init_context(ctx):
    """Initialize pfund_plot-specific context"""
    from pfund_plot.config import get_config
    ctx.obj['config'] = get_config()


pfund_plot_group = create_cli_group('pfund_plot', init_context=init_context)
pfund_plot_group.add_command(config)
pfund_plot_group.add_command(docker_compose)
pfund_plot_group.add_command(remove)
pfund_plot_group.add_command(serve)
