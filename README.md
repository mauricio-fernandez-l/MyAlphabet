# MyAlphabet 🔤

An alphabet learning game for young children (ages 3-5).

## Overview

MyAlphabet helps children learn the alphabet by showing them pictures and asking them to identify which picture matches a given letter. The game displays a letter (e.g., "L") along with several pictures, and the child must click/touch the picture that starts with that letter.

## Features

- 🎯 Simple, child-friendly interface with large buttons
- 🖼️ Uses your own pictures for a personalized experience
- ✅ Green highlight for correct answers
- ❌ Red highlight for incorrect answers (with correct answer shown)
- 📊 Score tracking
- ⚙️ Configurable via YAML file

## Installation

### From Source

```bash
# Clone or download the repository
cd MyAlphabet

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Dependencies

- Python 3.9+
- Pillow (for image handling)
- PyYAML (for configuration)
- Tkinter (usually included with Python)

## Setting Up Images

1. Create a folder for your alphabet images
2. Add pictures named with the pattern `{LETTER}{NUMBER}.{ext}`:
   - `A1.png` - First picture for letter A
   - `A2.jpg` - Second picture for letter A
   - `B1.png` - First picture for letter B
   - `L1.jpeg` - First picture for letter L
   - etc.

Supported image formats: PNG, JPG, JPEG, GIF, BMP, WEBP

### Tips for Images

- Use clear, simple images that obviously represent words starting with the letter
- For "A": apple, airplane, ant, alligator
- For "B": ball, banana, bear, butterfly
- For "L": lion, lemon, leaf, ladder
- Having 2-3 images per letter provides variety

## Configuration

Create or edit `config.yaml` in your project directory:

```yaml
# Path to your images folder (REQUIRED - update this!)
images_folder: "C:/Pictures/AlphabetImages"

# Number of pictures shown per round
pictures_per_round: 4

# Window settings
window:
  width: 1024
  height: 768
  title: "My Alphabet Game"
  fullscreen: false

# Game settings
game:
  highlight_duration_ms: 1500
  next_round_delay_ms: 2000
  background_color: "#f0f8ff"
  letter_font_size: 120
  show_letter_hint: true
```

The config file is searched in these locations (in order):
1. Current working directory (`./config.yaml`)
2. User home directory (`~/.myalphabet/config.yaml`)
3. Package directory

## Running the Game

```bash
# Run using the installed command
myalphabet

# Or run with a specific config file
myalphabet -c /path/to/config.yaml

# Or run as a Python module
python -m myalphabet

# Show version
myalphabet --version
```

## How to Play

1. **Look at the letter** displayed at the top of the screen
2. **Find the picture** that starts with that letter
3. **Click/touch** the correct picture
   - ✅ **Green border** = Correct! The game advances automatically
   - ❌ **Red border** = Wrong! The correct answer is highlighted in green
4. Keep playing to improve your score!

## Project Structure

```
MyAlphabet/
├── pyproject.toml          # Package configuration
├── config.yaml             # Game configuration
├── README.md               # This file
└── src/
    └── myalphabet/
        ├── __init__.py     # Package initialization
        ├── __main__.py     # Entry point
        ├── config.py       # Configuration management
        ├── game.py         # Main game GUI
        └── images.py       # Image loading utilities
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
```

## License

MIT License - Feel free to use and modify for your own children's education!

## Troubleshooting

### "No images found" error
- Check that `images_folder` in config.yaml points to the correct directory
- Verify image files are named correctly (e.g., `A1.png`, not `apple.png`)
- Ensure images have supported extensions (.png, .jpg, .jpeg, etc.)

### Images look blurry
- Use higher resolution source images (at least 300x300 pixels)
- The game automatically scales images to fit the buttons

### Window too small/large
- Adjust `window.width` and `window.height` in config.yaml
- Set `window.fullscreen: true` for fullscreen mode (press Escape to exit)
