"""
simulator.py — HRD Policy Simulator 수식 엔진 v4
Becker × Kirkpatrick × Herzberg × Meyer&Allen × Lee&Mitchell
30개 파라미터 | 4직군 분해 | 비교 시나리오 | 민감도 분석
"""

import math
from dataclasses import dataclass, field
from typing import Optional

# ─── 이론 계수 (절대 변경 금지) ───────────────────────────────
ALPHA = 0.20        # Becker 인적자본론: 학습 → 역량
BETA  = 0.72        # Herzberg 2요인론: 보상 → 이직방지
GAMMA = 0.58        # Meyer & Allen: 문화 → 몰입
TURNOVER_COST       = 7_000   # 이직비용 1인당 (만원)
KEY_TALENT_MULT     = 2       # 핵심인재 비용 승수
EFFECT_LAG          = 6       # 효과 발현 시차 (개월)

# ─── 조직 기본값 (SK하이닉스 기반 가상 기업) ─────────────────
ORG = dict(
    total        = 400,
    avg_salary   = 7_000,    # 만원
    rnd          = 136,
    production   = 152,
    sales        =  36,
    admin        =  76,
    s_grade      =  28,      # S고과자
    sa_grade     = 132,      # S+A고과자
    base_competency = 0.618,
    base_turnover   = 0.284,
    base_commitment = 0.622,
    annual_turnover = 41,
    avg_age      = 35.4,
    avg_tenure   = 7.4,
)

BASELINE = dict(
    competency  = ORG["base_competency"],
    turnover    = ORG["base_turnover"],
    commitment  = ORG["base_commitment"],
    n_turnover  = ORG["annual_turnover"],
)


@dataclass
class PolicyParams:
    """30개 파라미터 전체 정의 — 엑셀 v5 기준"""
    # 📚 교육·학습
    edu_cost_rate: float = 0        # 교육비 증가율 (%)
    edu_hours: float = 0            # 교육시간 목표 (시간)
    rnd_extra_hours: float = 0      # R&D 추가교육 (시간)
    online_ratio: float = 0         # 온라인 학습 비중 (%)
    completion_rate: float = 0      # 교육 이수율 (%)
    ojt_ratio: float = 0            # OJT 비중 (%)

    # 💰 보상·승진
    salary_raise: float = 0         # 연봉 인상률 (%)
    sa_incentive: float = 0         # S고과 인센티브 (%)
    a_incentive: float = 0          # A고과 인센티브 (%)
    promotion_shortcut: float = 0   # 승진 소요연수 단축 (년)
    welfare_score: float = 0        # 복지포인트 증가율 (%)
    market_salary_pct: float = 0    # 시장 대비 연봉수준 (%)

    # 🌱 조직문화·몰입
    culture_scope: str = ""         # 유연근무제 범위
    mentoring: str = ""             # 멘토링 운영
    idea_system: str = ""           # 사내 공모제
    eap: str = ""                   # EAP 확대
    retro_freq: str = ""            # 팀 회고 주기
    vision_sharing: float = 0       # 비전 공유 횟수 (회/년)

    # 🏠 근무 유연성
    remote_days_per_week: float = 0 # 주당 재택근무 일수
    overtime_cap_hours: float = 0   # 주 연장근무 상한 (시간)

    # 📊 평가·비금전 보상
    eval_cycle_months: float = 0    # 성과평가 주기 (개월)
    peer_review_weight: float = 0   # 다면평가 반영률 (%)

    # 🎯 커리어 개발
    internal_posting_ratio: float = 0  # 사내공모 비율 (%)
    idp_support_budget: float = 0      # IDP 자율지원비 (만원/인)

    # 👑 리더십·조직건강
    leader_coaching_hours: float = 0   # 리더 코칭 연간 시간
    onboarding_period_days: float = 0  # 온보딩 기간 (일)
    burnout_check_freq: float = 0      # 번아웃 진단 연간 횟수
    work_life_balance_budget: float = 0 # 일생활균형 지원금 (만원/인)
    team_building_freq: float = 0      # 팀빌딩 연간 횟수

    # 🔬 이론 계수 (고급)
    alpha: float = ALPHA
    beta: float  = BETA
    gamma: float = GAMMA


