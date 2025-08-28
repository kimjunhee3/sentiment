from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import os

sentiment_bp = Blueprint("sentiment", __name__, template_folder="templates", static_folder="static")

# 결과 집계 CSV (노트북이 저장하는 파일명에 맞춤)
DATA_PATH = os.environ.get("SENT_DATA_PATH", "data/sentiment_fine.csv")

# 팀별 슬로건
TEAM_SLOGANS = {
    "한화": "최강 한화! 이글스의 불꽃을 함께 피워요",
    "KIA": "남행열차! 타이거즈의 승리를 향해 달려요!",
    "롯데": "마, 롯데를 위해 응원 함 해보입시더!",
    "삼성": "뜨거운 대구별과 같은 열정으로 응원하자!",
    "LG": "무적 LG, 신바람 야구 함께 응원하자!",
    "두산": "승리를 위하여! 베어스 10번타자 모여라!",
    "SSG": "투혼의 랜더스! 으쓱이들 집합, 여기로 모여!",
    "키움": "영웅출정가! 히어로즈의 승리를 위한 함성!",
    "NC": "집행검을 들어올리자! 다이노스, 함께 해요!",
    "KT": "우리는 kt wiz! 마법같은 시즌을 위해!",
}

def _load_df():
    base_cols = ["팀", "긍정비율", "중립비율", "부정비율", "예시_긍정", "예시_중립", "예시_부정"]
    # CSV가 있으면 사용
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            for c in base_cols:
                if c not in df.columns:
                    df[c] = "" if c.startswith("예시_") else 0
            df = df[base_cols]
            if len(df) > 0:
                return df
        except Exception as e:
            print("[sentiment_fine.csv read error]", e)
    # CSV가 없거나 비면 슬로건 키로 기본 목록
    rows = []
    for team in TEAM_SLOGANS.keys():
        rows.append({ "팀": team, "긍정비율": 0, "중립비율": 0, "부정비율": 0,
                      "예시_긍정": "", "예시_중립": "", "예시_부정": "" })
    return pd.DataFrame(rows, columns=base_cols)

def _thermo_comment(temp):
    t = int(float(temp or 0))
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

def _read_comments_csv(path):
    """주어진 CSV에서 id/닉네임, 텍스트 컬럼을 자동 탐색해서 리스트 반환"""
    if not os.path.exists(path):
        return []
    try:
        df = pd.read_csv(path)
    except Exception:
        return []
    # id, text/comment 추정
    id_col = None
    for c in df.columns:
        lc = c.lower()
        if "id" in lc or "author" in lc or "user" in lc or "닉" in lc:
            id_col = c; break
    text_col = None
    for c in df.columns:
        lc = c.lower()
        if "comment" in lc or "text" in lc or "내용" in lc or "댓글" in lc:
            text_col = c; break
    if not text_col:
        return []
    out = []
    for _, row in df.iterrows():
        rid = str(row.get(id_col, "")).strip() if id_col else ""
        txt = str(row.get(text_col, "")).strip()
        if not txt:
            continue
        out.append({"id": rid, "comment": txt})
    return out

def _load_team_comments(team, limit=10):
    """
    data/<팀>_유튜브.csv, data/<팀>_댓글.csv 를 순서대로 읽어 최대 limit개를 반환.
    파일이 둘 다 있으면 유튜브 몇 개 + 댓글 몇 개 섞어서 limit 맞춥니다.
    """
    base = "data"
    yt = _read_comments_csv(os.path.join(base, f"{team}_유튜브.csv"))
    nk = _read_comments_csv(os.path.join(base, f"{team}_댓글.csv"))
    # 우선순위: 유튜브 → 네이버톡, 섞어서 상위 limit개
    out = []
    i = j = 0
    while len(out) < limit and (i < len(yt) or j < len(nk)):
        if i < len(yt):
            out.append(yt[i]); i += 1
        if len(out) >= limit: break
        if j < len(nk):
            out.append(nk[j]); j += 1
    return out[:limit]

@sentiment_bp.route("/sentiment")
def sentiment_page():
    """임베드 가능. /sentiment?team=한화&embed=1"""
    df = _load_df()
    teams = df["팀"].tolist()
    initial_team = request.args.get("team", "")
    embed = request.args.get("embed", "0")
    return render_template("sentiment.html",
                           team_list=teams,
                           initial_team=initial_team,
                           embed=str(embed))

@sentiment_bp.route("/api/teaminfo")
def api_teaminfo():
    """팀 요약 + 댓글 반환. ?team=한화&count=10"""
    team = request.args.get("team")
    count = int(request.args.get("count", 10))
    df = _load_df()
    row = df[df["팀"] == team]
    if row.empty:
        return jsonify({"error": "team not found"}), 404
    r = row.iloc[0]
    pos = float(r.get("긍정비율", 0))
    fill = "#ff5a36" if pos >= 80 else "#ffd600" if pos >= 40 else "#4fc3f7"

    comments = _load_team_comments(team, limit=count)

    return jsonify({
        "team": team,
        "temperature": int(pos),
        "fill_color": fill,
        "headline": TEAM_SLOGANS.get(team, ""),
        "temp_comment": _thermo_comment(pos),
        "logo_path": f"/static/logos/{team}.png",
        "예시_긍정": r.get("예시_긍정", ""),
        "예시_부정": r.get("예시_부정", ""),
        "comments": comments
    })

@sentiment_bp.route("/api/teams")
def api_teams():
    df = _load_df()
    return jsonify({"teams": df["팀"].tolist()})
