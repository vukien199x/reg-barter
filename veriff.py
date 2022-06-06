import json
import random
import time
import uuid

import requests
import urllib3

import utils


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
        resp = requests.get(url, headers=self._http_headers(), proxies=self.proxies, verify=False)
        return resp.json()

    def _http_post(self, url: str, data: dict = None):
        resp = requests.post(url, headers=self._http_headers(), json=data, proxies=self.proxies, verify=False)
        return resp.json()

    def started(self, session_id: str):
        res = requests.patch(self._url(f"v2/verifications/{session_id}"),
                             json={"status": "started"},
                             proxies=self.proxies, verify=False)
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
        return requests.put(self._url("api/v2/waiting-rooms"), proxies=self.proxies, verify=False)

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
            print(self._url(f"v1/verifications/{self.token}/event"))
            return self._http_post(self._url(f"v1/verifications/{self.token}/event"), {"events": [content]})
        return None

    def upload(self, upload_type: str, path_file: str, document_type: str):
        headers = self._http_headers()
        url = self._url(f"api/v2/verifications/{self.token}/{upload_type}")
        boundary = str(uuid.uuid4())
        boundary = "ae0b5a22-4fa5-48a4-afee-863331340e0e"
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        if not path_file.endswith(".webp"):
            path_file = utils.convert_image_to_webp(path_file)
        f = open(path_file, "rb")
        file = f.read()
        hitems = [str.encode(f'--{boundary}'), b'Content-Disposition: form-data; name="payload"',
                  b'Content-Transfer-Encoding: binary',
                  b'Content-Type: application/octet-stream', str.encode(f'Content-Length: {len(file)}\n\n')]
        head = b"\n\n".join(hitems)
        document_front = '{"content":"' + document_type + '"}'
        fitems = [f'--{boundary}', 'Content-Disposition: form-data; name="metadata"',
                  'Content-Transfer-Encoding: binary', 'Content-Type: application/json; charset=UTF-8',
                  f'Content-Length: {len(document_front)}\n\n', document_front, f'--{boundary}',
                  'Content-Disposition: form-data; name="inflowFeedback"', 'Content-Transfer-Encoding: binary',
                  'Content-Type: application/json; charset=UTF-8', f'Content-Length: {len("true")}\n\n', 'true',
                  f'--{boundary}', 'Content-Disposition: form-data; name="mrz"', 'Content-Transfer-Encoding: binary',
                  'Content-Type: application/json; charset=UTF-8', f'Content-Length: {len("false")}\n\n', 'false',
                  f'--{boundary}--\n\n']
        footer = str.encode("\n\n".join(fitems))
        data = b'\n\n'.join([head, file, footer])
        urllib3.disable_warnings()
        resp = requests.post(url, headers=headers, data=data, proxies=self.proxies, verify=False)
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
