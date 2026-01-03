"""Main game GUI for MyAlphabet."""

import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable

from PIL import Image, ImageTk

from .config import Config
from .images import get_available_letters, select_round_images


class ImageButton(tk.Canvas):
    """A clickable image button with highlight capability."""

    def __init__(
        self,
        parent: tk.Widget,
        size: tuple[int, int] = (200, 200),
        on_click: Callable[["ImageButton"], None] | None = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=size[0],
            height=size[1],
            highlightthickness=8,
            highlightbackground="#cccccc",
            **kwargs,
        )
        self.size = size
        self.on_click = on_click
        self.image_path: Path | None = None
        self.photo_image: ImageTk.PhotoImage | None = None
        self._enabled = True

        self.bind("<Button-1>", self._handle_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def load_image(self, image_path: Path) -> None:
        """Load and display an image."""
        self.image_path = image_path

        # Load and resize image
        img = Image.open(image_path)
        img.thumbnail((self.size[0] - 16, self.size[1] - 16), Image.Resampling.LANCZOS)

        # Keep reference to prevent garbage collection
        self.photo_image = ImageTk.PhotoImage(img)

        # Clear and draw
        self.delete("all")
        self.create_image(
            self.size[0] // 2,
            self.size[1] // 2,
            image=self.photo_image,
            anchor=tk.CENTER,
        )

    def set_highlight(self, color: str | None) -> None:
        """Set the highlight border color."""
        if color:
            self.configure(highlightbackground=color, highlightthickness=8)
        else:
            self.configure(highlightbackground="#cccccc", highlightthickness=8)

    def clear_highlight(self) -> None:
        """Remove highlight."""
        self.set_highlight(None)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the button."""
        self._enabled = enabled
        if enabled:
            self.configure(cursor="hand2")
        else:
            self.configure(cursor="")

    def _handle_click(self, event: tk.Event) -> None:
        """Handle click event."""
        if self._enabled and self.on_click:
            self.on_click(self)

    def _on_enter(self, event: tk.Event) -> None:
        """Handle mouse enter."""
        if self._enabled:
            self.configure(highlightthickness=10)

    def _on_leave(self, event: tk.Event) -> None:
        """Handle mouse leave."""
        self.configure(highlightthickness=8)


class AlphabetGame:
    """Main game class managing the alphabet learning game."""

    def __init__(self, config: Config):
        self.config = config
        self.available_letters: set[str] = set()
        self.letter_queue: list[str] = []  # Shuffled queue of letters for fair rotation
        self.current_letter: str = ""
        self.correct_index: int = -1
        self.image_buttons: list[ImageButton] = []
        self.score: int = 0
        self.rounds_played: int = 0

        # Initialize main window
        self.root = tk.Tk()
        self.root.title(config.window_title)
        self.root.configure(bg=config.background_color)

        if config.fullscreen:
            self.root.attributes("-fullscreen", True)
            self.root.bind(
                "<Escape>", lambda e: self.root.attributes("-fullscreen", False)
            )
        else:
            self.root.geometry(f"{config.window_width}x{config.window_height}")

        # Center window on screen
        self.root.update_idletasks()
        self._center_window()

        self._setup_ui()
        self._load_game_data()

    def _center_window(self) -> None:
        """Center the window on the screen."""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        bg_color = self.config.background_color

        # Main container
        self.main_frame = tk.Frame(self.root, bg=bg_color)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Top section - Letter display
        self.letter_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.letter_frame.pack(pady=(0, 30))

        self.letter_label = tk.Label(
            self.letter_frame,
            text="",
            font=("Arial", self.config.letter_font_size, "bold"),
            bg=bg_color,
            fg="#333333",
        )
        self.letter_label.pack()

        if self.config.show_letter_hint:
            self.hint_label = tk.Label(
                self.letter_frame,
                text="",
                font=("Arial", 24),
                bg=bg_color,
                fg="#666666",
            )
            self.hint_label.pack()

        # Middle section - Images
        self.images_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.images_frame.pack(expand=True)

        # Bottom section - Score and controls
        self.controls_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.controls_frame.pack(pady=(30, 0))

        self.score_label = tk.Label(
            self.controls_frame,
            text="Score: 0",
            font=("Arial", 20),
            bg=bg_color,
            fg="#333333",
        )
        self.score_label.pack(side=tk.LEFT, padx=20)

        self.next_button = tk.Button(
            self.controls_frame,
            text="Next Letter",
            font=("Arial", 16),
            command=self.start_new_round,
            state=tk.DISABLED,
        )
        self.next_button.pack(side=tk.LEFT, padx=20)

        self.quit_button = tk.Button(
            self.controls_frame,
            text="Quit",
            font=("Arial", 16),
            command=self.quit_game,
        )
        self.quit_button.pack(side=tk.LEFT, padx=20)

    def _load_game_data(self) -> None:
        """Load available letters from the images folder."""
        self.available_letters = get_available_letters(self.config.images_folder)

        # Filter by allowed_letters if specified
        if self.config.allowed_letters:
            allowed_set = set(self.config.allowed_letters)
            self.available_letters = self.available_letters & allowed_set

        if not self.available_letters:
            messagebox.showerror(
                "No Images Found",
                f"No valid images found in:\n{self.config.images_folder}\n\n"
                "Images should be named like A1.png, B2.jpg, etc.",
            )
            self.root.quit()
            return

        # Start the first round
        self.start_new_round()

    def _create_image_buttons(self, num_images: int) -> None:
        """Create image buttons for the round."""
        # Clear existing buttons
        for button in self.image_buttons:
            button.destroy()
        self.image_buttons.clear()

        # Calculate button size based on window and number of images
        # Arrange in a grid
        cols = min(num_images, 4)
        rows = (num_images + cols - 1) // cols

        available_width = self.config.window_width - 80
        available_height = self.config.window_height - 350

        button_width = min(250, available_width // cols - 20)
        button_height = min(250, available_height // rows - 20)
        button_size = min(button_width, button_height)

        # Create grid of buttons
        for i in range(num_images):
            row = i // cols
            col = i % cols

            button = ImageButton(
                self.images_frame,
                size=(button_size, button_size),
                on_click=self._on_image_click,
                bg="white",
            )
            button.grid(row=row, column=col, padx=10, pady=10)
            button.set_enabled(True)
            self.image_buttons.append(button)

    def _get_next_letter(self) -> str:
        """Get the next letter, reshuffling when all letters have been used."""
        if not self.letter_queue:
            # Reshuffle all available letters
            self.letter_queue = list(self.available_letters)
            random.shuffle(self.letter_queue)
        return self.letter_queue.pop()

    def start_new_round(self) -> None:
        """Start a new round with the next letter from the queue."""
        # Get next letter from shuffled queue
        self.current_letter = self._get_next_letter()

        # Update letter display
        self.letter_label.configure(text=self.current_letter)
        if self.config.show_letter_hint:
            self.hint_label.configure(
                text=f"Find the picture that starts with '{self.current_letter}'!"
            )

        # Get images for this round
        try:
            images, self.correct_index = select_round_images(
                self.config.images_folder,
                self.current_letter,
                self.config.pictures_per_round,
                self.available_letters,
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Create buttons and load images
        self._create_image_buttons(len(images))

        for i, (button, image_path) in enumerate(zip(self.image_buttons, images)):
            button.load_image(image_path)
            button.clear_highlight()
            button.set_enabled(True)

        # Disable next button until answer is given
        self.next_button.configure(state=tk.DISABLED)

        self.rounds_played += 1

    def _on_image_click(self, button: ImageButton) -> None:
        """Handle image button click."""
        clicked_index = self.image_buttons.index(button)

        # Disable all buttons
        for btn in self.image_buttons:
            btn.set_enabled(False)

        if clicked_index == self.correct_index:
            # Correct answer!
            button.set_highlight("#00ff00")  # Green
            self.score += 1
            self.score_label.configure(text=f"Score: {self.score}")

            # Auto-advance after delay
            self.root.after(self.config.next_round_delay_ms, self.start_new_round)
        else:
            # Wrong answer
            button.set_highlight("#ff0000")  # Red
            # Highlight the correct answer too
            self.image_buttons[self.correct_index].set_highlight("#00ff00")

            # Enable next button after highlighting
            self.root.after(
                self.config.highlight_duration_ms,
                lambda: self.next_button.configure(state=tk.NORMAL),
            )

    def quit_game(self) -> None:
        """Quit the game."""
        if self.rounds_played > 0:
            result = messagebox.askyesno(
                "Quit Game",
                f"You scored {self.score} out of {self.rounds_played} rounds!\n\n"
                "Do you want to quit?",
            )
            if result:
                self.root.quit()
        else:
            self.root.quit()

    def run(self) -> None:
        """Run the game main loop."""
        self.root.mainloop()


def run_game(config_path: str | Path | None = None) -> None:
    """
    Run the alphabet game.

    Args:
        config_path: Optional path to config file.
    """
    config = Config(config_path)

    # Validate configuration
    errors = config.validate()
    if errors:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Configuration Error",
            "The following configuration errors were found:\n\n"
            + "\n".join(f"• {e}" for e in errors),
        )
        root.destroy()
        return

    game = AlphabetGame(config)
    game.run()
