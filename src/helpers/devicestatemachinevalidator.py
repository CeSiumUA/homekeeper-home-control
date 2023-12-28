import datetime
import logging
from logging import Logger
from helpers.dbaccess import DeviceType, MongoDbAccess


class DeviceStateBasicValidator:

    DEVICE_TYPE_VALIDATOR_MAPPING = {
        DeviceType.DESK_LIGHT: lambda device, logger: DeviceSwitchDarkValidator(device, logger),
        DeviceType.FLOOR_HEATING: lambda device, logger: DeviceSwitchColdValidator(device, logger)
    }

    def __init__(self, device, logger: logging.Logger | None = None) -> None:
        self.device_name = device[MongoDbAccess.DEVICE_NAME_FIELD]
        self.power_on = device[MongoDbAccess.DEVICE_POWER_ON_FIELD]
        self.paired_devices = device[MongoDbAccess.DEVICE_PAIRED_DEVICES_FIELD]

        if MongoDbAccess.DEVICE_SWITCH_INTERVAL_FIELD not in device:
            self.switch_interval = 300
        else:
            self.switch_interval = device[MongoDbAccess.DEVICE_SWITCH_INTERVAL_FIELD]

        if MongoDbAccess.DEVICE_LAST_SWITCH_FIELD not in device:
            self.last_switch = datetime.datetime.min
        else:
            self.last_switch = device[MongoDbAccess.DEVICE_LAST_SWITCH_FIELD]

        if MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD not in device:
            self.is_power_forced = False
        else:
            self.is_power_forced = device[MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD]

        self.is_device_sleep = device[MongoDbAccess.DEVICE_IS_DEVICE_SLEEP]
        self.device_type = device[MongoDbAccess.DEVICE_TYPE_FIELD]
        self._logger = logging if logger is None else logger

    def is_toggle_allowed(self, new_state: bool, forced: bool = False) -> bool:
        self._logger.info(f'old state: {self.power_on}, new state: {new_state}, forced: {forced}, old forced: {self.is_power_forced}')
        if (self.is_power_forced and forced) or ((not self.is_power_forced) and (not forced)):
            return new_state != self.power_on
        elif forced:
            self.is_power_forced = True
            return self.is_power_forced
        else:
            return False
    
    def get_device_validator(device, logger: logging.Logger | None = None):
        device_type = DeviceType(device[MongoDbAccess.DEVICE_TYPE_FIELD])
        validator = DeviceStateBasicValidator.DEVICE_TYPE_VALIDATOR_MAPPING[device_type](device, logger)
        return validator
    

class DeviceSwitchTimeValidator(DeviceStateBasicValidator):
    def is_toggle_allowed(self, new_state: bool, forced: bool = False) -> bool:
        current_time = datetime.datetime.now()

        self._logger.info(f'last switch time: {self.last_switch}')

        if self.last_switch + datetime.timedelta(seconds=self.switch_interval) > current_time:
            self._logger.info(f"too small interval for {self.device_name}, device interval is: {self.switch_interval}")
            return False
        
        return super().is_toggle_allowed(new_state, forced=forced)
    
class DeviceSwitchSleepValidator(DeviceSwitchTimeValidator):
    def is_toggle_allowed(self, new_state: bool, forced: bool = False) -> bool:
        if self.is_device_sleep:
            new_state = False
        self._logger.info(f'device sleep: {self.is_device_sleep}')
        return super().is_toggle_allowed(new_state=new_state, forced=forced)
    
class DeviceSwitchColdValidator(DeviceSwitchSleepValidator):

    DEVICE_COLD_THRESHOLD = 25
    DEVICE_OVERHEATING_THRESHOLD = 38

    def __init__(self, device, logger: Logger | None = None) -> None:
        self.temperature = device[MongoDbAccess.DEVICE_TEMPERATURE_FIELD]
        super().__init__(device, logger)

    def is_toggle_allowed(self, new_state: bool | None = None, forced: bool = False) -> bool:
        self._logger.info(f'device temperature: {self.temperature}')
        if self.temperature < self.DEVICE_COLD_THRESHOLD:
            toggle = True
        elif self.temperature > self.DEVICE_COLD_THRESHOLD and self.temperature < self.DEVICE_OVERHEATING_THRESHOLD:
            toggle = self.power_on
        else:
            toggle = False
        return super().is_toggle_allowed(new_state=toggle, forced=forced)
    
class DeviceSwitchDarkValidator(DeviceSwitchSleepValidator):

    def __init__(self, device, logger: Logger | None = None) -> None:
        self.is_dark = device[MongoDbAccess.DEVICE_IS_DARK_FIELD]
        super().__init__(device, logger)

    def is_toggle_allowed(self, new_state: bool | None = None, forced: bool = False) -> bool:
        self._logger.info(f'device dark: {self.is_dark}')
        return super().is_toggle_allowed(self.is_dark, forced=forced)