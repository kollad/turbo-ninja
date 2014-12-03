from distutils.dir_util import copy_tree, remove_tree
import os
import shutil


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
                os.remove(game_app_interface)
            if _game_logic_path_exists:
                remove_tree(game_logic_path)
            _copy_function(app_template, cwd)
    else:
        _copy_function(app_template, cwd)

    if not os.path.exists('settings.yaml'):
        shutil.copy2('settings.yaml.template', 'settings.yaml')

    if not os.path.exists('logging.yaml'):
        shutil.copy2('logging.yaml.template', 'logging.yaml')


if __name__ == '__main__':
    create_app()
