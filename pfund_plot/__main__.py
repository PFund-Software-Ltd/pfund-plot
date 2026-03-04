def run_cli() -> None:
    """Application Entrypoint."""
    from pfund_plot.cli import pfund_plot_group
    pfund_plot_group(obj={})


if __name__ == '__main__':
    run_cli()
