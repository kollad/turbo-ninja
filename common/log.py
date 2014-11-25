from yaml import load
from logging import config
import os


def setup_logger(settings):
    """
    Settings object

    :param settings: Settings
    :type settings: dict
    :return:
    """
    with open(os.path.join("logging.yaml")) as logging_config:
        log_config = load(logging_config)

    configure_logs(settings, log_config)


def configure_logs(settings, cfg):
    """
    Configure logs

    :param settings: Settings
    :type settings: dict
    :param cfg: Logging config
    :type cfg: dict
    :return:
    """
    cfg = cfg.copy()
    log_path = os.path.join(settings['log_path'])
    if not os.path.isdir(log_path):
        os.mkdir(log_path)
    try:
        handlers = cfg['handlers']
    except KeyError:
        pass
    else:
        for handler in handlers.values():
            try:
                filename = handler['filename']
            except KeyError:
                pass
            else:
                handler['filename'] = os.path.join(log_path, filename)
    config.dictConfig(cfg)