def _learning_index(p: PolicyParams) -> float:
    """교육 종합 학습지수 (0~1) — Kirkpatrick 4단계 기반"""
    score = 0.0
    if p.edu_hours > 0:
        score += min(p.edu_hours / 70, 1.0) * 0.25   # 정규화 기준 70h, 가중치 0.25
    if p.edu_cost_rate > 0:
        score += min(p.edu_cost_rate / 100, 1.0) * 0.05  # 교육비 투자 → 학습 인프라 향상
    if p.completion_rate > 0:
        score += min(p.completion_rate / 100, 1.0) * 0.20
    if p.ojt_ratio > 0:
        score += min(p.ojt_ratio / 100, 1.0) * 0.20
    if p.online_ratio > 0:
        score += min(p.online_ratio / 100, 1.0) * 0.10
    if p.rnd_extra_hours > 0:
        score += min(p.rnd_extra_hours / 40, 1.0) * 0.10
    if p.idp_support_budget > 0:
        score += min(p.idp_support_budget / 300, 1.0) * 0.10
    return min(score, 1.0)


def _reward_index(p: PolicyParams) -> float:
    """보상 종합 지수 (0~1) — Herzberg 동기요인 기반"""
    score = 0.0
    if p.salary_raise > 0:
        score += min(p.salary_raise / 20, 1.0) * 0.35
    if p.sa_incentive > 0:
        score += min(p.sa_incentive / 30, 1.0) * 0.20
    if p.a_incentive > 0:
        score += min(p.a_incentive / 20, 1.0) * 0.10
    if p.welfare_score > 0:
        score += min(p.welfare_score / 30, 1.0) * 0.10
    if p.market_salary_pct > 0:
        mkt = (p.market_salary_pct - 100) / 30
        score += max(0, min(mkt, 1.0)) * 0.15
    if p.promotion_shortcut > 0:
        score += min(p.promotion_shortcut / 3, 1.0) * 0.10
    return min(score, 1.0)


def _culture_index(p: PolicyParams) -> float:
    """조직문화 종합 지수 (0~1) — Meyer&Allen 3요소 기반"""
    score = 0.0
    scope_map = {"전부서": 0.20, "일부": 0.10, "미도입": 0.0}
    score += scope_map.get(p.culture_scope, 0.0)
    if p.mentoring.lower() in ("예", "yes", "y", "true"):
        score += 0.15
    if p.idea_system.lower() in ("예", "yes", "y", "true"):
        score += 0.10
    if p.eap.lower() in ("예", "yes", "y", "true"):
        score += 0.10
    freq_map = {"주1": 0.15, "격주": 0.10, "월1": 0.05, "없음": 0.0}
    score += freq_map.get(p.retro_freq, 0.0)
    if p.vision_sharing > 0:
        score += min(p.vision_sharing / 12, 1.0) * 0.05
    if p.remote_days_per_week > 0:
        score += min(p.remote_days_per_week / 5, 1.0) * 0.05
    if p.leader_coaching_hours > 0:
        score += min(p.leader_coaching_hours / 100, 1.0) * 0.05
    if p.team_building_freq > 0:
        score += min(p.team_building_freq / 12, 1.0) * 0.03
    if p.work_life_balance_budget > 0:
        score += min(p.work_life_balance_budget / 300, 1.0) * 0.05
    if p.internal_posting_ratio > 0:
        score += min(p.internal_posting_ratio / 50, 1.0) * 0.05
    return min(score, 1.0)


