from flask import Blueprint, render_template, request, jsonify
import pandas as pd
import os

sentiment_bp = Blueprint("sentiment", __name__, template_folder="templates", static_folder="static")

DATA_PATH = "data/fan_sentiment.csv"

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
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame(columns=["팀","긍정비율","중립비율","부정비율","예시_긍정","예시_중립","예시_부정"])
    return pd.read_csv(DATA_PATH)

def _thermo_comment(temp):
    t = int(temp)
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

@sentiment_bp.route("/sentiment")
def sentiment_page():
    df = _load_df()
    teams = df["팀"].tolist()
    return render_template("sentiment.html", team_list=teams)

@sentiment_bp.route("/api/teaminfo")
def api_teaminfo():
    team = request.args.get("team")
    df = _load_df()
    row = df[df["팀"] == team]
    if row.empty:
        return jsonify({"error": "team not found"}), 404
    r = row.iloc[0]
    pos = float(r["긍정비율"])
    logo_path = f"/static/logos/{team}.png"
    return jsonify({
        "team": team,
        "temperature": int(pos),
        "fill_color": "#ff5a36" if pos>=80 else "#ffd600" if pos>=40 else "#4fc3f7",
        "headline": TEAM_SLOGANS.get(team, ""),
        "temp_comment": _thermo_comment(pos),
        "logo_path": logo_path,
        "예시_긍정": r.get("예시_긍정", ""),
        "예시_부정": r.get("예시_부정", ""),
    })
