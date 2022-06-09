import json
import logging
import os
import time
import uuid

from moviepy.video.io.VideoFileClip import VideoFileClip

from src import config
from src.android import AndroidDevice
from src.barter import BarterClient
from src.veriff import VeriffClient


class VerifyBarter:

    DEVICE_NAME = "Sony G8142"
    OS_VERSION = 28
    NOT_REQUIRED_FILE = {
        "document-front-pre": "document-front",
        "document-back-pre": "document-back",
        "face-pre": "face"
    }

    def __init__(self, folder: str):
        self.logger_ = logging.getLogger('bt')
        self.device_ = AndroidDevice(str(uuid.uuid4()), self.DEVICE_NAME, '', self.OS_VERSION, str(uuid.uuid4()))
        self.client_ = None
        self.info_ = {}
        self.folder_ = folder

    def check_info(self):
        if not os.path.exists(self.folder_):
            self.logger_.debug(f"{self.logger_} not exists")
            return False
        images = {}
        videos = {}
        for file in os.listdir(self.folder_):
            file_path = os.path.join(self.folder_, file)
            if os.path.getsize(file_path) > 12 * 1000 * 1000:
                self.logger_.debug(f"File {file_path} size does not exceed 12 MB")
                return False
            if file.endswith(".json"):
                with open(file_path, "r") as f:
                    self.info_ = json.load(f)
            items = os.path.splitext(file)
            name_file = items[0]
            if items[-1] == ".mp4":
                videos[name_file] = file_path
            else:
                images[name_file] = file_path
        for k, v in self.NOT_REQUIRED_FILE.items():
            if k not in images:
                if v not in images:
                    self.logger_.debug(f"{v} not exists")
                    return False
            images[k] = images[v]
        documents = {
            "images": images,
            "videos": videos
        }
        self.info_["documents"] = documents
        self.logger_.debug(self.info_)
        return True

    def verify(self):
        status = self.check_info()
        self.logger_.debug(self.info_)
        if not status:
            return False
        proxy = self.info_.get("proxy")
        proxies = None
        if proxy:
            url = f"{proxy['mode']}://{proxy['user']}:{proxy['passwd']}@{proxy['host']}:{proxy['port']}"
            proxies = {
                "http": url,
                "https": url
            }
        self.client_ = BarterClient(self.device_, self.info_['email'], self.info_['passwd'], self.info_['phone'],
                              self.info_['first_name'], self.info_['last_name'],
                              self.info_.get("country", "GB"), proxies=proxies)
        res = self.client_.check_ip()
        self.logger_.debug(res)
        res = self.client_.sign_up()
        self.logger_.debug(res)
        if res.get("Status", "fail") == "fail":
            self.logger_.debug(f"Sign up fail with => {res.get('Message')}")
            return False
        otp = str(input('OTP: '))
        res = self.client_.confirm_mobile_number(otp)
        self.logger_.debug(res)
        res = self.client_.confirm_account()
        self.logger_.debug(res)
        # Verify account
        res = self.client_.init_verify()
        self.logger_.debug(res)
        redirect_url = res["Data"]["RedirectUrl"]
        token = redirect_url.replace(config.ALCHEMY_URL, "")
        veriff_client = VeriffClient(token)
        res = veriff_client.session()
        self.logger_.debug(res)
        session_id = res["activeVerificationSession"]["id"]
        veriff_client.actions(["client_started", "device_info_received"])
        veriff_client.config()
        veriff_client.actions(["language_assigned"])
        veriff_client.utils("deviceid-token")
        veriff_client.actions(["language_assigned"])
        veriff_client.utils("supported-countries?lang=gb")
        veriff_client.waiting_rooms()
        veriff_client.session()
        veriff_client.actions(["intro_screen_shown"])
        veriff_client.config()
        veriff_client.actions(["intro_screen_shown"])
        actions = [
            {"event_type": "message", "feature": "microphone_permission_triggered"},
            {"event_type": "message", "feature": "camera_permission_triggered"},
            "intro_screen_start_button_clicked",
            {"event_type": "message", "feature": "camera_permission_granted"},
            {"event_type": "message", "feature": "microphone_permission_declined"},
            "hardware_test_successful"
        ]
        veriff_client.actions(actions)
        veriff_client.utils("supported-countries?lang=gb")
        actions = [
            "device_info_received", "country_select_screen_shown",
            {"event_type": "message", "feature": "country-select-dropdown"},
            "country_select_dropdown_item_chosen",
            {"event_type": "message", "feature": "country-select-chosen"},
            {"event_type": "message", "feature": "country-select-dropdown"},
            "country_select_dropdown_item_chosen",
            {"event_type": "message", "feature": "country-select-chosen"},
            "country_selected",
            {"event_type": "message", "feature": "country-select-continue"},
            "document_select_screen_shown", "document_from_list_chosen", "doc-select"
        ]
        veriff_client.actions(actions)
        veriff_client.verifications(f"{session_id}/documents", {
            "country": self.client_.country.upper(),
            "type": "DRIVERS_LICENSE"
        })
        veriff_client.actions(["document_selected"])
        veriff_client.status(session_id)
        actions = [
            "nfc_step_enabled", "tos_accepted", "session-started", "camera-started", "document_front_screen_shown",
            "video-started", "video_first_frame_received", "document_front_screen_take_picture_clicked",
            {"event_type": "capture_approved",
             "params": {"additional_data": {"message": "Capture: document-front-pre"}}},
            {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: document-front"}}},
            "document-front_approved", "document_back_screen_shown"
        ]
        veriff_client.actions(actions)
        # Upload document front pre
        documents = self.info_["documents"]
        res = veriff_client.upload(session_id, "images",
                                   documents["images"]["document-front-pre"],
                                   "document-front-pre", inflow_feedback=True)
        self.logger_.debug(res)
        time.sleep(20)
        video_front_path = documents["videos"]["document-front-pre-video"]
        video_front = VideoFileClip(video_front_path)
        video_front_length = os.path.getsize(video_front_path)
        actions = [
            "video-started",
            {"event_type": "video_file_saved", "params": {"additional_data": {"duration": video_front.duration * 1000,
                                                                              "file_length": video_front_length}}},
            "video_first_frame_received", "document_back_screen_take_picture_clicked",
            {"event_type": "capture_approved",
             "params": {"additional_data": {"message": "Capture: document-back-pre"}}},
            {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: document-back"}}},
            "document-back_approved", "portrait_auto_capture_enabled", "portrait_screen_shown"
        ]
        veriff_client.actions(actions)
        # Upload document back pre
        res = veriff_client.upload(session_id, "images", documents["images"]["document-back-pre"],
                                   "document-back-pre", inflow_feedback=True)
        self.logger_.debug(res)
        video_back_path = documents["videos"]["document-back-pre-video"]
        video_back = VideoFileClip(video_back_path)
        video_back_length = os.path.getsize(video_back_path)
        actions = [
            "video-started",
            {"event_type": "video_file_saved", "params": {"duration": video_back.duration * 1000,
                                                          "file_length": video_back_length}},
            "video_first_frame_received",
            "portrait_screen_take_picture_clicked",
            {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: face-pre"}}},
            {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: face"}}},
            "face_approved",
        ]
        veriff_client.actions(actions)
        # Upload face-pre
        res = veriff_client.upload(session_id, "images", documents["images"]["face-pre"],
                                   "face-pre", inflow_feedback=True)
        self.logger_.debug(res)
        video_face_path = documents["videos"]["face-pre-video"]
        face = VideoFileClip(video_face_path)
        face_length = os.path.getsize(video_face_path)
        actions = [
            {"event_type": "video_file_saved",
             "params": {"duration": face.duration * 1000, "file_length": face_length}},
            {"event_type": "message", "feature": "upload_view_started"},
            "uploading", "waiting_decision_screen_shown", "upload_screen_shown"
        ]
        veriff_client.actions(actions)
        res = veriff_client.upload(session_id, "images", documents["images"]["document-front"], "document-front")
        self.logger_.debug(res)
        res = veriff_client.upload(session_id, "videos", documents["videos"]["document-front-pre-video"],
                                   "document-front-pre-video", sleep=[2, 5])
        self.logger_.debug(res)
        res = veriff_client.upload(session_id, "images", documents["images"]["document-back"], "document-back")
        self.logger_.debug(res)
        res = veriff_client.upload(session_id, "videos", documents["videos"]["document-back-pre-video"],
                                   "document-back-pre-video", sleep=[2, 5])
        self.logger_.debug(res)
        res = veriff_client.upload(session_id, "images", documents["images"]["face"], "face")
        self.logger_.debug(res)
        res = veriff_client.upload(session_id, "videos", documents["videos"]["face-pre-video"], "face-pre-video",
                                   sleep=[2, 5])
        self.logger_.debug(res)
        actions = [
            {"event_type": "message", "feature": "upload_session_update"}
        ]
        veriff_client.actions(actions)
        # Submitted
        veriff_client.status(session_id, "submitted")
        actions = [
            "upload_success", "session-submitted"
        ]
        veriff_client.actions(actions)
        res = veriff_client.session()
        self.logger_.debug(res)
        res = veriff_client.session()
        self.logger_.debug(res)
        res = veriff_client.session()
        self.logger_.debug(res)
        actions = [
            "decision_received", "success"
        ]
        veriff_client.actions(actions)
        self.logger_.debug("Send message verify barter successfully")
        return True