def simulate(p: PolicyParams) -> dict:
    """핵심 시뮬레이션 — 전사 + 직군별 결과 반환"""
    alpha = p.alpha
    beta  = p.beta
    gamma = p.gamma

    L = _learning_index(p)
    R = _reward_index(p)
    C = _culture_index(p)

    # ── 전사 KPI ─────────────────────────────────────────────
    delta_comp   = alpha * L                        # Becker
    delta_turn   = -beta  * R                       # Herzberg (음수 = 이직 감소)
    delta_commit = gamma  * C                       # Meyer&Allen

    new_comp   = min(BASELINE["competency"]  + delta_comp,   1.0)
    new_turn   = max(BASELINE["turnover"]    + delta_turn,   0.0)
    new_commit = min(BASELINE["commitment"]  + delta_commit, 1.0)

    # 이직자 수 — Sigmoid 임계점 모형 (0.3 = 이직 결정 임계)
    turn_threshold = 0.30
    def sigmoid_turnover(t_prob, n):
        return int(round(n * (1 / (1 + math.exp(-10 * (t_prob - turn_threshold))))))

    new_n_turn = sigmoid_turnover(new_turn, ORG["total"])

    # ── 직군별 분해 ────────────────────────────────────────────
    dept_weights = {
        "R&D":    {"L": 1.30, "R": 0.80, "C": 0.90, "n": ORG["rnd"]},
        "생산":   {"L": 0.80, "R": 1.00, "C": 1.10, "n": ORG["production"]},
        "영업":   {"L": 0.70, "R": 1.30, "C": 0.80, "n": ORG["sales"]},
        "관리/지원": {"L": 0.90, "R": 0.90, "C": 1.20, "n": ORG["admin"]},
    }
    dept_results = {}
    for dept, w in dept_weights.items():
        d_comp   = min(alpha * L * w["L"], 0.30)
        d_turn   = -beta * R * w["R"]
        d_commit = min(gamma * C * w["C"], 0.40)
        dept_results[dept] = {
            "n": w["n"],
            "delta_comp":   round(d_comp,   4),
            "delta_turn":   round(d_turn,   4),
            "delta_commit": round(d_commit, 4),
            "new_comp":     round(min(BASELINE["competency"]  + d_comp,   1.0), 4),
            "new_turn":     round(max(BASELINE["turnover"]    + d_turn,   0.0), 4),
            "new_commit":   round(min(BASELINE["commitment"]  + d_commit, 1.0), 4),
        }

    # ── 비용·편익 ─────────────────────────────────────────────
    n     = ORG["total"]
    tsal  = n * ORG["avg_salary"]   # 총인건비 (만원)

    # 비용
    c_edu     = n * 30 * (p.edu_cost_rate / 100) if p.edu_cost_rate > 0 else 0
    c_idp     = n * p.idp_support_budget
    c_onboard = n * (p.onboarding_period_days / 180) * 20 if p.onboarding_period_days > 0 else 0
    c_burnout = n * p.burnout_check_freq * 3 if p.burnout_check_freq > 0 else 0
    c_eval    = n * (12 / p.eval_cycle_months) * 0.5 if p.eval_cycle_months > 0 else 0
    c_peer    = n * (p.peer_review_weight / 100) * 5 if p.peer_review_weight > 0 else 0
    c_edu_total = c_edu + c_idp + c_onboard + c_burnout + c_eval + c_peer

    c_eap      = n * 20  if p.eap.lower() in ("예","yes","y","true") else 0
    c_mentor   = n * 15  if p.mentoring.lower() in ("예","yes","y","true") else 0
    c_idea     = n * 10  if p.idea_system.lower() in ("예","yes","y","true") else 0
    c_vision   = p.vision_sharing * 500 if p.vision_sharing > 0 else 0
    c_wlb      = n * p.work_life_balance_budget
    c_team     = p.team_building_freq * 1_000 if p.team_building_freq > 0 else 0
    c_coach    = p.leader_coaching_hours * 50 if p.leader_coaching_hours > 0 else 0
    c_remote   = n * p.remote_days_per_week * 2 if p.remote_days_per_week > 0 else 0
    c_internal = n * (p.internal_posting_ratio / 100) * 30 if p.internal_posting_ratio > 0 else 0
    c_culture_total = c_eap + c_mentor + c_idea + c_vision + c_wlb + c_team + c_coach + c_remote + c_internal

    total_cost = c_edu_total + c_culture_total

    # 보상 비용 (참고용, ROI 산식 별도)
    c_salary_ref    = tsal * (p.salary_raise / 100) if p.salary_raise > 0 else 0
    c_incentive_ref = ORG["sa_grade"] * ORG["avg_salary"] * (
        (p.sa_incentive + p.a_incentive) / 200
    ) if (p.sa_incentive + p.a_incentive) > 0 else 0

    # 편익
    turn_reduction   = max(BASELINE["n_turnover"] - new_n_turn, 0)
    b_turnover       = turn_reduction * TURNOVER_COST
    sa_turn_reduced  = turn_reduction * (ORG["sa_grade"] / ORG["total"])
    b_key_talent     = sa_turn_reduced * TURNOVER_COST * KEY_TALENT_MULT
    b_productivity   = tsal * delta_comp * 0.03   # 역량향상 → 생산성 보수적 추정

    total_benefit = b_turnover + b_key_talent + b_productivity
    net_benefit   = total_benefit - total_cost
    roi           = (net_benefit / total_cost * 100) if total_cost > 0 else 0.0

    # ── 승인 등급 ─────────────────────────────────────────────
    def grade(roi_val, dt, dc, dd):
        if roi_val > 0 and dt < 0 and dc > 0 and dd > 0:
            return "S"
        elif roi_val > 0 and (dt < 0 or dc > 0):
            return "A"
        elif roi_val > -10 and (dc > 0 or dd > 0):
            return "B"
        elif roi_val < 0 and dc <= 0 and dd <= 0:
            return "F"
        else:
            return "C"

    approval_grade = grade(roi, delta_turn, delta_comp, delta_commit)

    return {
        "grade":         approval_grade,
        "L": round(L, 4), "R": round(R, 4), "C_idx": round(C, 4),
        # 전사 KPI
        "delta_comp":    round(delta_comp,   4),
        "delta_turn":    round(delta_turn,   4),
        "delta_commit":  round(delta_commit, 4),
        "new_comp":      round(new_comp,     4),
        "new_turn":      round(new_turn,     4),
        "new_commit":    round(new_commit,   4),
        "new_n_turn":    new_n_turn,
        "turn_reduction":turn_reduction,
        # 직군별
        "dept":          dept_results,
        # 비용·편익
        "cost": {
            "edu_total":       round(c_edu_total),
            "culture_total":   round(c_culture_total),
            "total":           round(total_cost),
            "salary_ref":      round(c_salary_ref),
            "incentive_ref":   round(c_incentive_ref),
            "breakdown": {
                "교육비 증가":  round(c_edu),
                "IDP 지원비":   round(c_idp),
                "온보딩":       round(c_onboard),
                "번아웃진단":   round(c_burnout),
                "EAP":          round(c_eap),
                "멘토링":       round(c_mentor),
                "사내공모":     round(c_idea),
                "비전공유":     round(c_vision),
                "일생활균형":   round(c_wlb),
                "팀빌딩":       round(c_team),
                "리더코칭":     round(c_coach),
                "재택인프라":   round(c_remote),
            }
        },
        "benefit": {
            "turnover_saving": round(b_turnover),
            "key_talent":      round(b_key_talent),
            "productivity":    round(b_productivity),
            "total":           round(total_benefit),
        },
        "net_benefit": round(net_benefit),
        "roi":         round(roi, 1),
    }


