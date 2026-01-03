"""Configuration management for MyAlphabet game."""

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = {
    "images_folder": "",
    "pictures_per_round": 4,
    "allowed_letters": [],
    "window": {
        "width": 1024,
        "height": 768,
        "title": "My Alphabet Game",
        "fullscreen": False,
    },
    "game": {
        "max_rounds": 7,
        "letter_display_delay_ms": 1500,
        "highlight_duration_ms": 1500,
        "next_round_delay_ms": 2000,
        "background_color": "#f0f8ff",
        "letter_font_size": 120,
        "show_letter_hint": True,
    },
    "buttons": {
        "play_again_color": "#2196F3",
        "play_again_hover": "#1976D2",
        "quit_color": "#FF9800",
        "quit_hover": "#F57C00",
        "menu_color": "#4CAF50",
        "menu_hover": "#388E3C",
    },
    "sound": {
        "enabled": False,
        "correct_sound": "",
        "wrong_sound": "",
    },
}


def find_config_file() -> Path | None:
    """
    Find the config.yaml file in common locations.

    Search order:
    1. Current working directory
    2. User's home directory/.myalphabet/
    3. Package directory
    """
    search_paths = [
        Path.cwd() / "config.yaml",
        Path.home() / ".myalphabet" / "config.yaml",
        Path(__file__).parent / "config.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def load_config(
    config_path: str | Path | None = None,
) -> tuple[dict[str, Any], Path | None]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Optional path to config file. If None, searches default locations.

    Returns:
        Tuple of (configuration dictionary, config file directory or None).
    """
    config = DEFAULT_CONFIG.copy()
    config_dir = None

    if config_path is None:
        config_path = find_config_file()

    if config_path is not None:
        config_path = Path(config_path)
        if config_path.exists():
            config_dir = config_path.parent
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    config = _deep_merge(config, user_config)

    return config, config_dir


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def validate_config(
    config: dict[str, Any], config_dir: Path | None = None
) -> list[str]:
    """
    Validate the configuration and return a list of errors.

    Args:
        config: Configuration dictionary to validate.
        config_dir: Directory containing the config file (for relative path resolution).

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    # Check images folder
    images_folder = config.get("images_folder", "")
    if not images_folder:
        errors.append("images_folder is not set in config.yaml")
    else:
        folder_path = Path(images_folder)
        if not folder_path.is_absolute() and config_dir:
            folder_path = config_dir / folder_path
        folder_path = folder_path.resolve()

        if not folder_path.exists():
            errors.append(f"images_folder does not exist: {folder_path}")
        elif not folder_path.is_dir():
            errors.append(f"images_folder is not a directory: {folder_path}")

    # Check pictures_per_round
    pictures_per_round = config.get("pictures_per_round", 4)
    if not isinstance(pictures_per_round, int) or pictures_per_round < 2:
        errors.append("pictures_per_round must be an integer >= 2")

    return errors


class Config:
    """Configuration container with easy attribute access."""

    def __init__(self, config_path: str | Path | None = None):
        self._data, self._config_dir = load_config(config_path)

    @property
    def images_folder(self) -> Path:
        """Return images folder path, resolving relative paths from config location."""
        folder = Path(self._data["images_folder"])
        if not folder.is_absolute() and self._config_dir:
            folder = self._config_dir / folder
        return folder.resolve()

    @property
    def pictures_per_round(self) -> int:
        return self._data["pictures_per_round"]

    @property
    def allowed_letters(self) -> list[str]:
        """Return list of allowed letters (uppercase), or empty list for all."""
        letters = self._data.get("allowed_letters", [])
        if letters:
            return [l.upper() for l in letters]
        return []

    @property
    def window_width(self) -> int:
        return self._data["window"]["width"]

    @property
    def window_height(self) -> int:
        return self._data["window"]["height"]

    @property
    def window_title(self) -> str:
        return self._data["window"]["title"]

    @property
    def fullscreen(self) -> bool:
        return self._data["window"]["fullscreen"]

    @property
    def max_rounds(self) -> int:
        """Return max rounds (0 = unlimited)."""
        return self._data["game"].get("max_rounds", 0)

    @property
    def letter_display_delay_ms(self) -> int:
        """Return delay before showing images (0 = no delay)."""
        return self._data["game"].get("letter_display_delay_ms", 0)

    @property
    def highlight_duration_ms(self) -> int:
        return self._data["game"]["highlight_duration_ms"]

    @property
    def next_round_delay_ms(self) -> int:
        return self._data["game"]["next_round_delay_ms"]

    @property
    def background_color(self) -> str:
        return self._data["game"]["background_color"]

    @property
    def letter_font_size(self) -> int:
        return self._data["game"]["letter_font_size"]

    @property
    def show_letter_hint(self) -> bool:
        return self._data["game"]["show_letter_hint"]

    @property
    def play_again_color(self) -> str:
        return self._data["buttons"]["play_again_color"]

    @property
    def play_again_hover(self) -> str:
        return self._data["buttons"]["play_again_hover"]

    @property
    def quit_color(self) -> str:
        return self._data["buttons"]["quit_color"]

    @property
    def quit_hover(self) -> str:
        return self._data["buttons"]["quit_hover"]

    @property
    def menu_color(self) -> str:
        return self._data["buttons"]["menu_color"]

    @property
    def menu_hover(self) -> str:
        return self._data["buttons"]["menu_hover"]

    def validate(self) -> list[str]:
        return validate_config(self._data, self._config_dir)
