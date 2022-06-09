from src.android import AndroidDevice
from hashlib import sha256
import time
import requests


class BarterClient:
    BASE_URL = 'https://barter.myflutterwave.com/api/v1/barter/'
    USER_ID = '0300A873A5BB85D5375864CFFD9BACA1BE8E72D6ADC227E336436ED863A3AE4E'
    SALT = '0300A873A5BB85D5375864CFFD9BACA1BE8E72D6ADC227E336436ED863A3AE4E395DBB31AB4CE3358B32471F8DA7664BF5ED58817ECB8125912D5017C9AD30B6'

    def __init__(self, device: 'AndroidDevice', email: str, passwd: str, phone: str,
                 first_name: str, last_name: str, country: str = "GB", proxies: dict = None) -> None:
        self.device = device
        self.email = email
        self.passwd = passwd
        self.phone = phone
        self.first_name = first_name
        self.last_name = last_name
        self.country = country
        self.proxies = proxies
        self.access_token = None
        self.refresh_token = None

    def _http_headers(self) -> dict:
        customerreference = 'ML_ANDROID_deviceId{}'.format(int(time.time()))
        for_hash = bytes(customerreference + self.SALT, 'UTF-8')
        headers = {
            'user-agent': 'okhttp/4.7.2',
            'customerreference': customerreference,
            'userid': self.USER_ID,
            'hash': sha256(for_hash).digest().hex().upper()
        }
        if self.access_token is not None:
            headers['authorization'] = 'Bearer {}'.format(self.access_token)
        return headers

    def _url(self, path: str):
        return self.BASE_URL + path

    def _http_get(self, url: str):
        resp = requests.get(url, headers=self._http_headers(), proxies=self.proxies, verify=False)
        return resp.json()

    def _http_post(self, url: str, data: dict = None):
        resp = requests.post(url, headers=self._http_headers(), json=data, proxies=self.proxies, verify=False)
        return resp.json()

    def check_ip(self):
        return requests.get("https://api64.ipify.org?format=json", proxies=self.proxies).json()

    def sign_up_or_login(self):
        res = self.sign_up()
        if res.get("Status", "fail") == "fail":
            res = self.login()
        return res

    # API call
    def sign_up(self):
        device = self.device
        body = {
            "Country": self.country,
            "DeviceInfo": {
                "DeviceId": device.device_id,
                "DeviceName": device.device_name,
                "DeviceToken": device.device_token,
                "Os": "android",
                "OsVersion": device.os_version,
                "SerialNumber": device.serial_number
            },
            "EmailAddress": self.email,
            "FirstName": self.first_name,
            "IsSocial": False,
            "LastName": self.last_name,
            "MobileNumber": self.phone,
            "Password": self.passwd
        }
        return self._http_post(self._url('signup'), body)

    def login(self):
        body = {
            "Device": self.device.to_json(),
            "Identifier": self.email,
            "IsSocial": False,
            "Password": self.passwd
        }
        res = self._http_post(self._url('login'), body)
        if res['Status'] == 'success':
            self.access_token = res['Token']['access_token']
            self.refresh_token = res['Token']['refresh_token']
        return res

    def confirm_mobile_number(self, otp: str):
        body = {
            "MobileNumber": self.phone,
            "Otp": otp
        }
        return self._http_post(self._url("signupV2/confirm-mobile-number"), body)

    def confirm_account(self):
        body = {
            "Firstname": self.first_name,
            "Lastname": self.last_name,
            "MobileNumber": self.phone,
            "Password": self.passwd
        }
        res = self._http_post(self._url("signupV2/confirm-account"), body)
        if res['Status'] == 'success':
            self.access_token = res['Token']['access_token']
            self.refresh_token = res['Token']['refresh_token']
        return res

    def init_verify(self):
        body = {
            "provider": "VERIFF"
        }
        return self._http_post(self._url("verify/initiate"), body)
