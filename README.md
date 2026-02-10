# MyAlphabet 🔤

An alphabet learning game for young children (ages 3-5).

## Overview

MyAlphabet helps children learn the alphabet through three game modes — picture matching, letter quizzes, and a letter gallery. The game runs fullscreen with a touch-friendly emoji UI designed for small hands.

## Features

- 🎯 Touch-friendly fullscreen interface with large emoji buttons
- 🖼️ Uses your own pictures for a personalized experience
- 🔤 Three game modes:
  - **Alphabet Game** — a letter is shown, child picks the matching picture
  - **Letter Quiz** — a letter sound plays, child picks the correct letter
  - **Letters View** — browse all letters and their images as a gallery
- 🔊 Letter sounds when the letter appears (click letter to replay)
- ✅ Green highlight for correct answers with optional sound
- ❌ Red highlight for incorrect (correct answer shown in blue)
- 📊 Progress tracking with visual boxes
- 🖼️ End-of-game gallery showing all rounds
- 🎬 Video reward — plays a random video alongside the gallery when the child does well
- ⚙️ Settings menu before each game (pictures per round, number of rounds)
- 🎨 Customizable colors, sounds, and button styles via config file
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
- python-vlc (for video reward playback)
- Tkinter (usually included with Python)
- pywin32 (for desktop shortcut creation, Windows only)

> **Note:** The video reward feature requires [VLC media player](https://www.videolan.org/) to be installed on your system.

## Setting Up Images

1. Create a folder for your alphabet images
2. Add pictures named starting with the letter they represent:
   - `Apple.png` — picture for letter A
   - `Airplane.jpg` — another picture for letter A
   - `Ball.png` — picture for letter B
   - `Lion.jpeg` — picture for letter L
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
2. Add `.wav` files named with the letter:
   - `a.wav` — sound for letter A
   - `b.wav` — sound for letter B
   - etc.
3. Optionally add reaction sounds:
   - A sound for correct answers
   - A sound for wrong answers

## Setting Up Video Rewards (Optional)

The game can play a short reward video alongside the end-of-game gallery when the child performs well.

1. Create a folder for reward videos
2. Add video files (`.mp4`, `.avi`, `.mkv`, etc.)
3. Configure thresholds in `config.yaml`:

```yaml
video_reward:
  min_rounds_video: 3       # Minimum rounds played to be eligible
  max_wrong_answers: 1      # Max wrong answers allowed (0 = perfect score only)
  videos_folder: "path/to/videos"
```

A random video from the folder is chosen each time the child earns a reward.

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

# Game settings
game:
  pictures_per_round: 4        # Number of choices per round (2-8)
  allowed_letters: []           # Empty = all available letters
  max_rounds: 10                # 0 = unlimited, max 10
  letter_display_delay_ms: 1500 # Show letter before images
  letter_font_size: 72          # Size of letter display
  show_lowercase: false         # Show "A a" instead of just "A"
  show_image_names: true        # Show names below pictures
  show_letter_hint: true        # Show "L is for..." hint
  background_color: "#f0f8ff"

# Button colors
buttons:
  play_again_color: "#2196F3"
  menu_color: "#4CAF50"
  quit_color: "#FF9800"
  letters_color: "#9C27B0"
  quiz_color: "#00BCD4"

# Sound settings
sound:
  enabled: true
  sounds_folder: "path/to/sounds"
  correct_sound: "path/to/correct.wav"
  wrong_sound: "path/to/wrong.wav"

# Video reward
video_reward:
  min_rounds_video: 3
  max_wrong_answers: 1
  videos_folder: "path/to/videos"
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

### Alphabet Game

1. A **letter** is displayed (e.g., "A a")
2. Several pictures appear — tap the one that starts with that letter
3. ✅ Green border = correct, ❌ red border = wrong (correct answer shown in blue)
4. After all rounds, a **gallery** shows your results (and a reward video if earned!)

### Letter Quiz

1. A **letter sound** plays automatically
2. Several letters appear — tap the one you heard
3. Tap the speaker icon to hear the sound again
4. Scoring and gallery work the same as the Alphabet Game

### Letters View

1. Browse all available letters in a grid
2. Tap a letter to see all its images
3. Tap an image to hear the letter sound

### Menu

- Choose your game mode from the main menu
- Adjust **pictures per round** and **number of rounds** before starting
- Return to the menu anytime via the 🏠 button

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
│   ├── videos/             # Reward videos
│   └── icon/               # Game icon
└── src/
    └── myalphabet/
        ├── __init__.py     # Package initialization
        ├── __main__.py     # Entry point
        ├── config.py       # Configuration management
        ├── game.py         # Game modes and UI
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
