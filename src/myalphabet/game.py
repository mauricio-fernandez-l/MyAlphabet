"""Main game GUI for MyAlphabet."""

import random
import tkinter as tk
import winsound
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox
from typing import Callable

from PIL import Image, ImageTk

from .config import Config
from .images import get_available_letters, get_images_for_letter, select_round_images


@dataclass
class RoundResult:
    """Store the result of a single round."""

    letter: str
    was_correct: bool
    chosen_image: Path
    correct_image: Path


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

    def __init__(
        self, config: Config, root: tk.Tk, on_menu_callback: Callable[[], None]
    ):
        self.config = config
        self.root = root
        self.on_menu_callback = on_menu_callback
        self.available_letters: set[str] = set()
        self.letter_queue: list[str] = []  # Shuffled queue of letters for fair rotation
        self.current_letter: str = ""
        self.correct_index: int = -1
        self.current_images: list[Path] = []  # Images for current round
        self.image_buttons: list[ImageButton] = []
        self.image_containers: list[tk.Frame] = (
            []
        )  # Container frames for buttons + labels
        self.image_name_labels: list[tk.Frame] = []  # Label frames showing image names
        self.score: int = 0
        self.rounds_played: int = 0
        self.round_results: list[RoundResult] = []  # Track all round results
        self.progress_boxes: list[tk.Canvas] = []  # Progress indicator boxes

        self._setup_ui()
        self._load_game_data()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        bg_color = self.config.background_color

        # Main container
        self.main_frame = tk.Frame(self.root, bg=bg_color)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Set up the game UI content
        self._setup_ui_content()

    def _setup_ui_content(self) -> None:
        """Set up the game UI content inside main_frame."""
        bg_color = self.config.background_color

        # Top bar: Progress (left), Letter (center), Buttons (right)
        self.top_bar = tk.Frame(self.main_frame, bg=bg_color)
        self.top_bar.pack(fill=tk.X)

        # Configure grid columns for top bar
        self.top_bar.columnconfigure(0, weight=1)  # Left - progress
        self.top_bar.columnconfigure(1, weight=1)  # Center - letter
        self.top_bar.columnconfigure(2, weight=1)  # Right - buttons

        # Left: Progress indicator
        if self.config.max_rounds > 0:
            self.progress_frame = tk.Frame(self.top_bar, bg=bg_color)
            self.progress_frame.grid(row=0, column=0, sticky="w")
            self._create_progress_boxes()

        # Center: Letter display (clickable button to replay sound)
        self.letter_frame = tk.Frame(self.top_bar, bg=bg_color)
        self.letter_frame.grid(row=0, column=1)

        self.letter_button = tk.Button(
            self.letter_frame,
            text="",
            font=("Arial", self.config.letter_font_size, "bold"),
            bg="white",
            fg="#333333",
            activebackground="#e0e0e0",
            activeforeground="#333333",
            bd=2,
            relief=tk.RAISED,
            padx=8,
            pady=0,
            command=self._on_letter_click,
            cursor="hand2",
        )
        self.letter_button.pack()

        # Right: Menu and Quit buttons
        self.top_right_frame = tk.Frame(self.top_bar, bg=bg_color)
        self.top_right_frame.grid(row=0, column=2, sticky="e")

        self.menu_button = tk.Button(
            self.top_right_frame,
            text="Menu",
            font=("Arial", 12),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
        )
        self.menu_button.pack(side=tk.LEFT, padx=(0, 5))

        self.quit_button = tk.Button(
            self.top_right_frame,
            text="Quit",
            font=("Arial", 12),
            command=self.quit_game,
            bg=self.config.quit_color,
            fg="white",
            activebackground=self.config.quit_hover,
            activeforeground="white",
        )
        self.quit_button.pack(side=tk.LEFT)

        # Images section - takes remaining space
        self.images_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.images_frame.pack(expand=True, fill=tk.BOTH)

    def _on_letter_click(self) -> None:
        """Handle letter button click - replay the letter sound."""
        if self.current_letter:
            self._play_letter_sound(self.current_letter)

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

    def _create_progress_boxes(self) -> None:
        """Create progress indicator boxes."""
        self.progress_boxes.clear()
        box_size = 30

        for i in range(self.config.max_rounds):
            box = tk.Canvas(
                self.progress_frame,
                width=box_size,
                height=box_size,
                bg="#dddddd",
                highlightthickness=2,
                highlightbackground="#999999",
            )
            box.pack(side=tk.LEFT, padx=3)
            self.progress_boxes.append(box)

    def _update_progress_box(self, round_index: int, correct: bool) -> None:
        """Update a progress box color based on result."""
        if round_index < len(self.progress_boxes):
            color = "#4CAF50" if correct else "#f44336"  # Green or Red
            self.progress_boxes[round_index].configure(bg=color)

    def _create_image_buttons(self, num_images: int) -> None:
        """Create image buttons for the round."""
        # Clear existing containers, buttons, and labels
        for container in self.image_containers:
            container.destroy()
        self.image_containers.clear()
        self.image_buttons.clear()
        self.image_name_labels.clear()

        # Calculate optimal grid layout
        # For 1-4 images: 1 row, for 5-8 images: 2 rows
        if num_images <= 4:
            cols = num_images
            rows = 1
        else:
            cols = 4  # Always 4 columns for 5-8 images
            rows = 2

        # Get actual dimensions of images_frame
        self.root.update_idletasks()
        frame_width = self.images_frame.winfo_width()
        frame_height = self.images_frame.winfo_height()

        # Fallback to window size minus top bar if frame not yet sized
        if frame_width < 100:
            frame_width = (self.root.winfo_width() or self.config.window_width) - 40
        if frame_height < 100:
            frame_height = (self.root.winfo_height() or self.config.window_height) - 200

        # Calculate button size with padding
        padding = 8
        available_width = frame_width - (cols + 1) * padding * 2
        available_height = frame_height - (rows + 1) * padding * 2

        # Account for name labels if enabled (reserve space for label + padding)
        label_height = 30 if self.config.show_image_names else 0
        available_height -= rows * label_height

        button_width = available_width // cols
        button_height = available_height // rows
        button_size = max(80, min(button_width, button_height))

        # Center the grid in the images_frame
        for i in range(cols):
            self.images_frame.columnconfigure(i, weight=1)
        for i in range(rows):
            self.images_frame.rowconfigure(i, weight=1)

        # Create grid of buttons (with optional name labels)
        show_names = self.config.show_image_names
        for i in range(num_images):
            row = i // cols
            col = i % cols

            # Create container frame for button + label
            container = tk.Frame(self.images_frame, bg=self.config.background_color)
            container.grid(row=row, column=col, padx=padding, pady=padding)
            self.image_containers.append(container)

            button = ImageButton(
                container,
                size=(button_size, button_size),
                on_click=self._on_image_click,
                bg="white",
            )
            button.pack()
            button.set_enabled(True)
            self.image_buttons.append(button)

            # Create name label frame (will be populated when images are loaded)
            if show_names:
                name_frame = tk.Frame(container, bg=self.config.background_color)
                name_frame.pack(pady=(2, 0))
                self.image_name_labels.append(name_frame)

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

        # Update letter display (uppercase, optionally with lowercase)
        if self.config.show_lowercase:
            letter_display = f"{self.current_letter} {self.current_letter.lower()}"
        else:
            letter_display = self.current_letter
        self.letter_button.configure(text=letter_display)

        # Play letter sound if available
        self._play_letter_sound(self.current_letter)

        # Get images for this round
        try:
            self.current_images, self.correct_index = select_round_images(
                self.config.images_folder,
                self.current_letter,
                self.config.pictures_per_round,
                self.available_letters,
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        # Create buttons but keep them hidden initially if delay is set
        self._create_image_buttons(len(self.current_images))

        # Load images into buttons and populate name labels
        for i, (button, image_path) in enumerate(
            zip(self.image_buttons, self.current_images)
        ):
            button.load_image(image_path)
            button.clear_highlight()
            button.set_enabled(False)  # Disabled until shown

            # Populate name label if enabled
            if self.config.show_image_names and i < len(self.image_name_labels):
                self._set_image_name_label(self.image_name_labels[i], image_path.stem)

        self.rounds_played += 1

        # Show images after delay, or immediately if no delay
        if self.config.letter_display_delay_ms > 0:
            # Hide image containers initially
            for container in self.image_containers:
                container.grid_remove()
            # Show after delay
            self.root.after(self.config.letter_display_delay_ms, self._show_images)
        else:
            self._show_images()

    def _set_image_name_label(self, name_frame: tk.Frame, name: str) -> None:
        """Set the image name label with the first letter bold and bigger."""
        # Clear existing content
        for widget in name_frame.winfo_children():
            widget.destroy()

        if not name:
            return

        bg_color = self.config.background_color
        font_size = 12
        first_letter_size = 20  # Slightly bigger for the first letter

        # First letter (bold and bigger)
        first_letter = name[0].upper()
        first_label = tk.Label(
            name_frame,
            text=first_letter,
            font=("Arial", first_letter_size, "bold"),
            bg=bg_color,
            fg="#333333",
            padx=0,
        )
        first_label.pack(side=tk.LEFT, padx=0)

        # Rest of the name (normal, no space)
        if len(name) > 1:
            rest = name[1:]
            rest_label = tk.Label(
                name_frame,
                text=rest,
                font=("Arial", font_size),
                bg=bg_color,
                fg="#333333",
                padx=0,
            )
            rest_label.pack(side=tk.LEFT, padx=0)

    def _play_letter_sound(self, letter: str) -> None:
        """Play the sound file for the given letter if available."""
        if not self.config.sound_enabled:
            return

        sounds_folder = self.config.sounds_folder
        if not sounds_folder or not sounds_folder.exists():
            return

        # Look for sound file (case-insensitive)
        letter_lower = letter.lower()
        for sound_file in sounds_folder.iterdir():
            if sound_file.suffix.lower() == ".wav":
                if sound_file.stem.lower() == letter_lower:
                    try:
                        winsound.PlaySound(
                            str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC
                        )
                    except Exception:
                        pass  # Silently ignore sound errors
                    break

    def _play_sound(self, sound_path: Path | None) -> None:
        """Play a sound file if it exists."""
        if not self.config.sound_enabled:
            return
        if not sound_path or not sound_path.exists():
            return
        try:
            winsound.PlaySound(
                str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        except Exception:
            pass  # Silently ignore sound errors

    def _show_images(self) -> None:
        """Show the image buttons and enable them."""
        # Re-show all containers in grid (buttons are inside containers now)
        cols = min(len(self.image_containers), 4)
        for i, container in enumerate(self.image_containers):
            row = i // cols
            col = i % cols
            container.grid(row=row, column=col, padx=10, pady=10)

        # Enable all buttons
        for button in self.image_buttons:
            button.set_enabled(True)

    def _on_image_click(self, button: ImageButton) -> None:
        """Handle image button click."""
        clicked_index = self.image_buttons.index(button)
        is_correct = clicked_index == self.correct_index

        # Disable all buttons
        for btn in self.image_buttons:
            btn.set_enabled(False)

        # Record round result
        result = RoundResult(
            letter=self.current_letter,
            was_correct=is_correct,
            chosen_image=self.current_images[clicked_index],
            correct_image=self.current_images[self.correct_index],
        )
        self.round_results.append(result)

        # Update progress indicator
        if self.config.max_rounds > 0:
            self._update_progress_box(self.rounds_played - 1, is_correct)

        if is_correct:
            # Correct answer!
            button.set_highlight("#00ff00")  # Green
            self._play_sound(self.config.correct_sound)
            self.score += 1

            # Check if game is complete
            if (
                self.config.max_rounds > 0
                and self.rounds_played >= self.config.max_rounds
            ):
                self.root.after(self.config.next_round_delay_ms, self._show_summary)
            else:
                # Auto-advance after delay
                self.root.after(self.config.next_round_delay_ms, self.start_new_round)
        else:
            # Wrong answer
            button.set_highlight("#ff0000")  # Red
            self._play_sound(self.config.wrong_sound)
            # Highlight the correct answer
            self.image_buttons[self.correct_index].set_highlight("#0066ff")

            # Check if game is complete
            if (
                self.config.max_rounds > 0
                and self.rounds_played >= self.config.max_rounds
            ):
                self.root.after(self.config.next_round_delay_ms, self._show_summary)
            else:
                # Auto-advance after delay
                self.root.after(self.config.next_round_delay_ms, self.start_new_round)

    def _show_summary(self) -> None:
        """Show the game summary in the main game window."""
        # Clear the main frame content
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.progress_boxes.clear()
        self.image_buttons.clear()

        bg_color = self.config.background_color

        # Number of columns based on number of results
        cols = min(6, len(self.round_results))

        # Header
        header_frame = tk.Frame(self.main_frame, bg=bg_color)
        header_frame.pack(pady=20)

        tk.Label(
            header_frame,
            text="🎉 Game Complete! 🎉",
            font=("Arial", 28, "bold"),
            bg=bg_color,
            fg="#333333",
        ).pack()

        tk.Label(
            header_frame,
            text=f"Score: {self.score} / {len(self.round_results)}",
            font=("Arial", 20),
            bg=bg_color,
            fg="#666666",
        ).pack(pady=(10, 0))

        # Scrollable results area
        canvas = tk.Canvas(self.main_frame, bg=bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.main_frame, orient="vertical", command=canvas.yview
        )
        results_frame = tk.Frame(canvas, bg=bg_color)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            # Center the results frame horizontally in the canvas
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        results_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas_window = canvas.create_window((0, 0), window=results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store photo references to prevent garbage collection
        self._summary_photos: list[ImageTk.PhotoImage] = []

        # Configure columns to center content
        for c in range(cols):
            results_frame.columnconfigure(c, weight=1)

        # Display each round result
        for i, result in enumerate(self.round_results):
            row = i // cols
            col = i % cols

            # Result card
            card_color = (
                "#c8e6c9" if result.was_correct else "#ffcdd2"
            )  # Light green or light red
            border_color = "#4CAF50" if result.was_correct else "#f44336"

            card = tk.Frame(
                results_frame,
                bg=card_color,
                highlightthickness=3,
                highlightbackground=border_color,
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Letter label
            tk.Label(
                card,
                text=result.letter,
                font=("Arial", 36, "bold"),
                bg=card_color,
                fg=border_color,
            ).pack(pady=(10, 5))

            # Image (show chosen image)
            try:
                img = Image.open(result.chosen_image)
                img.thumbnail((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._summary_photos.append(photo)

                img_label = tk.Label(card, image=photo, bg=card_color)
                img_label.pack(pady=5)

                # Show filename
                tk.Label(
                    card,
                    text=result.chosen_image.stem,
                    font=("Arial", 10),
                    bg=card_color,
                    fg="#333333",
                ).pack(pady=(0, 10))
            except Exception:
                tk.Label(
                    card,
                    text="(image)",
                    font=("Arial", 12),
                    bg=card_color,
                ).pack(pady=(5, 10))

        # Buttons at bottom
        button_frame = tk.Frame(self.main_frame, bg=bg_color)
        button_frame.pack(pady=20, side=tk.BOTTOM)

        tk.Button(
            button_frame,
            text="Play Again",
            font=("Arial", 14),
            command=self._restart_game,
            bg=self.config.play_again_color,
            fg="white",
            activebackground=self.config.play_again_hover,
            activeforeground="white",
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Main Menu",
            font=("Arial", 14),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Quit",
            font=("Arial", 14),
            command=self.root.quit,
            bg=self.config.quit_color,
            fg="white",
            activebackground=self.config.quit_hover,
            activeforeground="white",
        ).pack(side=tk.LEFT, padx=10)

    def _go_to_menu(self) -> None:
        """Close game and signal to return to menu."""
        # Clear the game frame
        self.main_frame.destroy()
        self.on_menu_callback()

    def _restart_game(self) -> None:
        """Restart the game for a new session."""
        # Clear the summary content
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Reset game state
        self.score = 0
        self.rounds_played = 0
        self.round_results.clear()
        self.letter_queue.clear()
        self.progress_boxes.clear()
        self.image_buttons.clear()

        # Rebuild the game UI
        self._setup_ui_content()

        # Start new game
        self.start_new_round()

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

    def destroy(self) -> None:
        """Clean up the game frame."""
        self.main_frame.destroy()


@dataclass
class QuizRoundResult:
    """Store the result of a single quiz round."""

    image_path: Path
    correct_letter: str
    chosen_letter: str
    was_correct: bool


class LetterQuizGame:
    """Letter Quiz game - guess the first letter of displayed images."""

    def __init__(
        self, config: Config, root: tk.Tk, on_menu_callback: Callable[[], None]
    ):
        self.config = config
        self.root = root
        self.on_menu_callback = on_menu_callback
        self.available_letters: list[str] = []
        self.all_images: list[Path] = []
        self.image_queue: list[Path] = []
        self.current_image: Path | None = None
        self.current_letter: str = ""
        self.score: int = 0
        self.rounds_played: int = 0
        self.round_results: list[QuizRoundResult] = []
        self.progress_boxes: list[tk.Canvas] = []
        self.letter_buttons: list[tk.Button] = []
        self.photo_ref: ImageTk.PhotoImage | None = None
        self._summary_photos: list[ImageTk.PhotoImage] = []

        self._setup_ui()
        self._load_game_data()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        bg_color = self.config.background_color

        # Main container
        self.main_frame = tk.Frame(self.root, bg=bg_color)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        self._setup_ui_content()

    def _setup_ui_content(self) -> None:
        """Set up the game UI content inside main_frame."""
        bg_color = self.config.background_color

        # Top bar: Progress (left), Title (center), Buttons (right)
        self.top_bar = tk.Frame(self.main_frame, bg=bg_color)
        self.top_bar.pack(fill=tk.X)

        self.top_bar.columnconfigure(0, weight=1)
        self.top_bar.columnconfigure(1, weight=1)
        self.top_bar.columnconfigure(2, weight=1)

        # Left: Progress indicator
        if self.config.max_rounds > 0:
            self.progress_frame = tk.Frame(self.top_bar, bg=bg_color)
            self.progress_frame.grid(row=0, column=0, sticky="w")
            self._create_progress_boxes()

        # Right: Menu and Quit buttons
        buttons_frame = tk.Frame(self.top_bar, bg=bg_color)
        buttons_frame.grid(row=0, column=2, sticky="e")

        tk.Button(
            buttons_frame,
            text="Menu",
            font=("Arial", 10),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
            padx=8,
            pady=2,
        ).pack(side=tk.LEFT, padx=2)

        tk.Button(
            buttons_frame,
            text="Quit",
            font=("Arial", 10),
            command=self._quit_game,
            bg=self.config.quit_color,
            fg="white",
            activebackground=self.config.quit_hover,
            activeforeground="white",
            padx=8,
            pady=2,
        ).pack(side=tk.LEFT, padx=2)

        # Image display area
        self.image_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.image_frame.pack(expand=True, fill=tk.BOTH, pady=20)

        self.image_label = tk.Label(
            self.image_frame, bg="white", relief=tk.RAISED, bd=3
        )
        self.image_label.pack(expand=True)

        # Image name label (optional)
        self.image_name_frame = tk.Frame(self.image_frame, bg=bg_color)
        self.image_name_frame.pack(pady=(10, 0))

        # Letter buttons area
        self.letters_frame = tk.Frame(self.main_frame, bg=bg_color)
        self.letters_frame.pack(pady=20)

    def _create_progress_boxes(self) -> None:
        """Create progress indicator boxes."""
        self.progress_boxes.clear()
        max_rounds = self.config.max_rounds

        for i in range(max_rounds):
            box = tk.Canvas(
                self.progress_frame,
                width=20,
                height=20,
                bg="#e0e0e0",
                highlightthickness=1,
                highlightbackground="#999999",
            )
            box.pack(side=tk.LEFT, padx=3)
            self.progress_boxes.append(box)

    def _update_progress_box(self, round_index: int, correct: bool) -> None:
        """Update a progress box color based on result."""
        if round_index < len(self.progress_boxes):
            color = "#4CAF50" if correct else "#f44336"
            self.progress_boxes[round_index].configure(bg=color)

    def _load_game_data(self) -> None:
        """Load available letters and images."""
        self.available_letters = sorted(
            get_available_letters(self.config.images_folder)
        )

        if len(self.available_letters) < 3:
            messagebox.showerror(
                "Error",
                "Need at least 3 different letters for Letter Quiz mode.\n"
                f"Found only: {', '.join(self.available_letters) or 'none'}",
            )
            self._go_to_menu()
            return

        # Collect all images
        self.all_images = []
        for letter in self.available_letters:
            self.all_images.extend(
                get_images_for_letter(self.config.images_folder, letter)
            )

        if not self.all_images:
            messagebox.showerror("Error", "No images found!")
            self._go_to_menu()
            return

        # Start first round
        self.start_new_round()

    def _get_next_image(self) -> Path:
        """Get the next image, reshuffling when all have been used."""
        if not self.image_queue:
            self.image_queue = list(self.all_images)
            random.shuffle(self.image_queue)
        return self.image_queue.pop()

    def start_new_round(self) -> None:
        """Start a new round with a random image."""
        # Check if game is complete
        max_rounds = self.config.max_rounds
        if max_rounds > 0 and self.rounds_played >= max_rounds:
            self._show_summary()
            return

        # Get next image
        self.current_image = self._get_next_image()
        self.current_letter = self.current_image.stem[0].upper()

        # Display the image
        self._display_image()

        # Create letter choice buttons
        self._create_letter_buttons()

        self.rounds_played += 1

    def _display_image(self) -> None:
        """Display the current image."""
        if not self.current_image:
            return

        try:
            img = Image.open(self.current_image)
            # Make image larger for quiz mode
            img.thumbnail((350, 350), Image.Resampling.LANCZOS)
            self.photo_ref = ImageTk.PhotoImage(img)
            self.image_label.configure(image=self.photo_ref)
        except Exception:
            self.image_label.configure(text="(error)", image="")

        # Show image name if enabled
        for widget in self.image_name_frame.winfo_children():
            widget.destroy()

        if self.config.show_image_names and self.current_image:
            name = self.current_image.stem
            bg_color = self.config.background_color

            # First letter bold and bigger
            first_label = tk.Label(
                self.image_name_frame,
                text=name[0].upper(),
                font=("Arial", 16, "bold"),
                bg=bg_color,
                fg="#333333",
            )
            first_label.pack(side=tk.LEFT)

            if len(name) > 1:
                rest_label = tk.Label(
                    self.image_name_frame,
                    text=name[1:],
                    font=("Arial", 14),
                    bg=bg_color,
                    fg="#333333",
                )
                rest_label.pack(side=tk.LEFT)

    def _create_letter_buttons(self) -> None:
        """Create letter choice buttons based on pictures_per_round setting."""
        # Clear existing buttons
        for btn in self.letter_buttons:
            btn.destroy()
        self.letter_buttons.clear()

        # Number of choices from config (same as pictures_per_round)
        num_choices = self.config.pictures_per_round

        # Get wrong letters (excluding correct one)
        wrong_letters = [l for l in self.available_letters if l != self.current_letter]
        random.shuffle(wrong_letters)
        wrong_choices = wrong_letters[: num_choices - 1]

        # Combine and shuffle
        choices = [self.current_letter] + wrong_choices
        random.shuffle(choices)

        # Create buttons
        for letter in choices:
            btn = tk.Button(
                self.letters_frame,
                text=letter,
                font=("Arial", 36, "bold"),
                width=4,
                height=2,
                bg=self.config.quiz_color,
                fg="white",
                activebackground=self.config.quiz_hover,
                activeforeground="white",
                command=lambda l=letter: self._on_letter_click(l),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=15)
            self.letter_buttons.append(btn)

    def _on_letter_click(self, chosen_letter: str) -> None:
        """Handle letter button click."""
        is_correct = chosen_letter == self.current_letter

        # Disable all buttons
        for btn in self.letter_buttons:
            btn.configure(state=tk.DISABLED, cursor="")

        # Record result
        result = QuizRoundResult(
            image_path=self.current_image,
            correct_letter=self.current_letter,
            chosen_letter=chosen_letter,
            was_correct=is_correct,
        )
        self.round_results.append(result)

        # Update progress
        if self.config.max_rounds > 0:
            self._update_progress_box(self.rounds_played - 1, is_correct)

        # Highlight correct/wrong
        for btn in self.letter_buttons:
            btn_letter = btn.cget("text")
            if btn_letter == self.current_letter:
                btn.configure(bg="#4CAF50")  # Green for correct
            elif btn_letter == chosen_letter and not is_correct:
                btn.configure(bg="#f44336")  # Red for wrong choice

        if is_correct:
            self.score += 1
            self._play_sound(self.config.correct_sound)
        else:
            self._play_sound(self.config.wrong_sound)

        # Next round after delay
        self.root.after(self.config.next_round_delay_ms, self.start_new_round)

    def _play_sound(self, sound_path: Path | None) -> None:
        """Play a sound file if it exists."""
        if not self.config.sound_enabled:
            return
        if not sound_path or not sound_path.exists():
            return
        try:
            winsound.PlaySound(
                str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC
            )
        except Exception:
            pass

    def _show_summary(self) -> None:
        """Show the game summary."""
        # Clear the main frame content
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.progress_boxes.clear()
        self.letter_buttons.clear()
        self._summary_photos.clear()

        bg_color = self.config.background_color
        cols = min(6, len(self.round_results))

        # Header
        header_frame = tk.Frame(self.main_frame, bg=bg_color)
        header_frame.pack(pady=20)

        tk.Label(
            header_frame,
            text="🎉 Quiz Complete! 🎉",
            font=("Arial", 28, "bold"),
            bg=bg_color,
            fg="#333333",
        ).pack()

        tk.Label(
            header_frame,
            text=f"Score: {self.score} / {len(self.round_results)}",
            font=("Arial", 20),
            bg=bg_color,
            fg="#666666",
        ).pack(pady=(10, 0))

        # Scrollable results area
        canvas = tk.Canvas(self.main_frame, bg=bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.main_frame, orient="vertical", command=canvas.yview
        )
        results_frame = tk.Frame(canvas, bg=bg_color)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        results_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas_window = canvas.create_window((0, 0), window=results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure columns for centering
        for c in range(cols):
            results_frame.columnconfigure(c, weight=1)

        # Display each round result
        for i, result in enumerate(self.round_results):
            row = i // cols
            col = i % cols

            card_color = "#c8e6c9" if result.was_correct else "#ffcdd2"
            border_color = "#4CAF50" if result.was_correct else "#f44336"

            card = tk.Frame(
                results_frame,
                bg=card_color,
                highlightthickness=3,
                highlightbackground=border_color,
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Show chosen letter vs correct letter
            if result.was_correct:
                letter_text = result.correct_letter
                letter_color = "#4CAF50"
            else:
                letter_text = f"{result.chosen_letter} → {result.correct_letter}"
                letter_color = "#f44336"

            tk.Label(
                card,
                text=letter_text,
                font=("Arial", 24, "bold"),
                bg=card_color,
                fg=letter_color,
            ).pack(pady=(10, 5))

            # Image
            try:
                img = Image.open(result.image_path)
                img.thumbnail((120, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._summary_photos.append(photo)

                img_label = tk.Label(card, image=photo, bg=card_color)
                img_label.pack(pady=5)

                # Show filename
                tk.Label(
                    card,
                    text=result.image_path.stem,
                    font=("Arial", 10),
                    bg=card_color,
                    fg="#333333",
                ).pack(pady=(0, 10))
            except Exception:
                tk.Label(card, text="(image)", font=("Arial", 12), bg=card_color).pack(
                    pady=(5, 10)
                )

        # Buttons at bottom
        button_frame = tk.Frame(self.main_frame, bg=bg_color)
        button_frame.pack(pady=20, side=tk.BOTTOM)

        tk.Button(
            button_frame,
            text="Play Again",
            font=("Arial", 14),
            command=self._restart_game,
            bg=self.config.play_again_color,
            fg="white",
            activebackground=self.config.play_again_hover,
            activeforeground="white",
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Main Menu",
            font=("Arial", 14),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Quit",
            font=("Arial", 14),
            command=self._quit_game,
            bg=self.config.quit_color,
            fg="white",
            activebackground=self.config.quit_hover,
            activeforeground="white",
        ).pack(side=tk.LEFT, padx=10)

    def _restart_game(self) -> None:
        """Restart the game."""
        self.score = 0
        self.rounds_played = 0
        self.round_results.clear()
        self.image_queue.clear()
        self._summary_photos.clear()
        self.progress_boxes.clear()
        self.letter_buttons.clear()

        # Rebuild UI
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self._setup_ui_content()

        self.start_new_round()

    def _go_to_menu(self) -> None:
        """Return to main menu."""
        self.main_frame.destroy()
        self.on_menu_callback()

    def _quit_game(self) -> None:
        """Quit the game."""
        if self.rounds_played > 0 and self.rounds_played < self.config.max_rounds:
            result = messagebox.askyesno("Quit Game", "Are you sure you want to quit?")
            if result:
                self.root.quit()
        else:
            self.root.quit()

    def destroy(self) -> None:
        """Clean up the game frame."""
        self.main_frame.destroy()


class LettersView:
    """Letters browsing mode - view all letters and their images."""

    def __init__(
        self,
        config: Config,
        root: tk.Tk,
        images_folder: Path,
        on_menu_callback: Callable[[], None],
    ):
        self.config = config
        self.root = root
        self.images_folder = images_folder
        self.on_menu_callback = on_menu_callback
        self.photo_refs: list[ImageTk.PhotoImage] = []  # Prevent garbage collection

        self.bg_color = config.background_color

        # Main frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Get available letters
        self.available_letters = sorted(get_available_letters(images_folder))

        # Show letters grid
        self._show_letters_grid()

    def _show_letters_grid(self) -> None:
        """Show grid of all available letters."""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.photo_refs.clear()

        # Header
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(pady=20)

        tk.Label(
            header_frame,
            text="🔤 Choose a Letter 🔤",
            font=("Arial", 32, "bold"),
            bg=self.bg_color,
            fg="#333333",
        ).pack()

        # Scrollable letters area
        canvas = tk.Canvas(self.main_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.main_frame, orient="vertical", command=canvas.yview
        )
        letters_frame = tk.Frame(canvas, bg=self.bg_color)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        letters_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas_window = canvas.create_window((0, 0), window=letters_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create letter buttons in a grid
        cols = 6
        for i, letter in enumerate(self.available_letters):
            row = i // cols
            col = i % cols

            # Count images for this letter
            images = get_images_for_letter(self.images_folder, letter)
            count = len(images)

            btn = tk.Button(
                letters_frame,
                text=f"{letter}\n({count})",
                font=("Arial", 28, "bold"),
                width=4,
                height=2,
                bg=self.config.letters_color,
                fg="white",
                activebackground=self.config.letters_hover,
                activeforeground="white",
                command=lambda l=letter: self._show_letter_images(l),
                cursor="hand2",
            )
            btn.grid(row=row, column=col, padx=10, pady=10)

        # Configure columns for centering
        for c in range(cols):
            letters_frame.columnconfigure(c, weight=1)

        # Menu button at bottom
        button_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        button_frame.pack(pady=20, side=tk.BOTTOM)

        tk.Button(
            button_frame,
            text="Main Menu",
            font=("Arial", 16),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
            width=14,
            height=2,
        ).pack()

    def _show_letter_images(self, letter: str) -> None:
        """Show all images for a specific letter."""
        # Play letter sound
        self._play_letter_sound(letter)

        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.photo_refs.clear()

        # Header with letter
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(pady=20)

        tk.Label(
            header_frame,
            text=f"{letter} {letter.lower()}",
            font=("Arial", 48, "bold"),
            bg=self.bg_color,
            fg=self.config.letters_color,
        ).pack()

        # Get images for this letter
        images = get_images_for_letter(self.images_folder, letter)

        # Scrollable images area
        canvas = tk.Canvas(self.main_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(
            self.main_frame, orient="vertical", command=canvas.yview
        )
        images_frame = tk.Frame(canvas, bg=self.bg_color)

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        images_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas_window = canvas.create_window((0, 0), window=images_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Buttons at bottom (create first so they're always visible)
        button_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        button_frame.pack(pady=20, side=tk.BOTTOM)

        tk.Button(
            button_frame,
            text="Back to Letters",
            font=("Arial", 16),
            command=self._show_letters_grid,
            bg=self.config.letters_color,
            fg="white",
            activebackground=self.config.letters_hover,
            activeforeground="white",
            width=14,
            height=2,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Main Menu",
            font=("Arial", 16),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
            width=14,
            height=2,
        ).pack(side=tk.LEFT, padx=10)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Display images in a grid
        cols = min(4, len(images))
        image_size = 180

        for i, image_path in enumerate(images):
            row = i // cols
            col = i % cols

            # Card frame
            card = tk.Frame(
                images_frame,
                bg="white",
                highlightthickness=2,
                highlightbackground="#cccccc",
            )
            card.grid(row=row, column=col, padx=10, pady=10)

            # Load and display image
            try:
                img = Image.open(image_path)
                img.thumbnail((image_size, image_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photo_refs.append(photo)

                img_label = tk.Label(card, image=photo, bg="white")
                img_label.pack(padx=5, pady=5)

                # Image name with bold first letter
                name_frame = tk.Frame(card, bg="white")
                name_frame.pack(pady=(0, 5))

                name = image_path.stem
                if name:
                    # First letter bold and bigger
                    first_label = tk.Label(
                        name_frame,
                        text=name[0].upper(),
                        font=("Arial", 14, "bold"),
                        bg="white",
                        fg="#333333",
                    )
                    first_label.pack(side=tk.LEFT)

                    if len(name) > 1:
                        rest_label = tk.Label(
                            name_frame,
                            text=name[1:],
                            font=("Arial", 12),
                            bg="white",
                            fg="#333333",
                        )
                        rest_label.pack(side=tk.LEFT)
            except Exception:
                tk.Label(card, text="(error)", bg="white").pack(padx=5, pady=5)

        # Configure columns for centering
        for c in range(cols):
            images_frame.columnconfigure(c, weight=1)

    def _play_letter_sound(self, letter: str) -> None:
        """Play the sound file for the given letter if available."""
        if not self.config.sound_enabled:
            return

        sounds_folder = self.config.sounds_folder
        if not sounds_folder or not sounds_folder.exists():
            return

        # Look for sound file (case-insensitive)
        letter_lower = letter.lower()
        for sound_file in sounds_folder.iterdir():
            if sound_file.suffix.lower() == ".wav":
                if sound_file.stem.lower() == letter_lower:
                    try:
                        winsound.PlaySound(
                            str(sound_file), winsound.SND_FILENAME | winsound.SND_ASYNC
                        )
                    except Exception:
                        pass
                    break

    def _go_to_menu(self) -> None:
        """Return to the main menu."""
        self.main_frame.destroy()
        self.on_menu_callback()

    def destroy(self) -> None:
        """Clean up the letters view."""
        self.main_frame.destroy()


class MenuView:
    """Menu view for game settings before starting."""

    def __init__(
        self,
        config: Config,
        root: tk.Tk,
        on_start_callback: Callable[[dict], None],
        on_letters_callback: Callable[[dict], None] | None = None,
        on_quiz_callback: Callable[[dict], None] | None = None,
    ):
        self.config = config
        self.root = root
        self.on_start_callback = on_start_callback
        self.on_letters_callback = on_letters_callback
        self.on_quiz_callback = on_quiz_callback
        self.icon_photos = []  # Store icon photos to prevent garbage collection

        bg_color = config.background_color

        # Main container with centering
        self.main_container = tk.Frame(self.root, bg=bg_color)
        self.main_container.place(relx=0.5, rely=0.5, anchor="center")

        # Title frame with optional icons
        title_frame = tk.Frame(self.main_container, bg=bg_color)
        title_frame.pack(pady=(0, 40))

        # Load icon for title if available
        icon_size = config.icon_size
        if config.icon_image and config.icon_image.exists():
            try:
                icon_img = Image.open(config.icon_image)
                icon_img.thumbnail((icon_size, icon_size), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_img)
                self.icon_photos.append(icon_photo)

                # Left icon
                tk.Label(title_frame, image=icon_photo, bg=bg_color).pack(
                    side=tk.LEFT, padx=(0, 15)
                )

                # Title text
                tk.Label(
                    title_frame,
                    text=config.game_name,
                    font=("Arial", 48, "bold"),
                    bg=bg_color,
                    fg="#333333",
                ).pack(side=tk.LEFT)
            except Exception:
                # Fallback to text-only title
                tk.Label(
                    title_frame,
                    text=f"🔤 {config.game_name} 🔤",
                    font=("Arial", 48, "bold"),
                    bg=bg_color,
                    fg="#333333",
                ).pack()
        else:
            # No icon, use emoji
            tk.Label(
                title_frame,
                text=f"🔤 {config.game_name} 🔤",
                font=("Arial", 48, "bold"),
                bg=bg_color,
                fg="#333333",
            ).pack()

        # Settings frame
        settings_frame = tk.Frame(self.main_container, bg=bg_color)
        settings_frame.pack(pady=20)

        # Images folder
        folder_row = tk.Frame(settings_frame, bg=bg_color)
        folder_row.pack(pady=15, fill=tk.X)

        tk.Label(
            folder_row,
            text="Images Folder:",
            font=("Arial", 18),
            bg=bg_color,
            width=18,
            anchor="e",
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.folder_var = tk.StringVar(value=str(config.images_folder))
        self.folder_entry = tk.Entry(
            folder_row,
            textvariable=self.folder_var,
            font=("Arial", 16),
            width=35,
        )
        self.folder_entry.pack(side=tk.LEFT)

        tk.Button(
            folder_row,
            text="Browse...",
            font=("Arial", 14),
            command=self._browse_folder,
            padx=15,
            pady=5,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Pictures per round with +/- buttons
        pictures_row = tk.Frame(settings_frame, bg=bg_color)
        pictures_row.pack(pady=15, fill=tk.X)

        tk.Label(
            pictures_row,
            text="Pictures per Round:",
            font=("Arial", 18),
            bg=bg_color,
            width=18,
            anchor="e",
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.pictures_var = tk.IntVar(value=config.pictures_per_round)

        tk.Button(
            pictures_row,
            text="−",
            font=("Arial", 24, "bold"),
            command=lambda: self._adjust_value(self.pictures_var, -1, 2, 8),
            width=3,
            height=1,
            bg="#e0e0e0",
        ).pack(side=tk.LEFT)

        tk.Label(
            pictures_row,
            textvariable=self.pictures_var,
            font=("Arial", 24, "bold"),
            bg=bg_color,
            width=4,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            pictures_row,
            text="+",
            font=("Arial", 24, "bold"),
            command=lambda: self._adjust_value(self.pictures_var, 1, 2, 8),
            width=3,
            height=1,
            bg="#e0e0e0",
        ).pack(side=tk.LEFT)

        # Number of rounds with +/- buttons
        rounds_row = tk.Frame(settings_frame, bg=bg_color)
        rounds_row.pack(pady=15, fill=tk.X)

        tk.Label(
            rounds_row,
            text="Number of Rounds:",
            font=("Arial", 18),
            bg=bg_color,
            width=18,
            anchor="e",
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.rounds_var = tk.IntVar(
            value=config.max_rounds if config.max_rounds > 0 else 10
        )

        tk.Button(
            rounds_row,
            text="−",
            font=("Arial", 24, "bold"),
            command=lambda: self._adjust_value(self.rounds_var, -1, 1, 10),
            width=3,
            height=1,
            bg="#e0e0e0",
        ).pack(side=tk.LEFT)

        tk.Label(
            rounds_row,
            textvariable=self.rounds_var,
            font=("Arial", 24, "bold"),
            bg=bg_color,
            width=4,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            rounds_row,
            text="+",
            font=("Arial", 24, "bold"),
            command=lambda: self._adjust_value(self.rounds_var, 1, 1, 10),
            width=3,
            height=1,
            bg="#e0e0e0",
        ).pack(side=tk.LEFT)

        # Buttons frame
        button_frame = tk.Frame(self.main_container, bg=bg_color)
        button_frame.pack(pady=40)

        tk.Button(
            button_frame,
            text="Start Game",
            font=("Arial", 20, "bold"),
            command=self._start_game,
            bg=config.play_again_color,
            fg="white",
            activebackground=config.play_again_hover,
            activeforeground="white",
            width=12,
            height=2,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Quiz",
            font=("Arial", 20),
            command=self._start_quiz,
            bg=config.quiz_color,
            fg="white",
            activebackground=config.quiz_hover,
            activeforeground="white",
            width=12,
            height=2,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Letters",
            font=("Arial", 20),
            command=self._start_letters,
            bg=config.letters_color,
            fg="white",
            activebackground=config.letters_hover,
            activeforeground="white",
            width=12,
            height=2,
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="Quit",
            font=("Arial", 20),
            command=self._quit,
            bg=config.quit_color,
            fg="white",
            activebackground=config.quit_hover,
            activeforeground="white",
            width=12,
            height=2,
        ).pack(side=tk.LEFT, padx=10)

    def _start_letters(self) -> None:
        """Start the letters browsing mode."""
        if not self.on_letters_callback:
            return

        folder = Path(self.folder_var.get())
        if not folder.exists():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return
        if not folder.is_dir():
            messagebox.showerror("Error", f"Not a valid folder:\n{folder}")
            return

        # Check for images
        letters = get_available_letters(folder)
        if not letters:
            messagebox.showerror(
                "Error",
                f"No valid images found in:\n{folder}\n\n"
                "Images should start with a letter (e.g., Apple.png, Lion.jpg)",
            )
            return

        settings = {
            "images_folder": folder,
        }
        # Destroy menu view and call letters callback
        self.main_container.destroy()
        self.on_letters_callback(settings)

    def _start_quiz(self) -> None:
        """Start the letter quiz mode."""
        if not self.on_quiz_callback:
            return

        folder = Path(self.folder_var.get())
        if not folder.exists():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return
        if not folder.is_dir():
            messagebox.showerror("Error", f"Not a valid folder:\n{folder}")
            return

        # Check for images
        letters = get_available_letters(folder)
        if not letters:
            messagebox.showerror(
                "Error",
                f"No valid images found in:\n{folder}\n\n"
                "Images should start with a letter (e.g., Apple.png, Lion.jpg)",
            )
            return

        num_choices = self.pictures_var.get()
        if len(letters) < num_choices:
            messagebox.showerror(
                "Error",
                f"Need at least {num_choices} different letters for Quiz mode.\n"
                f"Found only: {', '.join(sorted(letters))}",
            )
            return

        settings = {
            "images_folder": folder,
            "max_rounds": self.rounds_var.get(),
            "num_choices": num_choices,
        }
        # Destroy menu view and call quiz callback
        self.main_container.destroy()
        self.on_quiz_callback(settings)

    def _adjust_value(
        self, var: tk.IntVar, delta: int, min_val: int, max_val: int
    ) -> None:
        """Adjust an IntVar value within bounds."""
        new_val = var.get() + delta
        if min_val <= new_val <= max_val:
            var.set(new_val)

    def _browse_folder(self) -> None:
        """Open folder browser dialog."""
        from tkinter import filedialog

        folder = filedialog.askdirectory(
            initialdir=self.folder_var.get(),
            title="Select Images Folder",
        )
        if folder:
            self.folder_var.set(folder)

    def _start_game(self) -> None:
        """Validate and start the game."""
        folder = Path(self.folder_var.get())
        if not folder.exists():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return
        if not folder.is_dir():
            messagebox.showerror("Error", f"Not a valid folder:\n{folder}")
            return

        # Check for images
        from .images import get_available_letters

        letters = get_available_letters(folder)
        if not letters:
            messagebox.showerror(
                "Error",
                f"No valid images found in:\n{folder}\n\n"
                "Images should start with a letter (e.g., Apple.png, Lion.jpg)",
            )
            return

        settings = {
            "images_folder": folder,
            "pictures_per_round": self.pictures_var.get(),
            "max_rounds": self.rounds_var.get(),
        }
        # Destroy menu view and call start callback
        self.main_container.destroy()
        self.on_start_callback(settings)

    def _quit(self) -> None:
        """Quit without starting."""
        self.root.quit()

    def destroy(self) -> None:
        """Clean up the menu view."""
        self.main_container.destroy()


class GameApp:
    """Main application managing menu and game views in a single window."""

    def __init__(self, config: Config):
        self.config = config
        self.current_view = None
        self.icon_photo = None  # Store icon to prevent garbage collection

        # Create main window
        self.root = tk.Tk()
        self.root.title(config.game_name)
        self.root.configure(bg=config.background_color)

        # Set window icon
        if config.icon_image and config.icon_image.exists():
            try:
                icon_img = Image.open(config.icon_image)
                self.icon_photo = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(True, self.icon_photo)
            except Exception:
                pass  # Silently ignore icon errors

        if config.fullscreen:
            self.root.attributes("-fullscreen", True)
            self.root.bind(
                "<Escape>", lambda e: self.root.attributes("-fullscreen", False)
            )
        else:
            # Start maximized
            self.root.state("zoomed")

        # Show menu initially
        self._show_menu()

    def _show_menu(self) -> None:
        """Show the menu view."""
        self.current_view = MenuView(
            self.config,
            self.root,
            self._start_game,
            self._start_letters,
            self._start_quiz,
        )

    def _start_game(self, settings: dict) -> None:
        """Start the game with given settings."""
        # Update config with user settings
        self.config._data["images_folder"] = str(settings["images_folder"])
        self.config._data["pictures_per_round"] = settings["pictures_per_round"]
        self.config._data["game"]["max_rounds"] = settings["max_rounds"]
        # Update config_dir for proper path resolution
        self.config._config_dir = (
            settings["images_folder"].parent
            if not settings["images_folder"].is_absolute()
            else None
        )

        # Create game view
        self.current_view = AlphabetGame(self.config, self.root, self._show_menu)

    def _start_letters(self, settings: dict) -> None:
        """Start the letters browsing mode."""
        # Update config with user settings
        self.config._data["images_folder"] = str(settings["images_folder"])
        # Update config_dir for proper path resolution
        self.config._config_dir = (
            settings["images_folder"].parent
            if not settings["images_folder"].is_absolute()
            else None
        )

        # Create letters view
        self.current_view = LettersView(
            self.config, self.root, settings["images_folder"], self._show_menu
        )

    def _start_quiz(self, settings: dict) -> None:
        """Start the letter quiz mode."""
        # Update config with user settings
        self.config._data["images_folder"] = str(settings["images_folder"])
        self.config._data["game"]["max_rounds"] = settings["max_rounds"]
        self.config._data["pictures_per_round"] = settings["num_choices"]
        # Update config_dir for proper path resolution
        self.config._config_dir = (
            settings["images_folder"].parent
            if not settings["images_folder"].is_absolute()
            else None
        )

        # Create quiz view
        self.current_view = LetterQuizGame(self.config, self.root, self._show_menu)

    def run(self) -> None:
        """Run the application."""
        self.root.mainloop()


def run_game(config_path: str | Path | None = None) -> None:
    """
    Run the alphabet game.

    Args:
        config_path: Optional path to config file.
    """
    config = Config(config_path)
    app = GameApp(config)
    app.run()
