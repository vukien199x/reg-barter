import sys
import uuid

from android import AndroidDevice
from barter import BarterClient
from veriff import VeriffClient

if __name__ == '__main__':
    andr = AndroidDevice(str(uuid.uuid4()), 'Sony G8142', '', 28, str(uuid.uuid4()))
    proxies = {
        "http": "socks5://bpm-s5-45.57.236.20_1080:gK5Jz3aX0@173.208.239.130:22222",
        "https": "socks5://bpm-s5-45.57.236.20_1080:gK5Jz3aX0@173.208.239.130:22222"
    }
    client = BarterClient(andr, "dinkin1037@mailforspam.com", "Tuyen1997@",
                          "+447448964458", "Tuyen", "Vu", "GB", proxies=proxies)
    res = client.check_ip()
    print(res)
    res = client.sign_up()
    print(res)
    if res.get("Status", "fail") == "fail":
        print(res.get("Message"))
        sys.exit()
    otp = str(input('OTP: '))
    res = client.confirm_mobile_number(otp)
    print(res)
    res = client.confirm_account()
    print(res)
    # Verify account
    res = client.init_verify()
    print(res)
    redirect_url = res["Data"]["RedirectUrl"]
    token = redirect_url.replace("https://alchemy.veriff.com/v/", "")
    veriff_client = VeriffClient(token)
    res = veriff_client.session()
    print(res)
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
        "country": client.country.upper(),
        "type": "DRIVERS_LICENSE"
    })
    veriff_client.actions(["document_selected"])
    veriff_client.actions(["document_selected"])
    veriff_client.started(session_id)
    actions = [
        "nfc_step_enabled", "tos_accepted", "session-started", "camera-started", "document_front_screen_shown",
        "video-started", "video_first_frame_received", "document_front_screen_take_picture_clicked",
        {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: document-front-pre"}}},
        {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: document-front"}}},
        "document-front_approved", "document_back_screen_shown"
    ]
    veriff_client.actions(actions)
    # Upload document front pre
    res = veriff_client.upload("images", "data/blx-front.webp", "document-front-pre")
    print(res)
    actions = [
        "video-started",
        "video_file_saved",  # TODO edit source duration, file_length
        "video_first_frame_received", "document_back_screen_take_picture_clicked",
        {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: document-back-pre"}}},
        {"event_type": "capture_approved", "params": {"additional_data": {"message": "Capture: document-back"}}},
        "document-back_approved", "portrait_auto_capture_enabled", "portrait_screen_shown"
    ]
    # Upload document bakc pre
    res = veriff_client.upload("images", "data/blx-back.webp", "document-back-pre")
    print(res)
