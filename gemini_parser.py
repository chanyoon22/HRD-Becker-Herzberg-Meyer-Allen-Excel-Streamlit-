"""
gemini_parser.py — Gemini API 연동 파싱 모듈 v4
정책 자유 서술 → 30개 파라미터 수치화
"""

import json
import re
import httpx
from simulator import PolicyParams

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

SYSTEM_PROMPT = """당신은 HRD 전문가입니다. 사용자가 자유롭게 서술한 HR 정책을 읽고,
아래 JSON 스키마에 맞게 30개 파라미터를 수치화하세요.

규칙:
1. 언급되지 않은 숫자 파라미터 → 반드시 0
2. 언급되지 않은 문자열 파라미터 → 반드시 "" (빈 문자열)
3. culture_scope: "전부서" / "일부" / "미도입" 중 하나
4. mentoring, idea_system, eap: "예" 또는 "아니오"
5. retro_freq: "주1" / "격주" / "월1" / "없음" 중 하나
6. 반드시 JSON만 반환. 설명, 마크다운 없이 순수 JSON

JSON 스키마:
{
  "edu_cost_rate": 0~100 (교육비 증가율 %),
  "edu_hours": 0~200 (교육시간 목표 시간),
  "rnd_extra_hours": 0~80 (R&D 추가교육 시간),
  "online_ratio": 0~100 (온라인 학습 비중 %),
  "completion_rate": 0~100 (교육 이수율 %),
  "ojt_ratio": 0~100 (OJT 비중 %),
  "salary_raise": 0~30 (연봉 인상률 %),
  "sa_incentive": 0~50 (S고과 인센티브 %),
  "a_incentive": 0~30 (A고과 인센티브 %),
  "promotion_shortcut": 0~3 (승진 소요연수 단축 년),
  "welfare_score": 0~50 (복지포인트 증가율 %),
  "market_salary_pct": 0~130 (시장 대비 연봉수준 %),
  "culture_scope": "미도입"|"일부"|"전부서",
  "mentoring": "예"|"아니오",
  "idea_system": "예"|"아니오",
  "eap": "예"|"아니오",
  "retro_freq": "없음"|"월1"|"격주"|"주1",
  "vision_sharing": 0~12 (비전 공유 회/년),
  "remote_days_per_week": 0~5 (주당 재택근무 일),
  "overtime_cap_hours": 0~20 (주 연장근무 상한 시간),
  "eval_cycle_months": 0~12 (성과평가 주기 개월),
  "peer_review_weight": 0~100 (다면평가 반영률 %),
  "internal_posting_ratio": 0~100 (사내공모 비율 %),
  "idp_support_budget": 0~500 (IDP 지원비 만원/인),
  "leader_coaching_hours": 0~150 (리더 코칭 연간 시간),
  "onboarding_period_days": 0~180 (온보딩 기간 일),
  "burnout_check_freq": 0~12 (번아웃 진단 연간 횟수),
  "work_life_balance_budget": 0~500 (일생활균형 지원금 만원/인),
  "team_building_freq": 0~12 (팀빌딩 연간 횟수)
}"""


def parse_policy(policy_text: str, api_key: str) -> PolicyParams:
    """자유 서술 → PolicyParams 변환"""
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    body = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n정책 서술:\n{policy_text}"}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1500},
    }

    try:
        resp = httpx.post(GEMINI_URL, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        raw  = data["candidates"][0]["content"]["parts"][0]["text"]
        raw  = re.sub(r"```(?:json)?|```", "", raw).strip()
        parsed = json.loads(raw)
        return _dict_to_params(parsed)
    except Exception as e:
        raise RuntimeError(f"Gemini 파싱 실패: {e}")


def _dict_to_params(d: dict) -> PolicyParams:
    """dict → PolicyParams (타입 안전)"""
    def flt(k): return float(d.get(k, 0) or 0)
    def s(k):   return str(d.get(k, "") or "")

    return PolicyParams(
        edu_cost_rate=flt("edu_cost_rate"),
        edu_hours=flt("edu_hours"),
        rnd_extra_hours=flt("rnd_extra_hours"),
        online_ratio=flt("online_ratio"),
        completion_rate=flt("completion_rate"),
        ojt_ratio=flt("ojt_ratio"),
        salary_raise=flt("salary_raise"),
        sa_incentive=flt("sa_incentive"),
        a_incentive=flt("a_incentive"),
        promotion_shortcut=flt("promotion_shortcut"),
        welfare_score=flt("welfare_score"),
        market_salary_pct=flt("market_salary_pct"),
        culture_scope=s("culture_scope"),
        mentoring=s("mentoring"),
        idea_system=s("idea_system"),
        eap=s("eap"),
        retro_freq=s("retro_freq"),
        vision_sharing=flt("vision_sharing"),
        remote_days_per_week=flt("remote_days_per_week"),
        overtime_cap_hours=flt("overtime_cap_hours"),
        eval_cycle_months=flt("eval_cycle_months"),
        peer_review_weight=flt("peer_review_weight"),
        internal_posting_ratio=flt("internal_posting_ratio"),
        idp_support_budget=flt("idp_support_budget"),
        leader_coaching_hours=flt("leader_coaching_hours"),
        onboarding_period_days=flt("onboarding_period_days"),
        burnout_check_freq=flt("burnout_check_freq"),
        work_life_balance_budget=flt("work_life_balance_budget"),
        team_building_freq=flt("team_building_freq"),
    )


# ── 데모용 샘플 파라미터 ──────────────────────────────────────
DEMO_PARAMS = PolicyParams(
    edu_cost_rate=30,
    edu_hours=60,
    rnd_extra_hours=20,
    online_ratio=40,
    completion_rate=85,
    ojt_ratio=30,
    salary_raise=5,
    sa_incentive=10,
    a_incentive=5,
    promotion_shortcut=1,
    welfare_score=20,
    market_salary_pct=110,
    culture_scope="전부서",
    mentoring="예",
    idea_system="예",
    eap="예",
    retro_freq="월1",
    vision_sharing=4,
    remote_days_per_week=2,
    overtime_cap_hours=12,
    eval_cycle_months=6,
    peer_review_weight=20,
    internal_posting_ratio=15,
    idp_support_budget=100,
    leader_coaching_hours=40,
    onboarding_period_days=30,
    burnout_check_freq=2,
    work_life_balance_budget=50,
    team_building_freq=4,
)

DEMO_SCENARIO_B = PolicyParams(
    salary_raise=10,
    sa_incentive=20,
    a_incentive=10,
    market_salary_pct=115,
    welfare_score=30,
    promotion_shortcut=2,
    eap="예",
    culture_scope="일부",
    retro_freq="격주",
)
