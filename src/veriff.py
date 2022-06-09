import datetime
import json
import random
import time
import uuid

import requests
import urllib3

from src import utils

from moviepy.editor import VideoFileClip


def convert_params_event(events: dict, params: dict = None):
    if not params:
        return events
    for k, v in params.items():
        if isinstance(v, dict):
            events[k] = convert_params_event(events.get(k, {}), v)
        else:
            events[k] = v
    return events


class VeriffClient:
    BASE_URL = "https://alchemy.veriff.com/"

    with open("data/events.json", "r") as f:
        events = json.load(f)

    def __init__(self, token: str, os_version: str = "28", version_code: int = "406009",
                 veriff_version: str = "4.6.0", proxies: dict = None):
        self.token = token
        self.veriff_version = veriff_version
        self.os_version = os_version
        self.version_code = version_code
        self.proxies = proxies

    def _http_headers(self) -> dict:
        headers = {
            "accept-language": "en",
            "Accept": "application/vnd.veriff.v1+json",
            "X-Veriff-VersionName": self.veriff_version,
            "X-Veriff-VersionCode": self.version_code,
            "X-Veriff-OS-Version": self.os_version,
            "X-Veriff-Platform-Version": "2.4.44",
            "X-Veriff-Platform": "android",
            "X-ORIGIN": "mobile",
            "Authorization": f"Bearer {self.token}",
            "Host": "alchemy.veriff.com",
            "User-Agent": "okhttp/4.7.2"
        }
        return headers

    def _url(self, path: str):
        return self.BASE_URL + path

    def _http_get(self, url: str):
        resp = requests.get(url, headers=self._http_headers(), proxies=self.proxies)
        return resp.json()

    def _http_post(self, url: str, data: dict = None):
        resp = requests.post(url, headers=self._http_headers(), json=data, proxies=self.proxies)
        return resp.json()

    def status(self, session_id: str, status: str = "started"):
        res = requests.patch(self._url(f"v2/verifications/{session_id}"),
                             json={"status": status},
                             proxies=self.proxies)
        return res.json()

    def session(self):
        return self._http_get(self._url("api/v2/sessions"))

    def verifications(self, path: str, data: dict):
        return self._http_post(self._url(f"api/v1/{self.token}/{path}"), data)

    def utils(self, path: str):
        return self._http_get(self._url(f"api/v1/{self.token}/{path}"))

    def config(self):
        return self._http_get(self._url("api/v2/config"))

    def waiting_rooms(self):
        return requests.put(self._url("api/v2/waiting-rooms"), proxies=self.proxies)

    def event(self, event_type: str, feature: str = None, params: dict = None):
        print(event_type)
        if event_type not in self.events:
            return None
        content = self.events[event_type]
        if event_type == "message":
            if feature and feature in content:
                content = content[feature]
        content["timestamp"] = int(time.time())
        content = convert_params_event(content, params)
        print(content)
        if content:
            return self._http_post(self._url(f"v1/verifications/{self.token}/event"), {"events": [content]})
        return None

    def upload(self, session_id: str, upload_type: str, path_file: str, document_type: str, sleep: list = [1, 2]):
        print(f"Upload {document_type}")
        headers = self._http_headers()
        url = self._url(f"api/v2/verifications/{session_id}/{upload_type}")
        boundary = str(uuid.uuid4())
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        if upload_type == "images":
            if not path_file.endswith(".webp"):
                path_file = utils.convert_image_to_webp(path_file)
        f = open(path_file, "rb")
        file = f.read()
        hitems = [str.encode(f'--{boundary}'), b'Content-Disposition: form-data; name="payload"',
                  b'Content-Transfer-Encoding: binary',
                  b'Content-Type: application/octet-stream', str.encode(f'Content-Length: {len(file)}') + b'\x0d\x0a']
        head = b"\x0d\x0a".join(hitems)
        if upload_type == "images":
            context = '{"context":"' + document_type + '"}'
            fitems = [str.encode(f'--{boundary}'), b'Content-Disposition: form-data; name="metadata"',
                      b'Content-Transfer-Encoding: binary', b'Content-Type: application/json; charset=UTF-8',
                      str.encode(f'Content-Length: {len(context)}') + b'\x0d\x0a', str.encode(context),
                      str.encode(f'--{boundary}'),
                      b'Content-Disposition: form-data; name="inflowFeedback"', b'Content-Transfer-Encoding: binary',
                      b'Content-Type: application/json; charset=UTF-8',
                      str.encode(f'Content-Length: {len("true")}') + b'\x0d\x0a',
                      b"\x74\x72\x75\x65", str.encode(f'--{boundary}'), b'Content-Disposition: form-data; name="mrz"',
                      b'Content-Transfer-Encoding: binary',
                      b'Content-Type: application/json; charset=UTF-8',
                      str.encode(f'Content-Length: {len("false")}') + b'\x0d\x0a', b"\x66\x61\x6c\x73\x65",
                      str.encode(f'--{boundary}--') + b'\x0d\x0a']
        else:
            timestamp = datetime.datetime.utcnow().isoformat(timespec='milliseconds')
            duration = VideoFileClip(path_file).duration * 1000
            context = '{"timestamp":"' + timestamp + 'Z","duration":' + str(duration) + ',"context":"' + document_type + '"}'
            fitems = [str.encode(f'--{boundary}'), b'Content-Disposition: form-data; name="metadata"',
                      b'Content-Transfer-Encoding: binary', b'Content-Type: application/json; charset=UTF-8',
                      str.encode(f'Content-Length: {len(context)}') + b'\x0d\x0a', str.encode(context),
                      str.encode(f'--{boundary}')]
        footer = b"\x0d\x0a".join(fitems)
        data = b'\x0d\x0a'.join([head, file, footer])
        urllib3.disable_warnings()
        resp = requests.post(url, headers=headers, data=data)
        if sleep:
            time.sleep(random.randint(*sleep))
        return resp.json()

    def actions(self, actions: list):
        for action in actions:
            if isinstance(action, dict):
                res = self.event(**action)
            else:
                res = self.event(action)
            print(action)
            time.sleep(random.randint(1, 10) / 1000)
            print(res)
