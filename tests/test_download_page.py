from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
ANDROID = ROOT / "api" / "android.json"
WINDOWS = ROOT / "api" / "windows.json"
WINDOWS_LATEST = ROOT / "api" / "windows-latest.json"
WINDOWS_TEST = ROOT / "api" / "windows-brand-test.json"
LOGO = ROOT / "assets" / "brand" / "moadoom-icon-b.svg"
RELEASE_TAG = "v2.5.17-windows"
ANDROID_RELEASE_TAG = "android-phase15-sync-test"
WINDOWS_ASSET = "Insurance.AI_2.5.17_x64-setup.exe"
ANDROID_ASSET = "Moadoom_Android_1.0.0-phase15_debug.apk"
WINDOWS_URL = f"https://github.com/nasawon0-beep/insurance-ai/releases/download/{RELEASE_TAG}/{WINDOWS_ASSET}"
ANDROID_URL = f"https://github.com/nasawon0-beep/insurance-ai/releases/download/{ANDROID_RELEASE_TAG}/{ANDROID_ASSET}"
WINDOWS_SIGNATURE = "dW50cnVzdGVkIGNvbW1lbnQ6IHNpZ25hdHVyZSBmcm9tIHRhdXJpIHNlY3JldCBrZXkKUlVUa2tvZmJNSGFpbEpieXpPMnZHeVBrMnROWEFyczI5b29uMitpQ203SE1NOFRLcDRXeC9Wem9xOE8yK01mKzREY2dXV1VDNzZEa0Rqai9RWG5wSTVwV0lhZmN6WXRPemc0PQp0cnVzdGVkIGNvbW1lbnQ6IHRpbWVzdGFtcDoxNzk0MjcwMjEyCWZpbGU6SW5zdXJhbmNlIEFJXzIuNS4xN194NjQtc2V0dXAuZXhlClhxVlRaMXNoT2dxbVdUZHd0SmtzVjlHUmp5N1ZzTkVmOGFIWm9BRlZVSEVEZ0xHNHlsdkIrRUdHN3ZQTFd1RG9wRFZJZWdva3RldkpMVXhIdFFTZENRPT0K"
WINDOWS_TEST_TAG = "v2.5.5-brand-b-test.2"
WINDOWS_TEST_ASSET = "Moadoom_2.5.5_brand-b-test.2_x64-setup.exe"


def test_b_logo_is_exact_selected_source_and_referenced() -> None:
    assert hashlib.sha256(LOGO.read_bytes()).hexdigest() == "f0b103e3d9a2a9000db1a5ff3f6e2f00f43d2b3967507307e80ec1010fdec893"
    html = INDEX.read_text(encoding="utf-8")
    assert "assets/brand/moadoom-icon-b.svg" in html
    assert ">모<" not in html


def test_windows_stable_and_updater_metadata_match_verified_setup() -> None:
    stable = json.loads(WINDOWS.read_text(encoding="utf-8"))
    latest = json.loads(WINDOWS_LATEST.read_text(encoding="utf-8"))
    assert stable["version"] == "2.5.17"
    assert stable["url"] == WINDOWS_URL
    assert stable["fileName"] == WINDOWS_ASSET
    assert stable["fileSize"] == "182,948,211 bytes"
    assert stable["checksum"]["sha256"] == "fdf2853be160b38089d815f3f49397546b6cac425fb90b14188d88580a758c93"
    assert stable["signature"] == WINDOWS_SIGNATURE
    assert latest["version"] == "v2.5.17"
    assert set(latest["platforms"]) == {"windows-x86_64"}
    updater = latest["platforms"]["windows-x86_64"]
    assert updater["url"] == WINDOWS_URL
    assert updater["signature"] == WINDOWS_SIGNATURE
    assert latest["notes"] == stable["notes"]
    assert latest["pub_date"] == stable["pub_date"]


