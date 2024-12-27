import click

from pfeed.const.enums import DataTool
from pfund_plot.const.paths import PROJ_NAME


@click.group()
def config():
    """Manage configuration settings."""
    pass


@config.command()
@click.pass_context
def list(ctx):
    """List all available options."""
    from pprint import pformat
    from dataclasses import asdict
    config_dict = asdict(ctx.obj['config'])
    content = click.style(pformat(config_dict), fg='green')
    click.echo(f"{PROJ_NAME} config:\n{content}")


@config.command()
@click.pass_context
def reset(ctx):
    """Reset the configuration to defaults."""
    ctx.obj['config'].reset()
    click.echo(f"{PROJ_NAME} config reset successfully.")


@config.command()
@click.option('--data-tool', '--dt', type=click.Choice(DataTool, case_sensitive=False), help='Set the data tool')
@click.option('--max-points', '--mp', type=int, help='Set the maximum number of points to display in the plot')
@click.option('--data-path', '--dp', type=click.Path(resolve_path=True), help='Set the data path')
@click.option('--cache-path', '--cp', type=click.Path(resolve_path=True), help='Set the cache path')
def set(**kwargs):
    """Configures pfund_plot settings."""
    from pfund_plot.config_handler import configure
    provided_options = {k: v for k, v in kwargs.items() if v is not None}
    if not provided_options:
        raise click.UsageError(f"No options provided. Please run '{PROJ_NAME} config set --help' to see all available options.")
    else:
        configure(write=True, **kwargs)
        click.echo(f"{PROJ_NAME} config updated successfully.")


@config.command()
@click.option('--config-file', '-c', is_flag=True, help=f'Open the {PROJ_NAME}_config.yml file')
@click.option('--default-editor', '-E', is_flag=True, help='Use default editor')
def open(config_file, default_editor):
    """Opens config files, e.g. pfund_plot_config.yml."""
    from pfund_plot.const.paths import CONFIG_FILE_PATH
    
    if sum([config_file]) > 1:
        click.echo('Please specify only one file to open')
        return
    else:
        if config_file:
            file_path = CONFIG_FILE_PATH
        else:
            click.echo(f'Please specify a file to open, run "{PROJ_NAME} config open --help" for more info')
            return
    
    if default_editor:
        click.edit(filename=file_path)
    else:
        open_with_vscode(file_path)
        
        
def open_with_vscode(file_path):
    import subprocess
    try:
        subprocess.run(["code", str(file_path)], check=True)
        click.echo(f"Opened {file_path} with VS Code")
    except subprocess.CalledProcessError:
        click.echo("Failed to open with VS Code. Falling back to default editor.")
        click.edit(filename=file_path)
    except FileNotFoundError:
        click.echo("VS Code command 'code' not found. Falling back to default editor.")
        click.edit(filename=file_path)