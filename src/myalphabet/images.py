"""Image loading and management for MyAlphabet game."""

import random
from pathlib import Path


# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def get_letter_from_filename(filename: str) -> str | None:
    """
    Extract the letter from the first character of a filename.

    Args:
        filename: The filename (without path).

    Returns:
        The uppercase letter if the first character is a letter, None otherwise.
    """
    if filename and filename[0].isalpha():
        return filename[0].upper()
    return None


def get_available_letters(images_folder: Path) -> set[str]:
    """
    Scan the images folder and return the set of available letters.

    Args:
        images_folder: Path to the folder containing images.

    Returns:
        Set of uppercase letters that have at least one image.
    """
    letters = set()

    if not images_folder.exists():
        return letters

    for file_path in images_folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            letter = get_letter_from_filename(file_path.stem)
            if letter:
                letters.add(letter)

    return letters


def get_images_for_letter(images_folder: Path, letter: str) -> list[Path]:
    """
    Get all image paths for a specific letter.

    Args:
        images_folder: Path to the folder containing images.
        letter: The letter to get images for (case-insensitive).

    Returns:
        List of paths to images for the given letter.
    """
    letter = letter.upper()
    images = []

    if not images_folder.exists():
        return images

    for file_path in images_folder.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            file_letter = get_letter_from_filename(file_path.stem)
            if file_letter == letter:
                images.append(file_path)

    return sorted(images)


def select_round_images(
    images_folder: Path,
    target_letter: str,
    num_pictures: int = 4,
    available_letters: set[str] | None = None,
) -> tuple[list[Path], int]:
    """
    Select images for a game round.

    Args:
        images_folder: Path to the folder containing images.
        target_letter: The letter the player needs to find.
        num_pictures: Total number of pictures to show.
        available_letters: Pre-computed set of available letters (optional).

    Returns:
        Tuple of (list of image paths, index of correct image).
    """
    target_letter = target_letter.upper()

    if available_letters is None:
        available_letters = get_available_letters(images_folder)

    # Get images for the target letter
    target_images = get_images_for_letter(images_folder, target_letter)
    if not target_images:
        raise ValueError(f"No images found for letter '{target_letter}'")

    # Pick one random target image
    target_image = random.choice(target_images)

    # Get distractor letters (excluding target)
    distractor_letters = list(available_letters - {target_letter})

    # Select distractor images
    num_distractors = min(num_pictures - 1, len(distractor_letters))
    selected_distractors = []

    if distractor_letters and num_distractors > 0:
        chosen_letters = random.sample(distractor_letters, num_distractors)
        for letter in chosen_letters:
            letter_images = get_images_for_letter(images_folder, letter)
            if letter_images:
                selected_distractors.append(random.choice(letter_images))

    # Combine and shuffle
    all_images = [target_image] + selected_distractors

    # Track where the target ends up after shuffling
    random.shuffle(all_images)
    correct_index = all_images.index(target_image)

    return all_images, correct_index


def get_letter_from_image(image_path: Path) -> str | None:
    """
    Extract the letter from an image filename (first character).

    Args:
        image_path: Path to the image file.

    Returns:
        The uppercase letter, or None if the filename doesn't start with a letter.
    """
    return get_letter_from_filename(image_path.stem)
