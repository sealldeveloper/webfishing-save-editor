<p align="center">
  <img src="/img/logo.png" alt="WebFishing Save Tool Logo" width="200"/>
</p>

<h1 align="center">WebFishing Save Tool</h1>

<p align="center">
  A Python utility for converting WebFishing save files (.sav) to and from JSON format.
</p>

## Features

- Decode WebFishing `.sav` files to human-readable JSON
- Encode JSON files back to WebFishing `.sav` format
- View basic player statistics while decoding
- Support for all Godot variant types used in save files
- Proper padding and alignment handling

## Installation

Clone the repository and ensure you have Python 3.6 or higher installed:

```bash
git clone https://github.com/yourusername/webfishing-save-tool.git
cd webfishing-save-tool
```

## Usage

### Decode Save File to JSON

```bash
python save_tool.py decode input.sav output.json
```

To view player stats while decoding:
```bash
python save_tool.py decode input.sav output.json --info
```

### Encode JSON to Save File

```bash
python save_tool.py encode input.json output.sav
```

### Help

For full command documentation:
```bash
python save_tool.py --help
```

## Supported Data Types

- Basic types (nil, bool, int, float, string)
- Vector2
- Arrays
- Dictionaries
- All numeric types with proper bit width handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the WebFishing game community
- Based on Godot's binary serialization format
- Inspired by [NotNite's webfishing-save-editor](https://github.com/NotNite/webfishing-save-editor) and [alicealys editor](https://github.com/alicealys/webfishing-save-editor)
