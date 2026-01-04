# MyAlphabet 🔤

An alphabet learning game for young children (ages 3-5).

## Overview

MyAlphabet helps children learn the alphabet by showing them pictures and asking them to identify which picture matches a given letter. The game displays a letter (e.g., "A a") along with several pictures, and the child must click/touch the picture that starts with that letter.

## Features

- 🎯 Simple, child-friendly touch interface with large buttons
- 🖼️ Uses your own pictures for a personalized experience
- 🔤 Shows both uppercase and lowercase letters (e.g., "A a")
- 🔊 Letter sounds when the letter appears (click letter to replay)
- ✅ Green highlight for correct answers with optional sound
- ❌ Red highlight for incorrect (correct answer shown in blue)
- 📊 Progress tracking with visual boxes
- 🖼️ End-of-game gallery showing all rounds
- ⚙️ Settings menu before each game
- 🎨 Customizable colors and sounds via config file
- 🖼️ Custom icon support for window and menu

## Installation

### From Source

```bash
# Clone or download the repository
cd MyAlphabet

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Linux/Mac

# Install in development mode
pip install -e .
```

### Dependencies

- Python 3.9+
- Pillow (for image handling)
- PyYAML (for configuration)
- Tkinter (usually included with Python)
- pywin32 (for desktop shortcut creation, Windows only)

## Setting Up Images

1. Create a folder for your alphabet images
2. Add pictures named starting with the letter they represent:
   - `Apple.png` - Picture for letter A
   - `Airplane.jpg` - Another picture for letter A  
   - `Ball.png` - Picture for letter B
   - `Lion.jpeg` - Picture for letter L
   - etc.

The game matches images by their **first letter** (case-insensitive).

Supported image formats: PNG, JPG, JPEG, GIF, BMP, WEBP

### Tips for Images

- Use clear, simple images that obviously represent words starting with the letter
- For "A": apple, airplane, ant, alligator
- For "B": ball, banana, bear, butterfly
- For "L": lion, lemon, leaf, ladder
- Having 2-3 images per letter provides variety
- Use images of people/things familiar to your child!

## Setting Up Sounds (Optional)

1. Create a folder for letter sounds
2. Add .wav files named with the letter:
   - `a.wav` - Sound for letter A
   - `b.wav` - Sound for letter B
   - etc.

3. Optionally add reaction sounds:
   - A sound for correct answers
   - A sound for wrong answers

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit:

```yaml
# Custom game name
game_name: "My Super Alphabet"

# Icon for window and menu
icon_image: "path/to/icon.png"
icon_size: 80

# Path to your images folder (REQUIRED)
images_folder: "path/to/images"

# Number of pictures shown per round (2-8)
pictures_per_round: 4

# Limit to specific letters (optional)
allowed_letters: []  # Empty = all available letters

# Game settings
game:
  max_rounds: 10              # 0 = unlimited
  letter_display_delay_ms: 1500  # Show letter before images
  letter_font_size: 72        # Size of letter display
  background_color: "#f0f8ff"

# Sound settings
sound:
  enabled: true
  sounds_folder: "path/to/sounds"
  correct_sound: "path/to/correct.wav"
  wrong_sound: "path/to/wrong.wav"
```

The config file is searched in these locations (in order):
1. Current working directory (`./config.yaml`)
2. User home directory (`~/.myalphabet/config.yaml`)
3. Package directory

## Running the Game

```bash
# Run using the installed command
myalphabet
# or
myalph

# Run with a specific config file
myalph -c /path/to/config.yaml

# Run as a Python module
python -m myalphabet

# Show version
myalph --version
```

## Creating a Desktop Shortcut (Windows)

```bash
python create_shortcut.py
```

This creates a desktop shortcut using your configured `game_name` and `icon_image`.

## How to Play

1. **Start the game** - A menu appears with settings
2. **Adjust settings** if needed (pictures per round, number of rounds)
3. **Click Start Game**
4. **Look at the letter** displayed (shows uppercase and lowercase, e.g., "A a")
5. **Click the letter** to hear it again
6. **Find and click** the picture that starts with that letter
   - ✅ **Green border** = Correct!
   - ❌ **Red border** = Wrong (correct answer shown in blue)
7. **Game auto-advances** to the next round
8. **View the gallery** at the end showing all your answers
9. **Play Again** or return to **Menu**

## Project Structure

```
MyAlphabet/
├── pyproject.toml          # Package configuration
├── config.yaml             # Your game configuration
├── config.example.yaml     # Example configuration
├── create_shortcut.py      # Desktop shortcut creator
├── README.md               # This file
├── data/                   # Your data files
│   ├── images/             # Letter images
│   ├── sounds/             # Letter sounds (.wav)
│   └── icon/               # Game icon
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
- Verify image files start with a letter (e.g., `Apple.png`, `Ball.jpg`)
- Ensure images have supported extensions (.png, .jpg, .jpeg, etc.)

### Images look blurry
- Use higher resolution source images (at least 300x300 pixels)
- The game automatically scales images to fit the buttons

### Window too small/large
- Adjust `window.width` and `window.height` in config.yaml
- Set `window.fullscreen: true` for fullscreen mode (press Escape to exit)

### No sound
- Check that `sound.enabled` is `true` in config.yaml
- Verify sound files are .wav format
- Check that `sounds_folder` path is correct
- Letter sound files should be named `a.wav`, `b.wav`, etc. (lowercase)
