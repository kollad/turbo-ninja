from engine.commands import BaseCommand, CommandProcessor
from engine.user.user_stash import Stash


class GameCommand(BaseCommand):
    registry = {}
    disabled = True

    def run(self):
        pass

    def put_in_stash(self, stash):
        if not isinstance(stash, Stash):
            stash = self.user_state.make_stash(stash)
        self.user_state.stash += stash


class GameCommandProcessor(CommandProcessor):
    command_class = GameCommand