def sensitivity_analysis(p: PolicyParams) -> dict:
    """
    민감도 분석 — α/β/γ ±10%·±20% 변화 시 결과
    반환: { "alpha": [...], "beta": [...], "gamma": [...] }
    """
    import copy
    results = {"alpha": [], "beta": [], "gamma": []}
    steps = [-0.20, -0.10, 0.0, +0.10, +0.20]

    for coef, attr in [("alpha", "alpha"), ("beta", "beta"), ("gamma", "gamma")]:
        base_val = getattr(p, attr)
        base_res = simulate(p)

        for step in steps:
            pp = copy.deepcopy(p)
            setattr(pp, attr, round(base_val * (1 + step), 4))
            res = simulate(pp)

            if coef == "alpha":
                delta_val  = res["delta_comp"]
                base_delta = base_res["delta_comp"]
                label = "역량 Δ"
            elif coef == "beta":
                delta_val  = res["delta_turn"]
                base_delta = base_res["delta_turn"]
                label = "이직의향 Δ"
            else:
                delta_val  = res["delta_commit"]
                base_delta = base_res["delta_commit"]
                label = "몰입도 Δ"

            diff = round(delta_val - base_delta, 4) if step != 0 else None
            pct  = round(step * 100)

            if step == 0:
                robust = "기준"
            elif roi_direction_stable(res, base_res):
                robust = "✅ 강건"
            else:
                robust = "⚠️ 방향 변화"

            results[coef].append({
                "step_label": f"{'+' if pct > 0 else ''}{pct}%" if pct != 0 else "기준",
                "coef_val":   round(getattr(pp, attr), 4),
                "delta":      round(delta_val, 4),
                "diff":       diff,
                "roi":        res["roi"],
                "robust":     robust,
                "label":      label,
            })
    return results


