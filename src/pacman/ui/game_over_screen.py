import arcade
import arcade.gui
from typing import Any, cast

from pacman.window import GameView

UISpace = cast(Any, arcade.gui.UISpace)


class GameOverScreen(arcade.View):
    def __init__(self, score: int, file: str, game: GameView) -> None:
        super().__init__()
        self.score = score
        self.file = file
        self.game = game

        self.manager = arcade.gui.UIManager()

        # Box layout for buttons and texts
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        # Title
        box.add(arcade.gui.UILabel(
            text="Game over!",
            font_size=40,
            bold=True,
        ))

        # Score
        box.add(arcade.gui.UILabel(
            text=f"Score: {self.score}",
            font_size=30,
        ))

        # Spacer between text and buttons
        box.add(UISpace(height=20))

        # Buttons
        button_row = arcade.gui.UIBoxLayout(vertical=False, space_between=20)
        start_button = arcade.gui.UIFlatButton(text="Restart", width=150)
        exit_button = arcade.gui.UIFlatButton(text="Exit", width=150)
        button_row.add(start_button)
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

        @exit_button.event("on_click")
        def on_click_exit_button(event: arcade.gui.UIOnClickEvent) -> None:
            arcade.exit()

    def on_show_view(self) -> None:
        self.window.background_color = arcade.color.DARK_BLUE_GRAY
        self.manager.enable()

    def on_hide_view(self) -> None:
        self.manager.disable()

    def on_draw(self) -> None:
        self.clear()
        self.manager.draw()
