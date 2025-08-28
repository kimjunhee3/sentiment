# sentiment_routes.py
from flask import Blueprint, request, jsonify, render_template, send_from_directory, abort
import pandas as pd
import os

# ---------------------------
# 경로 / 기본값
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
STATIC_LOGOS_DIR = os.path.join(BASE_DIR, "static", "logos")
DATA_LOGOS_DIR = os.path.join(DATA_DIR, "logos")   # 깃에 올린 data/logos 지원
DEFAULT_TEAM = os.environ.get("DEFAULT_TEAM", "SSG")

sentiment_bp = Blueprint(
    "sentiment",
    __name__,
    template_folder="templates",
    static_folder="static",
)

# ---------------------------
# CSV 지연 로딩(서버 부팅 시 파일 없어도 앱 안 죽게)
# ---------------------------
_fan_df_cache = None

def _load_fan_df():
    for path in [
        os.path.join(DATA_DIR, "fan_sentiment.csv"),
        os.path.join(DATA_DIR, "sentiment_fine.csv"),
        "fan_sentiment.csv",
        "sentiment_fine.csv",
    ]:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                if "팀" in df.columns:
                    return df
            except Exception:
                pass
    # 없으면 빈 DF
    return pd.DataFrame(columns=["팀", "긍정비율"])

def get_fan_df():
    global _fan_df_cache
    if _fan_df_cache is None:
        _fan_df_cache = _load_fan_df()
    return _fan_df_cache

# ---------------------------
# 정적 로고 서빙: static/logos 와 data/logos 둘 다
# ---------------------------
@sentiment_bp.route("/logos/<path:filename>")
def serve_logo_files(filename):
    static_path = os.path.join(STATIC_LOGOS_DIR, filename)
    if os.path.exists(static_path):
        return send_from_directory(STATIC_LOGOS_DIR, filename)
    data_path = os.path.join(DATA_LOGOS_DIR, filename)
    if os.path.exists(data_path):
        return send_from_directory(DATA_LOGOS_DIR, filename)
    abort(404)

# ---------------------------
# 구단 슬로건 / 파일명 힌트
# ---------------------------
TEAM_SLOGANS = {
    "한화": "최강 한화! 이글스의 불꽃을 함께 피워요",
    "KIA": "남행열차! 타이거즈의 승리를 향해 달려요!",
    "롯데": "마, 롯데를 위해 응원 함 해보입시더!",
    "삼성": "뜨거운 대구별과 같은 열정으로 응원하자!",
    "LG":  "무적 LG, 신바람 야구 함께 응원하자!",
    "두산": "승리를 위하여! 베어스 10번타자 모여라!",
    "SSG": "투혼의 랜더스! 으쓱이들 집합, 여기로 모여!",
    "키움": "영웅출정가! 히어로즈의 승리를 위한 함성!",
    "NC":  "집행검을 들어올리자! 다이노스, 함께 해요!",
    "KT":  "우리는 kt wiz! 마법같은 시즌을 위해!",
}

# 기본 확장자는 png로 가정(없으면 jpg/팀명.png 순으로 폴백)
TEAM_LOGO_FILE = {
    "KIA": "KIA.png",
    "두산": "두산.png",
    "LG": "LG.png",
    "키움": "키움.png",
    "KT": "KT.png",
    "한화": "한화.png",
    "롯데": "롯데.png",
    "NC": "NC.png",
    "삼성": "삼성.png",
    "SSG": "SSG.png",
}

# ---------------------------
# 온도 메시지/색
# ---------------------------
def temperature_comment(t):
    try:
        t = int(t)
    except Exception:
        t = 0
    if t <= 10: return "❄ 팬심 얼음장처럼 싸늘"
    if t <= 20: return "🧊 냉기 가득, 차가운 시선"
    if t <= 30: return "😨 불안감 감돌아, 걱정 섞인 반응"
    if t <= 40: return "😟 아쉬움과 우려, 불만 서려"
    if t <= 50: return "🌫 반신반의, 엇갈린 반응"
    if t <= 60: return "🌥 살짝 긍정 흐름이 보이는 중"
    if t <= 70: return "🌤 응원 분위기 점점 살아나"
    if t <= 80: return "😊 팬심 점화! 긍정 열기 감돌아"
    if t <= 90: return "🔥 뜨거운 응원! 팬심 활활 타오름"
    return "❤️ 팬심 폭발! 열광적 지지 쇄도"