def test_android_metadata_is_explicitly_phase15_debug_beta() -> None:
    data = json.loads(ANDROID.read_text(encoding="utf-8"))
    assert data["status"] == "test"
    assert data["versionCode"] == 15
    assert data["versionName"] == "1.0.0-phase15"
    assert data["releaseType"] == "debug"
    assert data["minimumAndroid"] == "8.0"
    assert data["downloadUrl"] == ANDROID_URL
    assert data["fileName"] == ANDROID_ASSET
    assert data["fileSize"] == "32,696,813 bytes"
    assert data["checksum"]["sha256"] == "cf89af919adb7baaf220bc21eeb2d80b841ab2024ce117b60c8e7795d4557f72"
    assert any("기존 주소로 한 번 정상 연결" in item for item in data["requirements"])
    warning_text = " ".join(data["warnings"])
    assert "debug APK" in warning_text
    assert "실제 기기" in warning_text
    assert "완료되지 않았습니다" in warning_text


def test_windows_stable_is_separate_from_old_brand_test_candidate() -> None:
    stable = json.loads(WINDOWS.read_text(encoding="utf-8"))
    candidate = json.loads(WINDOWS_TEST.read_text(encoding="utf-8"))
    assert stable["version"] == "2.5.17"
    assert stable["url"] == WINDOWS_URL
    assert candidate["channel"] == "brand-test"
    assert candidate["internalVersion"] == "2.5.5"
    assert candidate["updaterArtifact"] is False
    assert candidate["fileSize"] == "195,045,033 bytes"
    assert candidate["checksum"]["sha256"] == "dfd688fdf559129b54966e9e948eb49f4481f343dc3b543dcb79773920233cc4"
    assert WINDOWS_TEST_TAG in candidate["downloadUrl"]
    assert candidate["downloadUrl"].endswith("/" + WINDOWS_TEST_ASSET)


def test_download_ui_links_stable_windows_and_phase15_android() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert f'href="{WINDOWS_URL}"' in html
    assert f'href="{ANDROID_URL}"' in html
    assert html.count('<article class="download-card">') == 2
    assert "<h3>Windows</h3>" in html
    assert "안정 버전 2.5.17" in html
    assert "Windows 10 이상 · 64비트" in html
    assert ">Windows용 다운로드<" in html
    assert "<h3>Android</h3>" in html
    assert ">APK 다운로드<" in html
    assert "Android 8.0 이상 · PC와 같은 Wi-Fi에서 연결" in html
    assert ">베타<" in html
    assert "베타 · 1.0.0-phase15" in html
    assert "가족 연결" in html
    assert "모아둠 계정 가입·로그인과 7일 무료체험을 반영한 최신 검수 버전입니다." in html
    assert "개발용 서명 APK" in html
    assert 'id="android-download"' in html
    assert 'id="windows-download"' in html
    assert 'id="android-version"' in html
    assert "알 수 없는 앱 설치" in html
    assert "기존 주소로 한 번 정상 연결" in html
    assert "실폰 QR·동기화 및 업데이트 설치 흐름의 전체 검증은 완료되지 않았습니다" in html
    for notice in ("phase11·12", "최초 한 번", "삭제하지 마세요", "브라우저 다운로드", "Android 설치 승인", "무인 업데이트가 아닙니다"):
        assert notice in html
        assert notice in " ".join(json.loads(ANDROID.read_text(encoding="utf-8"))["warnings"])
    assert 'id="windows-test-download"' not in html
    assert "v2.5.5-brand-b-test" not in html
    assert "v2.5.9-windows" not in html
    assert "untagged-" not in html  # Draft 임시 주소 금지
    assert f"releases/download/v2.5.10-windows/Insurance.AI_2.5.10" not in html
    for unsupported_claim in (
        "IP 변경 자동 연결 완료",
        "실폰 검증 완료",
        "Android 무인 자동 설치",
        "자동 결제",
        "만료 시 사용 차단",
        "안내 메일 자동 발송",
    ):
        assert unsupported_claim not in html
    assert "iOS" not in html
    assert "macOS" not in html


def test_smooth_scroll_does_not_intercept_download_buttons() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert "a[href^=\"#\"]:not(.download-button)" in html or "a[href^='#']:not(.download-button)" in html
    assert "const androidConfig=" in html
    assert "loadPlatformInfo(windowsConfig)" in html
    assert "loadPlatformInfo(androidConfig)" in html
