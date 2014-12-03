from engine.common.data import DataObjectAbstract


class GameData(DataObjectAbstract):
    """
    This is game data object
    """

    def __init__(self, settings):
        self._data = 'Store game data into this variable'

    @property
    def data(self):
        return self._data

    def reload_cache(self, key):
        pass

    def drop_cache(self):
        pass


class StaticData(DataObjectAbstract):
    """
    This is static data object
    """

    def __init__(self, settings):
        self._data = 'Store static data into this variable'

    @property
    def data(self):
        return self._data

    def reload_cache(self, key):
        pass

    def drop_cache(self):
        pass


class ContentManager(object):
    """
    This is main content manager object, that application would use
    """

    def __init__(self, settings):
        self.settings = settings
        self._game_data = GameData(settings)
        self._static_data = StaticData(settings)

    @property
    def game_data(self):
        return self._game_data.data

    @property
    def static_data(self):
        return self._static_data.data