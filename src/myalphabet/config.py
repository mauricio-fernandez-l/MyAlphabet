"""Configuration management for MyAlphabet game."""

import copy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG = {
    "app": {
        "name": "My Alphabet Game",
        "icon": {
            "path": "",
            "size": 80,
        },
    },
    "resources": {
        "images": {
            "folder": "",
        },
        "sound": {
            "enabled": True,
            "letters_folder": "",
            "feedback": {
                "correct": "",
                "wrong": "",
            },
        },
        "rewards": {
            "video": {
                "min_rounds": 0,
                "max_wrong_answers": 1,
                "folder": "",
            },
        },
    },
    "game": {
        "player_adjustable": {
            "pictures_per_round": 4,
            "max_rounds": 7,
        },
        "presentation": {
            "letter_font_size": 120,
            "show_lowercase": False,
            "show_image_names": False,
            "show_letter_hint": True,
        },
        "timing": {
            "letter_display_delay_ms": 1500,
            "next_round_delay_ms": 2000,
        },
    },
    "ui": {
        "colors": {
            "background": "#f0f8ff",
            "buttons": {
                "play_again": "#2196F3",
                "quit": "#FF9800",
                "menu": "#4CAF50",
                "letters": "#9C27B0",
                "quiz": "#00BCD4",
            },
        },
    },
}


