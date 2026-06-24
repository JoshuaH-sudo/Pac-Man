import arcade
import arcade.gui
from arcade.gui.events import UIKeyPressEvent, UITextInputEvent
from typing import Any, cast, Callable

from pacman.core import GameConfig, WINDOW_WIDTH, WINDOW_HEIGHT
from pacman.game import HighScore, HighscoreEntry, GameView, GameState
from pacman.ui.main_menu import MainMenu

UISpace = cast(Any, arcade.gui.UISpace)


class _EnterAwareInputText(arcade.gui.UIInputText):
    """UIInputText that fires a callback on Enter instead of inserting a newline."""

    def __init__(self, on_enter: Callable[[], None], width: float = 300,
                 height: float = 35, font_size: float = 18) -> None:
        super().__init__(width=width, height=height, font_size=font_size)
        self._on_enter = on_enter

    def on_event(self, event: arcade.gui.UIEvent) -> bool | None:
        if isinstance(event, UIKeyPressEvent) and event.symbol == arcade.key.ENTER:
            self._on_enter()
            return True
        if isinstance(event, UITextInputEvent) and event.text in ("\n", "\r"):
            return True  # suppress newline character insertion
        return super().on_event(event)


class EndScreen(arcade.View):
    def __init__(self, message: str, color: arcade.types.Color,
                 score: int, config: GameConfig, game: GameView) -> None:
        super().__init__()

        self.score = score
        self.config = config
        self.game = game
        self.highscore = HighScore(self.config.highscore_filename)

        self.main_menu = None
        self._saved = False

        self.manager = arcade.gui.UIManager()

        # Box layout for buttons and texts
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        # Title
        box.add(arcade.gui.UILabel(
            text=message,
            font_size=40,
            bold=True,
            text_color=color
        ))

        # Score
        box.add(arcade.gui.UILabel(
            text=f"Score: {self.score}",
            font_size=30,
        ))

        # Input user name
        box.add(UISpace(height=20))
        box.add(arcade.gui.UILabel(
            text="Enter your name to save your score:",
            font_size=16,
        ))
        self.input_text = _EnterAwareInputText(on_enter=self._save_score, width=300,
                                               height=35, font_size=18)
        save_button = arcade.gui.UIFlatButton(text="Save", width=50, height=30)
        input_row = arcade.gui.UIBoxLayout(vertical=False, space_between=10)
        input_row.add(self.input_text)
        input_row.add(save_button)
        box.add(input_row)

        # Spacer between text and buttons
        box.add(UISpace(height=20))

        # Buttons
        button_row = arcade.gui.UIBoxLayout(vertical=False, space_between=20)
        start_button = arcade.gui.UIFlatButton(text="Restart", width=150)
        back_button = arcade.gui.UIFlatButton(text="Main menu", width=150)
        exit_button = arcade.gui.UIFlatButton(text="Exit", width=150)
        button_row.add(start_button)
        button_row.add(back_button)
        button_row.add(exit_button)
        box.add(button_row)

        # Anchor the whole box to center
        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
            anchor_x="center_x",
            anchor_y="center_y",
            child=box,
        )

        @start_button.event("on_click")
        def on_click_start_button(event: arcade.gui.UIOnClickEvent) -> None:
            # Reset game state and create a new game
            state = GameState(self.config)
            if not self.main_menu:
                self.main_menu = MainMenu(config)
            self.game = GameView(self.config, state, self.main_menu)
            self.window.show_view(self.game)

        @back_button.event("on_click")
        def on_click_back(event: arcade.gui.UIOnClickEvent) -> None:
            # Create a new main menu and thus a new game
            if not self.main_menu:
                self.main_menu = MainMenu(config)
            if self.main_menu:
                self.window.show_view(self.main_menu)

        @exit_button.event("on_click")
        def on_click_exit_button(event: arcade.gui.UIOnClickEvent) -> None:
            arcade.exit()

        @save_button.event("on_click")
        def on_click_save_button(event: arcade.gui.UIOnClickEvent) -> None:
            self._save_score()

    def on_show_view(self) -> None:
        self.window.background_color = arcade.color.DARK_BLUE_GRAY
        self.manager.enable()

    def on_hide_view(self) -> None:
        self.manager.disable()

    def on_draw(self) -> None:
        self.clear()
        if self._saved:
            arcade.Text("Saved!", WINDOW_WIDTH / 2 - 36, WINDOW_HEIGHT / 2 - 118,
                        font_size=16, align="center").draw()
        self.manager.draw()

    def _save_score(self) -> None:
        if not self._saved:
            name = HighScore.sanitize_name(self.input_text.text)
            existing = self.highscore.load_highscores()
            existing.append(HighscoreEntry(name=name, score=self.score))
            self.highscore.save_highscores(existing)
            self._saved = True
