import arcade
import arcade.gui
from typing import Any, cast

from pacman.highscore import (HighscoreEntry, load_highscores,
                              save_highscores, sanitize_name)
from pacman.ui.main_menu import MainMenu
from pacman.window import GameView

UISpace = cast(Any, arcade.gui.UISpace)


class EndScreen(arcade.View):
    def __init__(self, message: str, color: arcade.types.Color,
                 score: int, file: str, game: GameView,
                 main_menu: MainMenu | None = None) -> None:
        super().__init__()

        self.score = score
        self.file = file
        self.game = game
        self.main_menu = main_menu

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
        self.input_text = arcade.gui.UIInputText(width=250, height=30,
                                                 font_size=16).with_border()
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
            self.window.show_view(self.game)

        @back_button.event("on_click")
        def on_click_back(event: arcade.gui.UIOnClickEvent) -> None:
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
        self.manager.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        if symbol == arcade.key.ENTER:
            self._save_score()

    def _save_score(self) -> None:
        if not self._saved:
            name = sanitize_name(self.input_text.text)
            existing = load_highscores(self.file)
            existing.append(HighscoreEntry(name=name, score=self.score))
            save_highscores(self.file, existing)
            self._saved = True