def _get_nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely read a nested value from a configuration dictionary."""
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _resolve_path(path_str: str, config_dir: Path | None) -> Path | None:
    """Resolve a possibly relative path using the config file directory."""
    if not path_str:
        return None
    path = Path(path_str)
    if not path.is_absolute() and config_dir:
        path = config_dir / path
    return path.resolve()


def _derive_hover_color(color: str) -> str:
    """Return a slightly darker hex color for hover states."""
    if not isinstance(color, str) or not color.startswith("#") or len(color) != 7:
        return color

    try:
        red = int(color[1:3], 16)
        green = int(color[3:5], 16)
        blue = int(color[5:7], 16)
    except ValueError:
        return color

    factor = 0.82
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(red * factor))),
        max(0, min(255, int(green * factor))),
        max(0, min(255, int(blue * factor))),
    )


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
    config = copy.deepcopy(DEFAULT_CONFIG)
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


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
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
    images_folder = _get_nested(config, "resources", "images", "folder", default="")
    if not images_folder:
        errors.append("resources.images.folder is not set in config.yaml")
    else:
        folder_path = Path(images_folder)
        if not folder_path.is_absolute() and config_dir:
            folder_path = config_dir / folder_path
        folder_path = folder_path.resolve()

        if not folder_path.exists():
            errors.append(f"resources.images.folder does not exist: {folder_path}")
        elif not folder_path.is_dir():
            errors.append(f"resources.images.folder is not a directory: {folder_path}")

    # Check pictures_per_round
    pictures_per_round = _get_nested(
        config,
        "game",
        "player_adjustable",
        "pictures_per_round",
        default=4,
    )
    if not isinstance(pictures_per_round, int) or pictures_per_round < 2:
        errors.append("pictures_per_round must be an integer >= 2")

    return errors


class Config:
    """Configuration container with easy attribute access."""

    def __init__(self, config_path: str | Path | None = None):
        resolved_config_path = Path(config_path) if config_path is not None else None
        if resolved_config_path is None:
            resolved_config_path = find_config_file()

        self._config_path = (
            resolved_config_path.resolve()
            if resolved_config_path is not None
            else (Path.cwd() / "config.yaml").resolve()
        )
        self._data, self._config_dir = load_config(resolved_config_path)
        if self._config_dir is None:
            self._config_dir = self._config_path.parent

    @property
    def config_path(self) -> Path:
        """Return the resolved path of the active config file."""
        return self._config_path

    def to_dict(self) -> dict[str, Any]:
        """Return a deep copy of the current configuration data."""
        return copy.deepcopy(self._data)

    def replace_data(self, data: dict[str, Any]) -> None:
        """Replace the current configuration data."""
        self._data = copy.deepcopy(data)

    def save(self) -> Path:
        """Persist the current configuration to disk."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as file_handle:
            yaml.safe_dump(
                self._data,
                file_handle,
                sort_keys=False,
                allow_unicode=False,
            )
        self._config_dir = self._config_path.parent
        return self._config_path

    def apply_runtime_settings(
        self,
        *,
        images_folder: Path,
        pictures_per_round: int | None = None,
        max_rounds: int | None = None,
    ) -> None:
        """Apply menu-driven settings without changing config file path resolution."""
        self._data["resources"]["images"]["folder"] = str(images_folder)
        if pictures_per_round is not None:
            self._data["game"]["player_adjustable"][
                "pictures_per_round"
            ] = pictures_per_round
        if max_rounds is not None:
            self._data["game"]["player_adjustable"]["max_rounds"] = max_rounds

    @property
    def game_name(self) -> str:
        """Return custom game name or default."""
        return _get_nested(self._data, "app", "name", default="My Alphabet Game")

    @property
    def icon_image(self) -> Path | None:
        """Return icon image path, resolving relative paths from config location."""
        icon_str = _get_nested(self._data, "app", "icon", "path", default="")
        return _resolve_path(icon_str, self._config_dir)

    @property
    def icon_size(self) -> int:
        """Return icon size in pixels for menu title."""
        return _get_nested(self._data, "app", "icon", "size", default=80)

    @property
    def images_folder(self) -> Path:
        """Return images folder path, resolving relative paths from config location."""
        folder_str = _get_nested(
            self._data, "resources", "images", "folder", default=""
        )
        folder = _resolve_path(folder_str, self._config_dir)
        if folder is None:
            return Path()
        return folder

    @property
    def pictures_per_round(self) -> int:
        return _get_nested(
            self._data,
            "game",
            "player_adjustable",
            "pictures_per_round",
            default=4,
        )

    @property
    def max_rounds(self) -> int:
        """Return max rounds (0 = unlimited)."""
        return _get_nested(
            self._data, "game", "player_adjustable", "max_rounds", default=0
        )

    @property
    def letter_display_delay_ms(self) -> int:
        """Return delay before showing images (0 = no delay)."""
        return _get_nested(
            self._data, "game", "timing", "letter_display_delay_ms", default=0
        )

    @property
    def next_round_delay_ms(self) -> int:
        return _get_nested(
            self._data, "game", "timing", "next_round_delay_ms", default=2000
        )

    @property
    def background_color(self) -> str:
        return _get_nested(self._data, "ui", "colors", "background", default="#f0f8ff")

    @property
    def letter_font_size(self) -> int:
        return _get_nested(
            self._data, "game", "presentation", "letter_font_size", default=120
        )

    @property
    def show_lowercase(self) -> bool:
        return _get_nested(
            self._data, "game", "presentation", "show_lowercase", default=False
        )

    @property
    def show_image_names(self) -> bool:
        return _get_nested(
            self._data, "game", "presentation", "show_image_names", default=False
        )

    @property
    def show_letter_hint(self) -> bool:
        return _get_nested(
            self._data, "game", "presentation", "show_letter_hint", default=True
        )

    @property
    def play_again_color(self) -> str:
        return _get_nested(
            self._data, "ui", "colors", "buttons", "play_again", default="#2196F3"
        )

    @property
    def play_again_hover(self) -> str:
        return _derive_hover_color(self.play_again_color)

    @property
    def quit_color(self) -> str:
        return _get_nested(
            self._data, "ui", "colors", "buttons", "quit", default="#FF9800"
        )

    @property
    def quit_hover(self) -> str:
        return _derive_hover_color(self.quit_color)

    @property
    def menu_color(self) -> str:
        return _get_nested(
            self._data, "ui", "colors", "buttons", "menu", default="#4CAF50"
        )

    @property
    def menu_hover(self) -> str:
        return _derive_hover_color(self.menu_color)

    @property
    def letters_color(self) -> str:
        return _get_nested(
            self._data, "ui", "colors", "buttons", "letters", default="#9C27B0"
        )

    @property
    def letters_hover(self) -> str:
        return _derive_hover_color(self.letters_color)

    @property
    def quiz_color(self) -> str:
        return _get_nested(
            self._data, "ui", "colors", "buttons", "quiz", default="#00BCD4"
        )

    @property
    def quiz_hover(self) -> str:
        return _derive_hover_color(self.quiz_color)

    @property
    def sound_enabled(self) -> bool:
        """Return whether sound is enabled."""
        return _get_nested(self._data, "resources", "sound", "enabled", default=True)

    @property
    def sounds_folder(self) -> Path | None:
        """Return sounds folder path, resolving relative paths from config location."""
        folder_str = _get_nested(
            self._data,
            "resources",
            "sound",
            "letters_folder",
            default="",
        )
        return _resolve_path(folder_str, self._config_dir)

    @property
    def correct_sound(self) -> Path | None:
        """Return correct answer sound path, resolving relative paths from config location."""
        sound_str = _get_nested(
            self._data,
            "resources",
            "sound",
            "feedback",
            "correct",
            default="",
        )
        return _resolve_path(sound_str, self._config_dir)

    @property
    def wrong_sound(self) -> Path | None:
        """Return wrong answer sound path, resolving relative paths from config location."""
        sound_str = _get_nested(
            self._data,
            "resources",
            "sound",
            "feedback",
            "wrong",
            default="",
        )
        return _resolve_path(sound_str, self._config_dir)

    @property
    def min_rounds_video(self) -> int:
        """Return minimum rounds required to be eligible for video reward (0 = disabled)."""
        return _get_nested(
            self._data,
            "resources",
            "rewards",
            "video",
            "min_rounds",
            default=0,
        )

    @property
    def max_wrong_answers(self) -> int:
        """Return maximum wrong answers allowed to get video reward."""
        return _get_nested(
            self._data,
            "resources",
            "rewards",
            "video",
            "max_wrong_answers",
            default=1,
        )

    @property
    def videos_folder(self) -> Path | None:
        """Return videos folder path, resolving relative paths from config location."""
        folder_str = _get_nested(
            self._data,
            "resources",
            "rewards",
            "video",
            "folder",
            default="",
        )
        return _resolve_path(folder_str, self._config_dir)

    def validate(self) -> list[str]:
        return validate_config(self._data, self._config_dir)
