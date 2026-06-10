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
7. edu_cost_rate > 0인데 edu_hours가 명시되지 않은 경우, 교육비 증액은 교육 시간 확대를 의미하므로 합리적으로 추론할 것:
   - edu_cost_rate 10~20% → edu_hours 20시간
   - edu_cost_rate 21~40% → edu_hours 40시간
   - edu_cost_rate 41~70% → edu_hours 60시간
   - edu_cost_rate 71% 이상 → edu_hours 80시간
8. 멘토링 도입이 언급된 경우 mentoring="예", EAP 도입이 언급된 경우 eap="예", 사내공모/아이디어 시스템이 언급된 경우 idea_system="예"로 설정
9. "전부서 유연근무" 또는 "전사 유연근무" 언급 시 culture_scope="전부서"로 설정
10. [절대금액 → 퍼센트 환산] 연봉 관련 절대금액이 언급된 경우 반드시 퍼센트로 환산하여 salary_raise에 반영:
    - 기준: 회사 평균 연봉 7,000만원/년 (월 583만원)
    - 예시: "월 20만원 인상" → 연 240만원 → 7,000만원의 3.4% → salary_raise=3.4
    - 예시: "연 100만원 인상" → 7,000만원의 1.4% → salary_raise=1.4
    - 예시: "월급 30만원 올려줘" → 연 360만원 → salary_raise=5.1
    - 인상 금액이 명시되지 않고 "인상", "올려줘" 등 방향만 있으면 salary_raise=3 (국내 대기업 평균)
11. [근무시간 → overtime_cap_hours 환산] 연장근무 관련 표현 처리:
    - "근무시간 1시간 연장" → 주 연장근무가 1시간 늘어나는 것이므로 overtime_cap_hours=1
    - "야근 줄여줘", "초과근무 없애줘" → overtime_cap_hours=0
    - overtime_cap_hours는 시뮬레이터 파라미터 중 편익 계산에 직접 반영되지 않는 참고 지표임을 유의
12. [파싱 불가 항목 처리] 30개 파라미터로 명확히 매핑할 수 없는 내용(HR 정책과 무관하거나 수치 변환이 불가능한 요청)은 억지로 끼워 맞추지 말고, parsing_warning에 간략히 기재:
    - 예시: "사무실 의자 교체" → parsing_warning="사무실 의자 교체: 환경 개선 사항으로 HR 파라미터에 미반영"
    - 정상 파싱된 경우 → parsing_warning=""

--- Few-Shot 파싱 예시 (반드시 이 방식을 따를 것) ---

[입력 예시 1]
"전 직원 월급 20만원씩 인상, 근무시간 1시간씩 연장"
[올바른 출력]
{
  "salary_raise": 3.43,
  "overtime_cap_hours": 5,
  "parsing_warning": "",
  (나머지 모든 항목 0 또는 기본값)
}
[계산 근거] 월 20만원 × 12 = 연 240만원. 240 / 7000 × 100 = 3.43%. 1시간/일 × 주5일 = 주5시간.

[입력 예시 2]
"교육비 30% 증액, S고과 10% 인센티브, 멘토링·EAP 도입, 주 2일 재택"
[올바른 출력]
{
  "edu_cost_rate": 30,
  "edu_hours": 40,
  "sa_incentive": 10,
  "mentoring": "예",
  "eap": "예",
  "remote_days_per_week": 2,
  "parsing_warning": "",
  (나머지 모든 항목 0 또는 기본값)
}
[계산 근거] edu_cost_rate=30이고 edu_hours 미언급 → 규칙7: 21~40% → 40시간.

[입력 예시 3]
"사무실 의자 시디즈로 교체, 연봉 5% 인상"
[올바른 출력]
{
  "salary_raise": 5,
  "parsing_warning": "사무실 의자 교체: 물리적 환경 개선으로 HR 파라미터에 미반영",
  (나머지 모든 항목 0 또는 기본값)
}

---

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
  "team_building_freq": 0~12 (팀빌딩 연간 횟수),
  "parsing_warning": "" (매핑 불가 항목 요약, 없으면 빈 문자열)
}"""


def _clean_json(raw: str) -> str:
    """Gemini 응답에서 순수 JSON만 추출"""
    # 1) 마크다운 코드블록 제거
    raw = re.sub(r"```(?:json)?", "", raw)
    raw = re.sub(r"```", "", raw)
    raw = raw.strip()

    # 2) JSON 오브젝트 부분만 추출 (첫 { ~ 마지막 } )
    start = raw.find("{")
    end   = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]

    # 3) 한국어 주석 제거 (// 이후 줄 끝까지)
    raw = re.sub(r"//[^\n]*", "", raw)

    # 4) 줄 끝 trailing comma 제거 (JSON 표준 위반)
    raw = re.sub(r",\s*([}\]])", r"\1", raw)

    # 5) 제어문자 제거 (탭·줄바꿈 제외)
    raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)

    return raw


def parse_policy(policy_text: str, api_key: str) -> tuple:
    """자유 서술 → (PolicyParams, parsing_warning) 튜플 반환"""
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

        cleaned = _clean_json(raw)

        # 1차 시도: 정상 파싱
        try:
            parsed = json.loads(cleaned)
            params = _dict_to_params(parsed)
            warning = str(parsed.get("parsing_warning", "") or "")
            return (params, warning)
        except json.JSONDecodeError:
            pass

        # 2차 시도: 작은따옴표 → 큰따옴표 치환 후 재시도
        try:
            fixed = cleaned.replace("'", '"')
            parsed = json.loads(fixed)
            params = _dict_to_params(parsed)
            warning = str(parsed.get("parsing_warning", "") or "")
            return (params, warning)
        except json.JSONDecodeError:
            pass

        # 3차 시도: 키-값 정규식으로 직접 추출
        extracted = {}
        # 숫자 값
        for m in re.finditer(r'"(\w+)"\s*:\s*(-?[\d.]+)', cleaned):
            extracted[m.group(1)] = float(m.group(2))
        # 문자열 값
        for m in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', cleaned):
            if m.group(1) not in extracted:
                extracted[m.group(1)] = m.group(2)

        if extracted:
            params = _dict_to_params(extracted)
            warning = str(extracted.get("parsing_warning", "") or "")
            return (params, warning)

        raise RuntimeError("JSON 구조를 파악할 수 없습니다")

    except RuntimeError:
        raise
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
