"""공개 사이트 계정 화면(로그인·재설정·관리자) 실제 서비스 연결 후보 검사.

- config.js: 실제 프로젝트 URL + publishable(공개) 키만, 신규 가입 열림(signupOpen=true, Gmail SMTP 설정 완료 후)
- 비밀/QA 흔적 없음, 로그인 SDK는 설정된 경우에만 동적 로드
- 설정이 비면(롤백 등) 기존 '연결 준비 중' 잠금 경로 유지
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PAGES = [ROOT / "account" / "index.html", ROOT / "account" / "reset.html", ROOT / "admin" / "index.html"]
CENTRAL = ROOT / "assets" / "central"
ALL = PAGES + [CENTRAL / "central.js", CENTRAL / "central.css", CENTRAL / "config.js"]
PROJECT_URL = "https://fhdushntttxbfwkxylhz.supabase.co"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_public_config_has_only_project_url_publishable_key_and_open_signup() -> None:
    cfg = read(CENTRAL / "config.js")
    assert f'url: "{PROJECT_URL}"' in cfg
    keys = re.findall(r'publishableKey:\s*"([^"]*)"', cfg)
    assert len(keys) == 1 and re.fullmatch(r"sb_publishable_[A-Za-z0-9_-]{20,}", keys[0])
    assert re.search(r"signupOpen:\s*true", cfg)
    assert len(re.findall(r"sb_[a-z]+_[A-Za-z0-9]", cfg)) == 1  # 공개키 1개 외 다른 키 없음


def test_no_secrets_qa_urls_or_sample_accounts() -> None:
    bad = [
        r"sb_secret_", r"service_role\s*[:=]", r"eyJhbGciOi", r"127\.0\.0\.1:\d", r"localhost:\d", r"54399",
        r"@example\.test", r"qa-(owner|member)", r"QA합성", r"__qa/", r"PRIVATE KEY", r"SIGNING_KEY",
    ]
    for p in ALL:
        text = read(p)
        for pat in bad:
            assert not re.search(pat, text), f"{p.name}: {pat}"
    for p in ALL:
        if p.name != "config.js":
            assert not re.search(r"sb_publishable_[A-Za-z0-9]", read(p)), p.name


def test_login_sdk_is_not_loaded_statically() -> None:
    for p in PAGES:
        assert "supabase.min.js" not in read(p), p.name
    js = read(CENTRAL / "central.js")
    assert "function loadSdk()" in js and "if (!configured()) return Promise.reject" in js
    assert "integrity = SDK_SRI" in js


def test_signup_gate_kept_and_mail_ready_wording() -> None:
    # 가입 개방은 config.js 한 곳(signupOpen)으로만 — 닫힘 경로 코드는 롤백용으로 유지
    js = read(CENTRAL / "central.js")
    assert "return configured() && cfg.signupOpen === true;" in js
    account = read(PAGES[0])
    assert "지금은 기존 모아둠 계정 로그인만 가능합니다" in account
    assert '$("tabSignup").disabled = true;' in account
    assert 'if (m === "signup" && !signupOpen) return;' in account
    assert 'if (!signupOpen) throw new Error("신규 회원가입은 아직 열리지 않았습니다.");' in account
    index = read(INDEX)
    assert "가입·로그인" in index
    for p in ALL:
        assert "준비 중이라" not in read(p) and "메일 발송 설정 준비 중" not in read(p), p.name
    assert "스팸함을 확인하세요" in read(PAGES[1])


def test_unconfigured_fallback_still_locks_everything() -> None:
    for p in PAGES:
        html = read(p)
        assert "회원가입·로그인 연결 준비 중" in html, p.name
        assert re.search(r"if \(!C\.configured\(\)\) \{[^}]*C\.lockAll\(\); return; \}", html), p.name
    js = read(CENTRAL / "central.js")
    assert "el.disabled = true" in js and "ev.preventDefault(); ev.stopImmediatePropagation();" in js


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
    assert '<a href="account/">모아둠 계정</a>' in index


def test_callback_urls_are_page_relative() -> None:
    assert "emailRedirectTo: location.origin + location.pathname" in read(PAGES[0])
    assert "redirectTo: location.origin + location.pathname" in read(PAGES[1])


def test_account_pages_noindex() -> None:
    for p in PAGES:
        assert '<meta name="robots" content="noindex">' in read(p), p.name


def test_owner_view_separates_permission_from_past_trial_record() -> None:
    js = read(CENTRAL / "central.js")
    assert 'if (role === "owner") return "사용 가능 — 소유자 권한(이용권 기간과 무관)";' in js
    assert "function ownerRecord(sub)" in js and "소유자 사용에는 영향 없음" in js
    account = read(PAGES[0])
    assert '$("meStartLabel").textContent = owner ? "일반 이용권 기록" : "시작";' in account
    assert '$("meEndLabel").hidden = owner; $("meEnd").hidden = owner;' in account
    assert "if (owner) $(\"meStart\").textContent = C.ownerRecord(s);" in account
