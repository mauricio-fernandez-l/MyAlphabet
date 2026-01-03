"""
MyAlphabet - An alphabet learning game for young children.

This game helps children learn the alphabet by showing them pictures
and asking them to identify which picture matches a given letter.
"""

__version__ = "0.1.0"
__author__ = "Parent Developer"

from .config import Config, load_config
from .game import AlphabetGame, run_game
from .images import get_available_letters, get_images_for_letter

__all__ = [
    "Config",
    "load_config",
    "AlphabetGame",
    "run_game",
    "get_available_letters",
    "get_images_for_letter",
]
