# CLI Commands

## Plotting
```bash
# TODO: plot sth using command `pfplt`
```


## Configuration
```bash
# list current configs
pfplt config --list

# for more config options, run:
pfplt config --help 
```


## Open Configuration Files
For convenience, you can open the config files directly from your CLI.
```bash
# open the config file with VS Code/Cursor AI
pfplt open --config-file
```

## Start/Build Docs
> need to have `mystmd` installed to start/build docs locally: `npm install -g mystmd`
```bash
# open the docs in browser
pfplt doc
# --execute: execute the jupyter notebooks
pfplt doc --start [--execute]
pfplt doc --build [--execute]
```

## Open Terminal UI
```bash
pfplt tui
```