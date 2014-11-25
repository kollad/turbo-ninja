from logging import getLogger
import os
import yaml

__author__ = 'kollad'

# TODO: maybe should be separate log
log = getLogger('process')


def load_settings(path, *additional_settings_paths):
    """
    Load settings and override it with additional settings if provided. This function will always try to find
    local_settings.yaml file in path, where settings.yaml is, and override main_settings.

    :param path: Main settings path. Usually should contain settings, that should not contain basic required
                                parameters.
    :type main_settings_patham additional_settings_paths: Additional settings paths. This one will override main settings
    :type additional_settings_paths: list or tuple or set
    :return: Parsed settings
    :rtype: dict
    :raises: OSError
    """

    _base_settings = yaml.load(open('settings.yaml'))

    if not path == 'settings.yaml':
        _settings = yaml.load(open(path))
        _base_settings.update(_settings)

    if os.path.exists('local_settings.yaml'):
        _local_settings = yaml.load(open('local_settings.yaml'))
        _base_settings.update(_local_settings)

    for settings_path in additional_settings_paths:
        try:
            _settings = yaml.load(open(settings_path))
        except FileNotFoundError as e:
            log.error('Settings loader error: {}'.format(e))
        else:
            _base_settings.update(_settings)

    return _base_settings
