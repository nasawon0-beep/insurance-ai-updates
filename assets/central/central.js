// 모아둠 계정 공통 클라이언트(사이트). 권한 판단은 전부 서버(RLS/RPC)가 한다.
(function () {
  const cfg = window.MOADOOM_CENTRAL || {};
  function configured() {
    const url = cfg.url || "";
    const key = String(cfg.publishableKey || "");
    if (!key.startsWith("sb_publishable_")) return false;
    if (/^https:\/\/[a-z0-9-]+\.supabase\.co$/.test(url)) return true;
    // 로컬 QA 전용: 페이지 자체가 127.0.0.1에서 열렸을 때만 로컬 대역 서버 허용
    return location.hostname === "127.0.0.1" && /^http:\/\/127\.0\.0\.1:\d+$/.test(url);
  }
  // 로그인 모듈(supabase-js)은 서비스가 연결된 경우에만 불러온다. 미연결이면 외부 요청 자체가 없다.
  const SDK_SRC = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.118.0/dist/umd/supabase.min.js";
  const SDK_SRI = "sha384-UagCvVPT5XXA0Hx+nJYUAGBFseHT9zBgpJMSebsAxl9lciTwbT+39j5VfRjdP5Tp";
  let sdkPromise = null;
  function loadSdk() {
    if (!configured()) return Promise.reject(new Error("모아둠 계정 서비스가 아직 연결되지 않았습니다."));
    if (window.supabase && window.supabase.createClient) return Promise.resolve();
    sdkPromise = sdkPromise || new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = SDK_SRC;
      s.integrity = SDK_SRI;
      s.crossOrigin = "anonymous";
      s.onload = () => resolve();
      s.onerror = () => { sdkPromise = null; reject(new Error("로그인 모듈을 불러오지 못했습니다. 새로 고침해 주세요.")); };
      document.head.appendChild(s);
    });
    return sdkPromise;
  }
  // 미연결 상태: 화면의 모든 입력·버튼을 잠그고 제출을 막는다(입력 수집·저장·전송 없음).
  function lockAll() {
    document.querySelectorAll("main input, main button, main select, main textarea").forEach((el) => {
      el.disabled = true;
      if (el.tagName === "INPUT") { el.value = ""; el.placeholder = ""; }
    });
    document.querySelectorAll("main form").forEach((f) => {
      f.setAttribute("aria-disabled", "true");
      f.addEventListener("submit", (ev) => { ev.preventDefault(); ev.stopImmediatePropagation(); }, true);
    });
  }
  function signupOpen() {
    return configured() && cfg.signupOpen === true;
  }
  let client = null;
  function sb() {
    if (!configured()) throw new Error("모아둠 계정 서비스가 아직 연결되지 않았습니다.");
    if (!window.supabase || !window.supabase.createClient) throw new Error("로그인 모듈을 불러오지 못했습니다. 새로 고침해 주세요.");
    client = client || window.supabase.createClient(cfg.url, cfg.publishableKey, {
      auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true, storageKey: "moadoom.site.session" },
    });
    return client;
  }
  const KO = [
    [/invalid login credentials/i, "이메일 또는 비밀번호가 올바르지 않습니다."],
    [/email not confirmed/i, "이메일 확인이 끝나지 않았습니다. 가입 확인 메일의 링크를 눌러 주세요."],
    [/user already registered/i, "이미 가입된 이메일입니다. 로그인하거나 비밀번호를 재설정하세요."],
    [/password should be at least/i, "비밀번호가 너무 짧습니다."],
    [/rate limit|too many/i, "요청이 많습니다. 잠시 후 다시 시도하세요."],
    [/email address not authorized|error sending (confirmation|recovery|magic link)? ?email|sending email/i, "지금은 이 이메일로 안내 메일을 보낼 수 없습니다(메일 발송 설정 준비 중). 관리자에게 문의하세요."],
    [/operator role required/i, "권한이 없습니다(이용 상태 변경은 소유자만 가능합니다)."],
    [/cannot change own subscription/i, "자기 계정의 이용 상태는 직접 변경할 수 없습니다."],
    [/reason required/i, "변경 사유를 입력하세요."],
    [/ends_on required/i, "종료일을 입력하세요."],
    [/ends_on must be today or later/i, "종료일은 오늘 이후여야 합니다."],
    [/trial days must be/i, "체험 일수는 1~90일입니다."],
    [/lifetime has no end/i, "무기한 무료에는 종료일이 없어 연장/단축할 수 없습니다. 기간지정으로 바꾸세요."],
    [/shortened end would be before start/i, "그만큼 단축하면 시작 시각보다 앞서게 됩니다."],
    [/days must be/i, "연장/단축 일수는 0이 아닌 -3660~3660일입니다."],
    [/no subscription to/i, "이용권이 없습니다. 먼저 무료체험/기간지정/무기한 무료 중 하나를 지정하세요."],
    [/already suspended/i, "이미 이용정지 상태입니다."],
    [/not suspended/i, "이용정지 상태가 아닙니다."],
    [/notice days must be/i, "안내 일수는 1~30일, 최대 5개입니다."],
    [/failed to fetch|network/i, "서버에 연결할 수 없습니다. 인터넷 연결을 확인하세요."],
  ];
  function ko(err) {
    const m = (err && (err.message || err.error_description)) || String(err);
    for (const [re, text] of KO) if (re.test(m)) return text;
    return m;
  }
  function setMsg(el, text, kind) {
    el.textContent = text || "";
    el.className = "msg" + (kind ? " " + kind : "");
  }
  // 한국 표준시 표시(판정은 서버 시각 기준)
  function kst(iso) {
    if (!iso) return "—";
    const t = Date.parse(iso);
    if (isNaN(t)) return String(iso);
    return new Date(t + 9 * 3600 * 1000).toISOString().slice(0, 16).replace("T", " ");
  }
  function remaining(sec) {
    if (sec == null) return "";
    if (sec <= 0) return "0분";
    const d = Math.floor(sec / 86400), h = Math.floor((sec % 86400) / 3600), m = Math.floor((sec % 3600) / 60);
    if (d > 0) return h > 0 ? `${d}일 ${h}시간` : `${d}일`;
    if (h > 0) return `${h}시간 ${m}분`;
    return `${Math.max(1, m)}분`;
  }
  const KIND = { trial: "무료체험", term: "기간 이용", lifetime: "무기한 무료" };
  const STATUS = { active: "이용 중", expired: "기간 종료", suspended: "이용정지", none: "이용권 없음", scheduled: "시작 전" };
  // 한 줄 상태 문구(사이트·관리자 공통)
  function describe(sub, role) {
    if (role === "owner") return "소유자 계정 — 이용권과 무관하게 사용";
    const s = sub || {};
    if (s.status === "none" || !s.kind) return "이용권 없음";
    const k = KIND[s.kind] || s.kind;
    if (s.status === "suspended") return `${k} · 이용정지`;
    if (s.status === "expired") return `${k} · 종료됨 (${kst(s.ends_at)})`;
    if (s.kind === "lifetime") return "무기한 무료 · 사용 중 (종료일 없음)";
    return `${k} · 사용 중 · 남은 기간 ${remaining(s.remaining_seconds)}`;
  }
  window.MoadoomCentral = { configured, signupOpen, loadSdk, lockAll, sb, ko, setMsg, kst, remaining, describe, KIND, STATUS };
})();
