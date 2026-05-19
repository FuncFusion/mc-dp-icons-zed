# Datapack Icons for Zed

Minecraft icon theme for datapacks, resource packs, and addons.

Zed port of the [VS Code extension](https://github.com/FuncFusion/mc-dp-icons).

## Installation

1. Install the extension from the [Zed extensions page](https://zed.dev/extensions) (search "Datapack Icons")
2. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → `zed: open settings`
3. Set `"icon_theme": "Datapack Icons"`

## Usage

The theme registers file and folder icons for all Minecraft-related file types,
plus a Christmas variant that activates automatically in December.

## Limitations

This is a static icon theme — runtime features from the VS Code extension do not apply:

- No dynamic function icons (tick/load/crowned)
- No workspace detection
- No namespace or overlay folder detection
- No subfolder icon workaround
- No configurable settings

For the full experience with dynamic icons, use the [VS Code extension](https://github.com/FuncFusion/mc-dp-icons).

## Development

```sh
git clone https://github.com/FuncFusion/mc-dp-icons
git clone https://github.com/FuncFusion/mc-dp-icons-zed

cd mc-dp-icons-zed
python3 generate.py
```

The generator reads icon data from `../mc-dp-icons/src/data/baseTheme.ts`,
converts to Zed format, copies SVGs, and writes `icon_themes/mc-dp-icons.json`.
Point with `--source` to a different path:

```sh
python3 generate.py --source /path/to/mc-dp-icons
```
