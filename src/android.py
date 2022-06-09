

class AndroidDevice:
    def __init__(self, device_id: str, device_name: str,
                 device_token: str, os_version: int, serial_number: str) -> None:
        self.device_id = device_id
        self.device_name = device_name
        self.device_token = device_token
        self.os = 'android'
        self.os_version = os_version
        self.serial_number = serial_number

    def to_json(self):
        return {
            "DeviceId": self.device_id,
            "DeviceName": self.device_name,
            "DeviceToken": self.device_token,
            "Os": "android",
            "OsVersion": str(self.os_version),
            "SerialNumber": self.serial_number
        }
