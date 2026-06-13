import arcade
import arcade.gui

from pacman.highscore import HighscoreEntry
from pacman.window import GameView


class InstructionView(arcade.View):
    def __init__(self, game: GameView, main_menu: "MainMenu | None" = None) -> None:
        super().__init__()
        self.game = game
        self.main_menu = main_menu

        self.manager = arcade.gui.UIManager()

        # Box layout for buttons and texts
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        # Title
        box.add(
            arcade.gui.UILabel(
                text="Instructions",
                font_size=40,
                bold=True,
            )
        )

        # Instruction texts
        instructions_box = arcade.gui.UIBoxLayout(
            vertical=True, space_between=4, align="left"
        )
        for line in [
            "Use arrow keys or WASD to move Pac-Man.",
            "Eat all pacgums within the time limit to complete the level.",
            "Eat a super-pacgum to make ghosts edible.",
            "Avoid ghosts — you lose a life when touched by a ghost.",
            "Game over when all lives are lost.",
        ]:
            instructions_box.add(
                arcade.gui.UILabel(
                    text=line,
                    font_size=18,
                )
            )
        box.add(instructions_box)

        # Spacer between text and buttons
        box.add(arcade.gui.UISpace(height=20))

        # Buttons
        button_row = arcade.gui.UIBoxLayout(vertical=False, space_between=20)
        start_button = arcade.gui.UIFlatButton(text="Start Game", width=150)
        back_button = arcade.gui.UIFlatButton(text="Back", width=150)
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


class MainMenu(arcade.View):
    """
    The main menu allows the player to:
    - start a new game
    - view highscores
    - view instructions
    - exit
    """

    def __init__(self, game: GameView, highscores: list[HighscoreEntry]) -> None:
        super().__init__()
        self.manager = arcade.gui.UIManager()

        self.instruction = InstructionView(game)
        self.game = game
        self.highscores = highscores

        # Outer Box
        outer_box = arcade.gui.UIBoxLayout(vertical=True, space_between=20)
        # Title
        outer_box.add(
            arcade.gui.UILabel(
                text="Pac-Man", font_size=40, bold=True, text_color=arcade.color.YELLOW
            )
        )

        # Buttons
        button_box = arcade.gui.UIBoxLayout(vertical=True, space_between=10)
        start_button = arcade.gui.UIFlatButton(text="Start", width=150)
        instructions_button = arcade.gui.UIFlatButton(text="Instructions", width=150)
        exit_button = arcade.gui.UIFlatButton(text="Exit", width=150)
        button_box.add(start_button)
        button_box.add(instructions_button)
        button_box.add(exit_button)
        outer_box.add(button_box)

        # Spacer between text and buttons
        outer_box.add(arcade.gui.UISpace(height=20))

        # Highscores
        if highscores:
            outer_box.add(
                arcade.gui.UILabel(
                    text="High Scores:",
                    font_size=18,
                    bold=True,
                )
            )

            # Split into 2 columns
            left_col = arcade.gui.UIBoxLayout(
                vertical=True, space_between=4, align="left"
            )
            right_col = arcade.gui.UIBoxLayout(
                vertical=True, space_between=4, align="left"
            )

            for i, entry in enumerate(self.highscores):
                label = arcade.gui.UILabel(
                    text=f"{i + 1}. {entry.name} - {entry.score} pts",
                    font_size=14,
                )
                if i < 5:
                    left_col.add(label)
                else:
                    right_col.add(label)

            scores_row = arcade.gui.UIBoxLayout(
                vertical=False, space_between=40, align="top"
            )
            scores_row.add(left_col)
            scores_row.add(right_col)
            outer_box.add(scores_row)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
            anchor_x="center_x",
            anchor_y="center_y",
            child=outer_box,
        )

        @start_button.event("on_click")
        def on_click_start_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.game)

        @instructions_button.event("on_click")
        def on_click_instruction_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.instruction)

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
