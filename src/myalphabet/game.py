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
from .images import get_available_letters, select_round_images


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

    def __init__(self, config: Config):
        self.config = config
        self.available_letters: set[str] = set()
        self.letter_queue: list[str] = []  # Shuffled queue of letters for fair rotation
        self.current_letter: str = ""
        self.correct_index: int = -1
        self.current_images: list[Path] = []  # Images for current round
        self.image_buttons: list[ImageButton] = []
        self.score: int = 0
        self.rounds_played: int = 0
        self.round_results: list[RoundResult] = []  # Track all round results
        self.progress_boxes: list[tk.Canvas] = []  # Progress indicator boxes
        self._return_to_menu: bool = False  # Flag to return to main menu

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
            # Start maximized
            self.root.state("zoomed")

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

        # Set up the game UI content
        self._setup_ui_content()

    def _setup_ui_content(self) -> None:
        """Set up the game UI content inside main_frame."""
        bg_color = self.config.background_color

        # Top bar: Progress (left), Letter (center), Buttons (right)
        self.top_bar = tk.Frame(self.main_frame, bg=bg_color)
        self.top_bar.pack(fill=tk.X, pady=(0, 10))

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
            bg=bg_color,
            fg="#333333",
            activebackground=bg_color,
            activeforeground="#333333",
            bd=0,
            highlightthickness=0,
            command=self._on_letter_click,
            cursor="hand2",
        )
        self.letter_button.pack()

        # Right: Menu and Quit buttons
        self.top_right_frame = tk.Frame(self.top_bar, bg=bg_color)
        self.top_right_frame.grid(row=0, column=2, sticky="e")

        self.menu_button = tk.Button(
            self.top_right_frame,
            text="Main Menu",
            font=("Arial", 14),
            command=self._go_to_menu,
            bg=self.config.menu_color,
            fg="white",
            activebackground=self.config.menu_hover,
            activeforeground="white",
        )
        self.menu_button.pack(side=tk.LEFT, padx=(0, 10))

        self.quit_button = tk.Button(
            self.top_right_frame,
            text="Quit",
            font=("Arial", 14),
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
        # Clear existing buttons
        for button in self.image_buttons:
            button.destroy()
        self.image_buttons.clear()

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

        button_width = available_width // cols
        button_height = available_height // rows
        button_size = max(80, min(button_width, button_height))

        # Center the grid in the images_frame
        for i in range(cols):
            self.images_frame.columnconfigure(i, weight=1)
        for i in range(rows):
            self.images_frame.rowconfigure(i, weight=1)

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
            button.grid(row=row, column=col, padx=padding, pady=padding)
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
        self.letter_button.configure(text=self.current_letter)

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

        # Load images into buttons
        for i, (button, image_path) in enumerate(
            zip(self.image_buttons, self.current_images)
        ):
            button.load_image(image_path)
            button.clear_highlight()
            button.set_enabled(False)  # Disabled until shown

        self.rounds_played += 1

        # Show images after delay, or immediately if no delay
        if self.config.letter_display_delay_ms > 0:
            # Hide image buttons initially
            for button in self.image_buttons:
                button.pack_forget() if button.winfo_manager() == "pack" else None
                button.grid_remove()
            # Show after delay
            self.root.after(self.config.letter_display_delay_ms, self._show_images)
        else:
            self._show_images()

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
        # Re-show all buttons in grid
        cols = min(len(self.image_buttons), 4)
        for i, button in enumerate(self.image_buttons):
            row = i // cols
            col = i % cols
            button.grid(row=row, column=col, padx=10, pady=10)
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

        results_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Store photo references to prevent garbage collection
        self._summary_photos: list[ImageTk.PhotoImage] = []

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
        self._return_to_menu = True
        self.root.quit()

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

    def run(self) -> None:
        """Run the game main loop."""
        self.root.mainloop()
        self.root.destroy()


class MenuWindow:
    """Menu window for game settings before starting."""

    def __init__(self, config: Config):
        self.config = config
        self.result: dict | None = None

        # Create menu window
        self.root = tk.Tk()
        self.root.title("My Alphabet - Settings")
        self.root.configure(bg=config.background_color)

        # Start maximized
        self.root.state("zoomed")

        bg_color = config.background_color

        # Main container with centering
        main_container = tk.Frame(self.root, bg=bg_color)
        main_container.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        tk.Label(
            main_container,
            text=f"🔤 {config.game_name} 🔤",
            font=("Arial", 48, "bold"),
            bg=bg_color,
            fg="#333333",
        ).pack(pady=(0, 40))

        # Settings frame
        settings_frame = tk.Frame(main_container, bg=bg_color)
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
            command=lambda: self._adjust_value(self.rounds_var, -1, 1, 26),
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
            command=lambda: self._adjust_value(self.rounds_var, 1, 1, 26),
            width=3,
            height=1,
            bg="#e0e0e0",
        ).pack(side=tk.LEFT)

        # Buttons frame
        button_frame = tk.Frame(main_container, bg=bg_color)
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
            width=14,
            height=2,
        ).pack(side=tk.LEFT, padx=15)

        tk.Button(
            button_frame,
            text="Quit",
            font=("Arial", 20),
            command=self._quit,
            bg=config.quit_color,
            fg="white",
            activebackground=config.quit_hover,
            activeforeground="white",
            width=14,
            height=2,
        ).pack(side=tk.LEFT, padx=15)

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

        self.result = {
            "images_folder": folder,
            "pictures_per_round": self.pictures_var.get(),
            "max_rounds": self.rounds_var.get(),
        }
        self.root.quit()

    def _quit(self) -> None:
        """Quit without starting."""
        self.result = None
        self.root.quit()

    def run(self) -> dict | None:
        """Run the menu and return settings or None if cancelled."""
        self.root.mainloop()
        self.root.destroy()
        return self.result


def run_game(config_path: str | Path | None = None) -> None:
    """
    Run the alphabet game.

    Args:
        config_path: Optional path to config file.
    """
    config = Config(config_path)

    while True:
        # Show menu window
        menu = MenuWindow(config)
        settings = menu.run()

        if settings is None:
            return  # User cancelled

        # Update config with user settings
        config._data["images_folder"] = str(settings["images_folder"])
        config._data["pictures_per_round"] = settings["pictures_per_round"]
        config._data["game"]["max_rounds"] = settings["max_rounds"]
        # Update config_dir for proper path resolution
        config._config_dir = (
            settings["images_folder"].parent
            if not settings["images_folder"].is_absolute()
            else None
        )

        game = AlphabetGame(config)
        game.run()

        # Check if we should return to menu or exit
        if not game._return_to_menu:
            break  # User quit, exit completely
