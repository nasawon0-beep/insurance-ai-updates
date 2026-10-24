from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
ANDROID = ROOT / "api" / "android.json"
WINDOWS_TEST = ROOT / "api" / "windows-brand-test.json"
LOGO = ROOT / "assets" / "brand" / "moadoom-icon-b.svg"
ANDROID_TEST_TAG = "v2.5.5-brand-b-test.1"
WINDOWS_TEST_TAG = "v2.5.5-brand-b-test.2"
ANDROID_ASSET = "Moadoom_Android_1.0.0-phase1_debug.apk"
WINDOWS_ASSET = "Moadoom_2.5.5_brand-b-test.2_x64-setup.exe"


def test_b_logo_is_exact_selected_source_and_referenced() -> None:
    assert hashlib.sha256(LOGO.read_bytes()).hexdigest() == "f0b103e3d9a2a9000db1a5ff3f6e2f00f43d2b3967507307e80ec1010fdec893"
    html = INDEX.read_text(encoding="utf-8")
    assert "assets/brand/moadoom-icon-b.svg" in html
    assert ">모<" not in html


def test_android_metadata_is_explicitly_debug_test_only() -> None:
    data = json.loads(ANDROID.read_text(encoding="utf-8"))
    assert data["status"] == "test"
    assert data["versionCode"] == 1
    assert data["versionName"] == "1.0.0-phase1"
    assert data["releaseType"] == "debug"
    assert data["minimumAndroid"] == "8.0"
    assert data["checksum"]["sha256"] == "f973fcaf6405727d4a0e79712c6491767c051ddbbf293c618f03728f8e467c0d"
    assert ANDROID_TEST_TAG in data["downloadUrl"]
    assert data["downloadUrl"].endswith("/" + ANDROID_ASSET)


def test_windows_stable_is_separate_from_brand_test_candidate() -> None:
    stable = json.loads((ROOT / "api" / "windows.json").read_text(encoding="utf-8"))
    candidate = json.loads(WINDOWS_TEST.read_text(encoding="utf-8"))
    assert stable["version"] == "2.5.5"
    assert stable["url"].endswith("/v2.5.5-windows/Insurance.AI_2.5.5_x64-setup.exe")
    assert candidate["channel"] == "brand-test"
    assert candidate["internalVersion"] == "2.5.5"
    assert candidate["updaterArtifact"] is False
    assert candidate["fileSize"] == "195,045,033 bytes"
    assert candidate["checksum"]["sha256"] == "dfd688fdf559129b54966e9e948eb49f4481f343dc3b543dcb79773920233cc4"
    assert WINDOWS_TEST_TAG in candidate["downloadUrl"]
    assert candidate["downloadUrl"].endswith("/" + WINDOWS_ASSET)


def test_download_ui_has_real_asset_links_and_visible_debug_warning() -> None:
    html = INDEX.read_text(encoding="utf-8")
    android_url = json.loads(ANDROID.read_text(encoding="utf-8"))["downloadUrl"]
    windows_test_url = json.loads(WINDOWS_TEST.read_text(encoding="utf-8"))["downloadUrl"]
    assert f'href="{android_url}"' in html
    assert f'href="{windows_test_url}"' in html
    assert "바로가기 아이콘 지속 수정 포함" in html
    assert "Windows 화면 표시 최종 확인 전" in html
    assert 'id="android-download"' in html
    assert 'id="windows-test-download"' in html
    assert "Android 테스트 버전(APK)" in html
    assert "디버그 인증서" in html
    assert "UI 개편은 아직 완료되지 않았습니다" in html
    assert "Android 8.0 이상" in html
    assert "같은 Wi-Fi" in html
    assert "분석은 PC" in html
    assert "알 수 없는 앱 설치" in html
    assert "iOS" not in html
    assert "macOS" not in html


def test_smooth_scroll_does_not_intercept_download_buttons() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert "a[href^=\"#\"]:not(.download-button)" in html or "a[href^='#']:not(.download-button)" in html
