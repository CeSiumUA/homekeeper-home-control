import logging
from helpers.mongologger import MongoLogger
from helpers.env import Env
from helpers.interfaces import DependencyContainer
from modules.tlbot import TlBot
from modules.scheduler import HomeKeeperScheduler
from modules.netwatcher import HomeKeeperNetwatcher
from modules.mqttmanager import HomeKeeperMQTT
from modules.devicesmanager import DevicesManager

def main():
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    if Env.load_required_values():
        logging.info("environment variables presence verified")
    else:
        logging.fatal('missing required environment variables')
        return

    # TODO subscribe to devices
    # TODO register all jobs

    di_container = DependencyContainer()

    tl_bot_logger = logging.getLogger('homekeeper_tl_bot')
    scheduler_logger = logging.getLogger('homekeeper_scheduler')
    netwatcher_logger = logging.getLogger('homekeeper_netwatcher')
    mqtt_manager_logger = logging.getLogger('homekeeper_mqtt_manager')
    device_manager_logger = logging.getLogger('homekeeper_device_manager')

    mongo_handler = MongoLogger()

    loggers = [tl_bot_logger, scheduler_logger, netwatcher_logger, mqtt_manager_logger, device_manager_logger]
    for logger in loggers:
        logger.setLevel(logging.INFO)
        logger.addHandler(mongo_handler)

    tl_bot = TlBot(di_container, di_container, tl_bot_logger)
    scheduler = HomeKeeperScheduler(di_container, di_container, di_container, scheduler_logger)
    netwatcher = HomeKeeperNetwatcher(di_container, netwatcher_logger)
    mqtt_manager = HomeKeeperMQTT(di_container, di_container, mqtt_manager_logger)
    device_manager = DevicesManager(di_container, device_manager_logger)

    di_container.register_dependencies(device_manager, mqtt_manager, netwatcher, tl_bot)

    with mqtt_manager:
        mqtt_manager.subscribe_to_topics()
        with scheduler:
            scheduler.register_all_jobs()

            tl_bot.start_bot()

if __name__ == '__main__':
    main()