def temperature_color(t):
    try:
        t = int(t)
    except Exception:
        t = 0
    if t <= 20:
        r, g, b = 0, 0, int(139 + (116 * (t / 20)))
    elif t <= 50:
        ratio = (t - 20) / 30
        r, g, b = int(255 * ratio), 0, int(255 * (1 - ratio))
    else:
        r, g, b = 255, 0, 0
    return f"rgb({r},{g},{b})"

# ---------------------------
# 페이지 템플릿(필요시 사용)
# ---------------------------
@sentiment_bp.route("/sentiment")
def sentiment_page():
    return render_template("sentiment.html")

# ---------------------------
# 팀 목록 API (드롭다운용)
# ---------------------------
@sentiment_bp.route("/api/teams")
def api_teams():
    df = get_fan_df()
    teams = []
    if "팀" in df.columns:
        teams = [t for t in df["팀"].dropna().unique().tolist() if str(t).strip()]
    if not teams:
        teams = ["SSG","LG","두산","키움","KIA","KT","NC","롯데","삼성","한화"]
    return jsonify({"teams": teams, "default": DEFAULT_TEAM})

# ---------------------------
# 팀 정보/댓글 API
# ---------------------------
@sentiment_bp.route("/api/teaminfo")
def api_teaminfo():
    df = get_fan_df()

    # 팀 결정
    req_team = request.args.get("team")
    teams = list(df["팀"].dropna().unique()) if "팀" in df.columns else []
    if req_team and (not teams or req_team in teams):
        team = req_team
    elif teams:
        team = teams[0]
    else:
        team = DEFAULT_TEAM

    # 긍정비율
    pos = 0
    if "팀" in df.columns and "긍정비율" in df.columns and team in teams:
        try:
            pos = int(df.loc[df["팀"] == team, "긍정비율"].iloc[0])
        except Exception:
            pos = 0

    # 댓글 개수 파라미터 (기본 10, 상한 100)
    try:
        req_count = int(request.args.get("count", 10))
    except Exception:
        req_count = 10
    req_count = max(1, min(req_count, 100))

    # 로고 파일 탐색: 매핑 → 팀명.png → 팀명.jpg (static, data 순서)
    def _find_logo(candidate_name: str):
        candidates = []
        # 명시 매핑
        candidates += [
            os.path.join(STATIC_LOGOS_DIR, candidate_name),
            os.path.join(DATA_LOGOS_DIR, candidate_name),
        ]
        base = os.path.splitext(candidate_name)[0]
        # 팀명.png / 팀명.jpg
        for ext in (".png", ".jpg", ".jpeg"):
            candidates += [
                os.path.join(STATIC_LOGOS_DIR, f"{team}{ext}"),
                os.path.join(DATA_LOGOS_DIR, f"{team}{ext}"),
            ]
        for p in candidates:
            if os.path.exists(p):
                return os.path.basename(p)
        return None

    logo_hint = TEAM_LOGO_FILE.get(team, f"{team}.png")
    logo_file = _find_logo(logo_hint)
    logo_path = f"/logos/{logo_file}" if logo_file else ""

    # 댓글 수집
    comments = []
    for base in (f"{team}_유튜브.csv", f"{team}_댓글.csv"):
        path = os.path.join(DATA_DIR, base)
        if not os.path.exists(path):
            continue
        try:
            cdf = pd.read_csv(path)
        except Exception:
            continue
        id_col   = next((c for c in cdf.columns if "id" in c.lower() or "nickname" in c.lower()), None)
        text_col = next((c for c in cdf.columns if "comment" in c.lower() or "text" in c.lower() or "댓글" in c), None)
        if not text_col:
            continue
        for _, r in cdf.iterrows():
            nick = (str(r[id_col]).strip() if id_col and pd.notna(r.get(id_col)) else "익명")
            text = str(r.get(text_col, "")).strip()
            if text:
                comments.append({"id": nick or "익명", "comment": text})

    # 요청한 개수만큼 반환(로테이션 용)
    comments = comments[:req_count]

    return jsonify({
        "team": team,
        "logo_path": logo_path,
        "temperature": pos,
        "fill_color": temperature_color(pos),
        "headline": TEAM_SLOGANS.get(team, ""),
        "temp_comment": temperature_comment(pos),
        "comments": comments,
    })
