from logging import getLogger

from engine.social import connect_social_interface

import app # an entry point to game logic



__author__ = 'kollad'

log = getLogger('process')


def setup_game_server(application_settings, tornado_port):
    """
    Setup environment. Prepare user manager, init database locks, content manager, social interface, static files etc.

    :param application_settings: Application settings
    :type application_settings: dict
    :param tornado_port: Game server tornado port
    :type tornado_port: int
    :return:
    """

    log.info('game.%s : Preparing game server for the app "%s"',
                                        tornado_port, app.name)

    command_processor_maker = app.get_command_processor_maker(application_settings)

    user_manager = app.get_user_manager(application_settings)

    log.info('game.%s : Player Manager initialized', tornado_port)

    log.info('game.%s : Preparing content manager for game data. Building cache...',
                                                                tornado_port)

    content_manager = app.get_content_manager(application_settings)

    log.info('game.%s : Content manager cache built successfully', tornado_port)

    social_interface = connect_social_interface(application_settings)

    log.info('game.%s : Social Interface connected successfully', tornado_port)

    return {
        'command_processor_maker': command_processor_maker,
        'user_manager': user_manager,
        'content_manager': content_manager,
        'social': social_interface,
    }
