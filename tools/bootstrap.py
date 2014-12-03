from distutils.dir_util import copy_tree, remove_tree
import os


def _copy_function(source, destination):
    print('Bootstrapping project at %s' % destination)
    copy_tree(source, destination)


def create_app():
    cwd = os.getcwd()
    game_logic_path = os.path.join(cwd, 'game_logic')
    game_app_interface = os.path.join(cwd, 'game_app.py')
    app_template = os.path.join(cwd, 'engine', 'app_template')
    _game_logic_path_exists = os.path.exists(game_logic_path)
    _game_app_interface_exists = os.path.exists(game_app_interface)
    if _game_logic_path_exists or _game_app_interface_exists:
        answer = input(
            'game_app.py or game_logic module already exists. Continue? (y/n). ' +
            '\nWARNING: This will remove all contents of game_logic module, use at your own risk:'.upper()
        )
        if answer == 'y':
            if _game_app_interface_exists:
                remove_tree(game_app_interface)
            if _game_logic_path_exists:
                remove_tree(game_logic_path)
            _copy_function(app_template, cwd)
    else:
        _copy_function(app_template, cwd)


if __name__ == '__main__':
    create_app()
