import arcade
import arcade.gui

from pacman.highscore import HighscoreEntry
from pacman.window import WINDOW_WIDTH, WINDOW_HEIGHT, GameView


class InstructionView(arcade.View):
    def __init__(self, game: GameView) -> None:
        super().__init__()
        self.game = game

        self.manager = arcade.gui.UIManager()

        # Buttons
        start = arcade.gui.UIFlatButton(text="Start Game", width=150)
        back = arcade.gui.UIFlatButton(text="Back", width=150)
        exit = arcade.gui.UIFlatButton(text="Exit", width=150)

        # Initialise a grid in which widgets can be arranged.
        self.grid = arcade.gui.UIGridLayout(
            column_count=3, row_count=1, horizontal_spacing=20, vertical_spacing=20
        )

        # Adding the buttons to the layout.
        self.grid.add(start, column=0, row=0)
        self.grid.add(back, column=1, row=0)
        self.grid.add(exit, column=2, row=0)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
            anchor_x="center_x",
            anchor_y="center_y",
            child=self.grid,
        )

        @start.event("on_click")
        def on_click_start_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.game)

        # @back.event("on_click")
        # def on_click_instruction_button(event) -> None:
        #     self.window.show_view(self.instruction)

        @exit.event("on_click")
        def on_click_exit_button(event: arcade.gui.UIOnClickEvent) -> None:
            arcade.exit()

    def on_show_view(self) -> None:
        self.window.background_color = arcade.color.ORANGE_PEEL
        self.manager.enable()

    def on_hide_view(self) -> None:
        self.manager.disable()

    def on_draw(self) -> None:
        self.clear()
        self.manager.draw()
        arcade.draw_text("Instructions", WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 150,
                         arcade.color.BLACK, font_size=50, anchor_x="center")


class MainMenu(arcade.View):
    """
    The main menu allows the player to:
    - start a new game
    - view highscores
    - view instructions
    - exit
    """
    def __init__(self, instruction: InstructionView,
                 game: GameView, highscores: list[HighscoreEntry]) -> None:
        super().__init__()
        self.manager = arcade.gui.UIManager()

        self.instruction = instruction
        self.game = game
        self.highscores = highscores

        # Buttons
        start = arcade.gui.UIFlatButton(text="Start", width=150)
        instructions = arcade.gui.UIFlatButton(text="Instructions", width=150)
        exit = arcade.gui.UIFlatButton(text="Exit", width=150)

        # Initialise a grid in which widgets can be arranged.
        self.grid = arcade.gui.UIGridLayout(
            column_count=1, row_count=3, horizontal_spacing=20, vertical_spacing=20
        )

        # Adding the buttons to the layout.
        self.grid.add(start, column=0, row=0)
        self.grid.add(instructions, column=0, row=1)
        self.grid.add(exit, column=0, row=2)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())

        self.anchor.add(
            anchor_x="center_x",
            anchor_y="center_y",
            child=self.grid,
        )

        @start.event("on_click")
        def on_click_start_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.game)

        @instructions.event("on_click")
        def on_click_instruction_button(event: arcade.gui.UIOnClickEvent) -> None:
            self.window.show_view(self.instruction)

        @exit.event("on_click")
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
        arcade.draw_text("Pac-Man", WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2 + 150,
                         arcade.color.YELLOW, 40, anchor_x="center")
