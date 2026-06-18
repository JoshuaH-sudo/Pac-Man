import arcade
import arcade.gui
from typing import Any, cast

from pacman.ui.main_menu import MainMenu
from pacman.window import GameView

UISpace = cast(Any, arcade.gui.UISpace)


class PauseMenu(arcade.View):
    """
    The main menu allows the player to:
    - Resume the game
    - Return to the main menu
    """
    def __init__(self,
                 game: GameView, main_menu: MainMenu) -> None:
        super().__init__()
        self.manager = arcade.gui.UIManager()

        self.game = game
        self.main_menu = main_menu

        # Outer Box
        outer_box = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        # Title
        outer_box.add(arcade.gui.UILabel(
            text="Paused",
            font_size=40,
            bold=True,
        ))

        # Buttons
        button_box = arcade.gui.UIBoxLayout(vertical=True, space_between=10)
        resume_button = arcade.gui.UIFlatButton(text="Resume", width=150)
        restart_button = arcade.gui.UIFlatButton(text="Restart game", width=150)
        menu_button = arcade.gui.UIFlatButton(text="Main menu", width=150)
        exit_button = arcade.gui.UIFlatButton(text="Exit game", width=150)
        button_box.add(resume_button)
        button_box.add(restart_button)
        button_box.add(menu_button)
        button_box.add(exit_button)
        outer_box.add(button_box)

        # Spacer between text and buttons
        outer_box.add(UISpace(height=20))

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
            anchor_x="center_x",
            anchor_y="center_y",
            child=outer_box,
        )

        @resume_button.event("on_click")
        def on_click_resume_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.game)

        @restart_button.event("on_click")
        def on_click_restart_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.game)

        @menu_button.event("on_click")
        def on_click_menu_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.main_menu)

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