def roi_direction_stable(res: dict, base_res: dict) -> bool:
    """ROI 방향이 기준값과 동일한지 확인"""
    return (res["roi"] >= 0) == (base_res["roi"] >= 0)


def compare_scenarios(p_a: PolicyParams, p_b: PolicyParams) -> dict:
    """A안 vs B안 비교"""
    ra = simulate(p_a)
    rb = simulate(p_b)

    def winner(val_a, val_b, higher_is_better=True):
        if higher_is_better:
            if val_a > val_b + 0.001: return "A안 우세"
            elif val_b > val_a + 0.001: return "B안 우세"
        else:
            if val_a < val_b - 0.001: return "A안 우세"
            elif val_b < val_a - 0.001: return "B안 우세"
        return "동일"

    rows = [
        {"지표": "역량 향상 Δ",   "A": ra["delta_comp"],    "B": rb["delta_comp"],    "방향": "↑ 클수록 좋음", "승자": winner(ra["delta_comp"],    rb["delta_comp"])},
        {"지표": "이직의향 Δ",    "A": ra["delta_turn"],    "B": rb["delta_turn"],    "방향": "↓ 작을수록 좋음","승자": winner(ra["delta_turn"],    rb["delta_turn"], False)},
        {"지표": "예상 이직자",   "A": ra["new_n_turn"],    "B": rb["new_n_turn"],    "방향": "↓ 작을수록 좋음","승자": winner(ra["new_n_turn"],    rb["new_n_turn"], False)},
        {"지표": "몰입도 향상 Δ", "A": ra["delta_commit"],  "B": rb["delta_commit"],  "방향": "↑ 클수록 좋음", "승자": winner(ra["delta_commit"],  rb["delta_commit"])},
        {"지표": "총 비용 (만원)","A": ra["cost"]["total"], "B": rb["cost"]["total"], "방향": "↓ 작을수록 좋음","승자": winner(ra["cost"]["total"], rb["cost"]["total"], False)},
        {"지표": "총 편익 (만원)","A": ra["benefit"]["total"],"B": rb["benefit"]["total"],"방향": "↑ 클수록 좋음","승자": winner(ra["benefit"]["total"],rb["benefit"]["total"])},
        {"지표": "순편익 (만원)", "A": ra["net_benefit"],   "B": rb["net_benefit"],   "방향": "↑ 클수록 좋음", "승자": winner(ra["net_benefit"],   rb["net_benefit"])},
        {"지표": "ROI (%)",       "A": ra["roi"],           "B": rb["roi"],           "방향": "↑ 클수록 좋음", "승자": winner(ra["roi"],           rb["roi"])},
    ]

    a_wins = sum(1 for r in rows if r["승자"] == "A안 우세")
    b_wins = sum(1 for r in rows if r["승자"] == "B안 우세")
    if a_wins > b_wins:
        overall = "🏆 A안 종합 우세"
    elif b_wins > a_wins:
        overall = "🏆 B안 종합 우세"
    else:
        overall = "⚖️ 동등"

    return {"rows": rows, "overall": overall, "result_a": ra, "result_b": rb}


