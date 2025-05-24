from typing import Any, List


class SimulationRunner:
    """
    Orchestrates simulation steps using the Command Pattern.
    """

    def __init__(self, commands: List):
        self.commands = commands

    def run_turn(self, state: Any) -> None:
        for command in self.commands:
            command.execute(state)
