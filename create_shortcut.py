"""Create a desktop shortcut for MyAlphabet game."""

import os
import sys
from pathlib import Path

import win32com.client
from PIL import Image


def png_to_ico(png_path: Path, ico_path: Path) -> None:
    """Convert PNG image to ICO format for Windows shortcut."""
    img = Image.open(png_path)
    # Resize to common icon sizes
    img = img.convert("RGBA")
    # Create ICO with multiple sizes
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    imgs = []
    for size in sizes:
        resized = img.copy()
        resized.thumbnail(size, Image.Resampling.LANCZOS)
        # Create a new image with exact size and paste centered
        new_img = Image.new("RGBA", size, (0, 0, 0, 0))
        offset = ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2)
        new_img.paste(resized, offset)
        imgs.append(new_img)

    # Save as ICO
    imgs[0].save(
        ico_path, format="ICO", sizes=[img.size for img in imgs], append_images=imgs[1:]
    )


def create_shortcut():
    """Create desktop shortcut for MyAlphabet game."""
    # Get project root directory
    project_root = Path(__file__).parent.resolve()

    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from myalphabet.config import Config

    # Load config
    config_path = project_root / "config.yaml"
    if not config_path.exists():
        print(f"Error: config.yaml not found at {config_path}")
        sys.exit(1)

    config = Config(config_path)

    # Get icon image path
    icon_path = config.icon_image
    if not icon_path:
        print(
            "Warning: app.icon.path is not set in config.yaml, shortcut will have no custom icon"
        )
        ico_path = None
    else:
        if not icon_path.exists():
            print(f"Warning: Icon image not found at {icon_path}")
            ico_path = None
        else:
            # Convert PNG to ICO
            ico_path = project_root / "data" / "icon" / "myalphabet.ico"
            ico_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"Converting {icon_path} to ICO format...")
            png_to_ico(icon_path, ico_path)
            print(f"Created icon: {ico_path}")

    # Find Python executable in .venv
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print(f"Error: Virtual environment not found at {venv_python}")
        print("Please create a .venv first: python -m venv .venv")
        sys.exit(1)

    # Get desktop path
    desktop = Path(os.path.expanduser("~")) / "Desktop"
    if not desktop.exists():
        # Try OneDrive desktop
        desktop = Path(os.path.expanduser("~")) / "OneDrive" / "Desktop"
    if not desktop.exists():
        print(f"Error: Desktop folder not found")
        sys.exit(1)

    # Get game name from config
    game_name = config.game_name

    # Create shortcut
    shortcut_path = desktop / f"{game_name}.lnk"

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))

    # Set target to pythonw.exe (no console window)
    pythonw = project_root / ".venv" / "Scripts" / "pythonw.exe"
    if pythonw.exists():
        shortcut.TargetPath = str(pythonw)
    else:
        shortcut.TargetPath = str(venv_python)

    # Arguments to run myalph module
    shortcut.Arguments = "-m myalphabet"

    # Working directory
    shortcut.WorkingDirectory = str(project_root)

    # Description
    shortcut.Description = f"{game_name} - Learn the alphabet with pictures!"

    # Icon
    if ico_path and ico_path.exists():
        shortcut.IconLocation = str(ico_path)

    # Save shortcut
    shortcut.Save()

    print(f"\nShortcut created successfully!")
    print(f"Location: {shortcut_path}")
    print(f"Target: {shortcut.TargetPath}")
    print(f"Arguments: {shortcut.Arguments}")
    print(f"Working Dir: {shortcut.WorkingDirectory}")
    if ico_path:
        print(f"Icon: {ico_path}")


if __name__ == "__main__":
    create_shortcut()