def check_feasibility(p: PolicyParams) -> list:
    """
    현실 제약 검증 — 비현실적 파라미터 조합 감지 (방법 1)
    수식은 변경하지 않고, 경고/오류 메시지만 반환
    반환: [{"level": "error"|"warning", "param": str, "msg": str}, ...]
    """
    issues = []

    if p.salary_raise > 15:
        issues.append({"level": "error", "param": "연봉 인상률",
            "msg": f"연봉 인상 {p.salary_raise:.0f}%는 비현실적입니다. "
                   f"국내 대기업 평균 3~5%, 최대 10% 수준입니다. "
                   f"실제 인건비 증가(연 {int(400*7000*p.salary_raise/100):,}만원)가 편익을 크게 초과할 수 있습니다."})
    elif p.salary_raise > 10:
        issues.append({"level": "warning", "param": "연봉 인상률",
            "msg": f"연봉 인상 {p.salary_raise:.0f}%는 높은 수준입니다 (대기업 기준 통상 5~8%)."})

    if p.remote_days_per_week >= 5:
        issues.append({"level": "error", "param": "재택근무 일수",
            "msg": "전면 재택(주 5일)은 생산직·영업직(전체 47%)에 적용 불가능합니다. "
                   "Google·Apple 등 빅테크도 하이브리드로 회귀 중이며, 현실적 상한은 주 2~3일입니다."})
    elif p.remote_days_per_week >= 4:
        issues.append({"level": "warning", "param": "재택근무 일수",
            "msg": f"주 {p.remote_days_per_week:.0f}일 재택은 생산직(전체 38%, 152명) 적용이 어렵습니다."})

    if p.sa_incentive > 30:
        issues.append({"level": "error", "param": "S고과 인센티브",
            "msg": f"S인센티브 {p.sa_incentive:.0f}%는 비현실적입니다 (대기업 통상 상한 15~20%)."})
    elif p.sa_incentive > 20:
        issues.append({"level": "warning", "param": "S고과 인센티브",
            "msg": f"S인센티브 {p.sa_incentive:.0f}%는 내부 형평성 이슈가 발생할 수 있습니다."})

    if p.edu_cost_rate > 100:
        issues.append({"level": "error", "param": "교육비 증가율",
            "msg": f"교육비 {p.edu_cost_rate:.0f}% 증가는 예산 2배 이상입니다. 현실적 상한은 30~50%입니다."})

    if p.welfare_score > 40:
        issues.append({"level": "warning", "param": "복지포인트",
            "msg": f"복지포인트 {p.welfare_score:.0f}% 증가는 예산 부담이 큽니다 (권장: 10~20%)."})

    if p.salary_raise > 8 and p.sa_incentive > 15:
        issues.append({"level": "warning", "param": "복합(보상 과부하)",
            "msg": f"연봉 {p.salary_raise:.0f}% + 인센티브 {p.sa_incentive:.0f}% 동시 적용 시 "
                   f"실제 인건비 부담이 매우 큽니다."})

    if p.remote_days_per_week >= 3:
        issues.append({"level": "warning", "param": "복합(재택+생산직)",
            "msg": f"생산직 152명(38%)은 재택 적용 불가. "
                   f"실질 적용 인원은 248명으로 효과가 축소됩니다."})

    return issues


