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


def test_download_ui_is_customer_facing_with_two_primary_cards() -> None:
    html = INDEX.read_text(encoding="utf-8")
    android_url = json.loads(ANDROID.read_text(encoding="utf-8"))["downloadUrl"]
    windows_test_url = json.loads(WINDOWS_TEST.read_text(encoding="utf-8"))["downloadUrl"]
    assert f'href="{android_url}"' in html
    assert f'href="{windows_test_url}"' in html
    assert html.count('<article class="download-card">') == 2
    assert "<h3>Windows</h3>" in html
    assert "Windows 10 이상 · 64비트" in html
    assert ">Windows용 다운로드<" in html
    assert "<h3>Android</h3>" in html
    assert ">APK 다운로드<" in html
    assert "Android 8.0 이상 · PC와 같은 Wi-Fi에서 연결" in html
    assert ">베타<" in html
    assert "개선 중인 버전입니다." in html
    assert "새 버전 미리보기" in html
    assert "미리보기 버전입니다." in html
    assert "개발용 서명 APK" in html
    assert 'id="android-download"' in html
    assert 'id="windows-test-download"' in html
    assert "알 수 없는 앱 설치" in html
    for internal_copy in (
        "브랜드",
        "후보",
        "내부 버전",
        "versionCode",
        "updater JSON",
        "검증",
        "실기기 미확인",
        "DEBUG TEST",
    ):
        assert internal_copy not in html
    assert "iOS" not in html
    assert "macOS" not in html


def test_smooth_scroll_does_not_intercept_download_buttons() -> None:
    html = INDEX.read_text(encoding="utf-8")
    assert "a[href^=\"#\"]:not(.download-button)" in html or "a[href^='#']:not(.download-button)" in html
