from engine.utils.timeutils import milliseconds
from engine.utils.mathutils import Median


class PerformanceInfo(object):
    __slots__ = ('_process_id', 'time', 'requests', 'fetch_time', 'run_commands_time', 'game_server_id')

    def __init__(self, game_server_id):
        self.time = milliseconds()
        self.requests = 0
        self.fetch_time = Median()
        self.run_commands_time = Median()
        self.game_server_id = game_server_id

    def reset(self):
        self.time = milliseconds()
        self.requests = 0
        self.fetch_time.clear()
        self.run_commands_time.clear()

    def dump(self):
        return dict((s, getattr(self, s)) for s in self.__slots__)

    def get(self):
        if not self.requests:
            return 'Performance info: Empty'

        period = float(milliseconds() - self.time) * .001
        rps = self.requests / period
        return ('Performance info: {game_server_id}\n'
                'Period: {period:.2f}s, Requests: {requests}, Fetch count: {fetch_count}, '
                'Run directive count: {run_directive_count}\n'
                'Requests per second:          {rps:.2f}\n'
                'Fetch time (ms):              {fetch_time}\n'
                'Run commands time (ms):       {run_commands_time}\n'
                '------------------------------------------------------------------------').format(
            game_server_id=self.game_server_id,
            rps=rps, period=period, fetch_count=self.fetch_time.len, **self.dump())