def build_interpretation(res: dict, params: PolicyParams) -> dict:
    """
    실무 해석 가이드 — A안 핵심
    각 KPI에 대한 경영적 해석 + 인사팀 주목 포인트 자동 생성
    """
    interp = {}

    # 역량
    dc = res["delta_comp"]
    if dc > 0.05:
        interp["competency"] = f"역량이 {dc:.1%} 향상됩니다. Becker 인적자본론에 따르면 이는 교육 투자의 효율적 전환을 의미합니다. 인사팀 포인트: R&D 직군에서 효과가 가장 크게 나타납니다."
    elif dc > 0.01:
        interp["competency"] = f"역량이 소폭({dc:.1%}) 향상됩니다. 교육 시간·이수율 강화 시 더 큰 효과를 기대할 수 있습니다."
    else:
        interp["competency"] = "교육 관련 파라미터(교육시간, 이수율, OJT 비중)를 높이면 역량 향상 효과가 나타납니다."

    # 이직
    dt = res["delta_turn"]
    red = res["turn_reduction"]
    if dt < -0.05:
        interp["turnover"] = f"이직의향이 {abs(dt):.1%} 감소하여 연간 약 {red}명의 이탈을 막을 수 있습니다. Herzberg 이론 기준으로 보상 요인이 충분히 작동하는 수준입니다."
    elif dt < -0.01:
        interp["turnover"] = f"이직의향이 소폭({abs(dt):.1%}) 감소합니다. 연봉 인상·인센티브 강화 시 이직 억제 효과가 더 커집니다."
    else:
        interp["turnover"] = "보상 파라미터(연봉 인상률, 인센티브, 시장 대비 연봉수준)를 높이면 이직 억제 효과가 나타납니다."

    # 몰입
    dd = res["delta_commit"]
    if dd > 0.05:
        interp["commitment"] = f"몰입도가 {dd:.1%} 향상됩니다. Meyer & Allen 3요소 모형에서 정서적 몰입이 강화된 것으로, 장기 성과와 직결됩니다."
    elif dd > 0.01:
        interp["commitment"] = f"몰입도가 소폭({dd:.1%}) 향상됩니다. 유연근무·멘토링·팀 회고 도입 시 추가 효과를 기대할 수 있습니다."
    else:
        interp["commitment"] = "조직문화 파라미터(유연근무, EAP, 팀 회고, 비전 공유)를 활성화하면 몰입도 향상 효과가 나타납니다."

    # ROI
    roi = res["roi"]
    nb  = res["net_benefit"]
    if roi > 50:
        interp["roi"] = f"ROI {roi:.1f}% — 투자 대비 매우 우수한 수익성. 1억 투자 시 약 {1+roi/100:.1f}억 효과를 기대할 수 있습니다. 인사팀 설득 근거로 강력합니다."
    elif roi > 0:
        interp["roi"] = f"ROI {roi:.1f}% — 순편익 {nb:,}만원으로 투자 가치가 있습니다. 비용 효율화 시 추가 개선 여지가 있습니다."
    elif roi > -20:
        interp["roi"] = f"ROI {roi:.1f}% — 소폭 마이너스이지만, 역량·몰입의 장기적 무형 가치를 감안하면 충분히 검토할 수 있는 수준입니다."
    else:
        interp["roi"] = f"ROI {roi:.1f}% — 비용 대비 편익이 부족합니다. 비용 항목을 줄이거나 고효율 정책에 집중하세요."

    # 승인 등급 해석
    grade = res["grade"]
    grade_msg = {
        "S": "S등급 — 역량·이직·몰입·ROI 모두 개선. 인사팀 즉시 승인 가능한 정책입니다.",
        "A": "A등급 — ROI 양수 + 핵심 지표 개선. 소규모 조정 후 승인을 기대할 수 있습니다.",
        "B": "B등급 — 역량·몰입은 개선되나 비용 효율 개선이 필요합니다.",
        "C": "C등급 — 일부 지표만 개선. 정책 범위를 좁혀 집중도를 높이세요.",
        "F": "F등급 — 비용 과다, 효과 미미. 전면 재검토가 필요합니다.",
    }
    interp["grade"] = grade_msg.get(grade, "")

    return interp
