import hashlib
import json


class Event(object):
    """Generic event."""

    def __init__(self, user_id, session_id, build):
        """Initialize object.

        :param user_id: unique id representing the user playing game
        :type user_id: str or unicode
        :param session_id: unique id representing the current play session
        :type session_id: str or unicode
        :param build: current version of the game
        :type build: str or unicode
        """
        self.user_id = user_id
        self.session_id = session_id
        self.build = build

    def __repr__(self):
        """Return string representation of the object."""
        representation = "{}: {}".format(self.__class__.__name__, self.__dict__)
        return representation

    def encode(self, secret_key):
        """Return dict with prepared data for Game Analytics.

        :param secret_key: application secret key
        :type secret_key: string or unicode
        """
        message = json.dumps(self.__dict__)
        digest = hashlib.md5()
        digest.update(message)
        digest.update(secret_key)
        auth_header = {'Authorization': digest.hexdigest()}
        encoded = {
            'message': message,
            'auth_header': auth_header,
            'category': self.__class__.category
        }
        return encoded


class GameEvent(Event):
    """Generic game event."""
    category = 'design'

    def __init__(self, user_id, session_id, build, area=None):
        """Initialize object.

        :param user_id: unique id representing the user playing game
        :type user_id: str or unicode
        :param session_id: unique id representing the current play session
        :type session_id: str or unicode
        :param build: current version of the game
        :type build: str or unicode
        :param area: area or game level where the event occured
        :type area: str or unicode
        """
        super(GameEvent, self).__init__(user_id, session_id, build)
        if area:
            self.area = area


class GameDesignEvent(GameEvent):
    """Game design event."""

    def __init__(self, user_id, session_id, build, event_id, value=None, area=None):
        """Initialize object.

        :param user_id: unique id representing the user playing game
        :type user_id: str or unicode
        :param session_id: unique id representing the current play session
        :type session_id: str or unicode
        :param build: current version of the game
        :type build: str or unicode
        :param event_id: event identifier, can be sub-categorized by using ":" notation
        :type event_id: str or unicode
        :param value: numeric value which may be used to enhance the event_id
        :type value: float
        :param area: area or game level where the event occured
        :type area: str or unicode
        """
        super(GameDesignEvent, self).__init__(user_id, session_id, build, area)
        self.event_id = event_id
        if value:
            self.value = value


class GameErrorEvent(GameEvent):
    """Game error event."""
    category = 'error'

    def __init__(self, user_id, session_id, build, message, severity, area=None):
        """Initialize object.

        :param user_id: unique id representing the user playing game
        :type user_id: str or unicode
        :param session_id: unique id representing the current play session
        :type session_id: str or unicode
        :param build: current version of the game
        :type build: str or unicode
        :param area: area or game level where the event occured
        :type area: str or unicode
        :param message: describe the event in further detail
        :type message: str or unicode
        :param severity: describe the severity of the event, must be one of the following values: "critical",
                         "error", "warning", "info", "debug"
        :type severity: str or unicode
        :param area: area or game level where the event occured
        :type area: str or unicode
        """
        super(GameErrorEvent, self).__init__(user_id, session_id, build, area)
        self.message = message
        self.severity = severity


class GameBusinessEvent(GameEvent):
    """In-game purchases event."""
    category = 'business'

    def __init__(self, user_id, session_id, build, event_id, currency, amount, area=None):
        """Initialize object.
        :param user_id: unique id representing the user playing game
        :type user_id: str or unicode
        :param session_id: unique id representing the current play session
        :type session_id: str or unicode
        :param build: current version of the game
        :type build: str or unicode
        :param event_id: event identifier, can be sub-categorized by using ":" notation
        :type event_id: str or unicode
        :param currency: custom string for identifying the currency
        :type currency: str or unicode
        :param amount: numeric value which corresponds to the cost of purchase in the monetary unit multiplied by 100
        :type amount: int
        :param area: area or game level where the event occured
        :type area: str or unicode
        """
        super(GameBusinessEvent, self).__init__(user_id, session_id, build, area)
        self.event_id = event_id
        self.currency = currency
        self.amount = amount


class UserEvent(Event):
    """Event that contains information about individual users."""
    category = 'user'

    def __init__(self, user_id, session_id, build, platform, gender=None, birth_year=None, friend_count=None,
                 facebook_id=None, install_publisher=None, install_site=None, install_campaign=None,
                 install_adgroup=None, install_ad=None):
        """Initialize object.

        :param user_id: unique id representing the user playing game
        :type user_id: str or unicode
        :param session_id: unique id representing the current play session
        :type session_id: str or unicode
        :param build: current version of the game
        :type build: str or unicode
        :param platform: platform that this user plays the game on
        :type platform: str or unicode
        :param gender: gender of the user: M or F
        :type gender: str or unicode
        :param birth_year: year the user was born
        :type birth_year: integer
        :param friend_count: number of friends in the user network
        :type friend_count: int
        :param facebook_id: facebook id of the user
        :type facebook_id: str or unicode
        :param install_publisher: name of the ad publisher
        :type install_publisher: str or unicode
        :param install_site: website or app where the ad for your game was shown
        :type install_site: str or unicode
        :param install_campaign: name of your ad campaign this user comes from
        :type install_campaign: str or unicode
        :param install_adgroup: name of the ad group this user comes from
        :type install_adgroup: str or unicode
        :param install_ad: name of the ad this user comes from
        :type install_ad: str or unicode
        """
        super(UserEvent, self).__init__(user_id, session_id, build)
        self.platform = platform
        if gender:
            self.gender = gender
        if birth_year:
            self.birth_year = birth_year
        if friend_count:
            self.friend_count = friend_count
        if facebook_id:
            self.facebook_id = facebook_id
        if install_publisher:
            self.install_publisher = install_publisher
        if install_site:
            self.install_site = install_site
        if install_campaign:
            self.install_campaign = install_campaign
        if install_adgroup:
            self.install_adgroup = install_adgroup
        if install_ad:
            self.install_ad = install_ad

