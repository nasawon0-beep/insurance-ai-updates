"""공개 사이트 계정 화면(가입·로그인·재설정·관리자) 미연결 안전 상태 검사.

계정 서비스(Supabase)가 연결되기 전 공개해도 안전한지 정적으로 확인한다:
빈 설정, 비밀/QA 주소 없음, 정적 외부 로그인 SDK 없음(연결 시에만 동적 로드), 준비 중 안내, 진입 링크.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PAGES = [ROOT / "account" / "index.html", ROOT / "account" / "reset.html", ROOT / "admin" / "index.html"]
CENTRAL = ROOT / "assets" / "central"
ALL = PAGES + [CENTRAL / "central.js", CENTRAL / "central.css", CENTRAL / "config.js"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_public_config_is_empty_and_publishable_only() -> None:
    cfg = read(CENTRAL / "config.js")
    assert re.search(r'url:\s*""', cfg)
    assert re.search(r'publishableKey:\s*""', cfg)


def test_no_secrets_qa_urls_or_sample_accounts() -> None:
    bad = [
        r"sb_secret_", r"service_role\s*[:=]", r"eyJhbGciOi", r"sb_publishable_[A-Za-z0-9]", r"127\.0\.0\.1:\d",
        r"localhost:\d", r"54399", r"@example\.test", r"qa-(owner|member)", r"QA합성", r"__qa/",
        r"\.supabase\.co[\"'/]",
    ]
    for p in ALL:
        text = read(p)
        for pat in bad:
            assert not re.search(pat, text), f"{p.name}: {pat}"


def test_login_sdk_is_not_loaded_statically() -> None:
    for p in PAGES:
        assert "supabase.min.js" not in read(p), p.name
    js = read(CENTRAL / "central.js")
    assert "function loadSdk()" in js and "if (!configured()) return Promise.reject" in js
    assert 'integrity = SDK_SRI' in js


def test_unconfigured_pages_show_preparing_notice_and_lock_inputs() -> None:
    for p in PAGES:
        html = read(p)
        assert "회원가입·로그인 연결 준비 중" in html, p.name
        assert re.search(r"if \(!C\.configured\(\)\) \{[^}]*C\.lockAll\(\); return; \}", html), p.name
    js = read(CENTRAL / "central.js")
    assert "el.disabled = true" in js and "ev.preventDefault(); ev.stopImmediatePropagation();" in js
    account = read(PAGES[0])
    assert "7일 무료체험은 계정 서비스가 연결된 뒤" in account and "지금은 체험이 시작되지 않습니다" in account


def test_admin_has_no_public_entry_and_requires_server_role() -> None:
    index = read(INDEX)
    assert "admin/" not in index
    admin = read(PAGES[2])
    assert 'me.role !== "owner" && me.role !== "admin"' in admin
    account = read(PAGES[0])
    assert 'id="adminLink" href="../admin/" hidden' in account


def test_main_page_links_to_account_on_desktop_and_mobile() -> None:
    index = read(INDEX)
    assert '<a class="nav-account" href="account/">가입·로그인</a>' in index
    assert ".nav a.nav-account{display:inline-block}" in index
    assert index.index(".nav a.nav-account{display:inline-block}") > index.index(".nav a:not(.nav-cta){display:none}")
    assert '<a href="account/">모아둠 계정(연결 준비 중)</a>' in index


def test_account_pages_noindex() -> None:
    for p in PAGES:
        assert '<meta name="robots" content="noindex">' in read(p), p.name
