"""
app.py — HRD Policy Simulator Streamlit v4
건물 이미지 대형 | 글자 대형 | A안(실무해석) + C안(제안서) | 비교 시나리오 | 직군별 분해 | 민감도 분석 | PDF 다운로드
"""

import base64, os, time
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from simulator import (
    PolicyParams, simulate, sensitivity_analysis,
    compare_scenarios, build_interpretation, BASELINE, ORG
)
from gemini_parser import parse_policy, DEMO_PARAMS, DEMO_SCENARIO_B

# ──────────────────────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HRD Policy Simulator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────────────────────────
# 전역 CSS
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 기본 배경 */
.stApp { background: #090B10; color: #E0E6F0; }
[data-testid="stSidebar"] { background: #0D1B2A; }
.main .block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }

/* 헤더 */
.hrd-header { text-align:center; padding: 1.5rem 0 0.5rem; }
.hrd-super  { font-size:0.9rem; letter-spacing:0.25em; color:#00E5FF;
              text-transform:uppercase; margin-bottom:0.3rem; }
.hrd-title  { font-size:3.4rem; font-weight:800; color:#FFFFFF;
              line-height:1.05; margin:0.1rem 0; }
.hrd-sub    { font-size:1.05rem; color:#607D8B; margin-top:0.4rem; }

/* 건물 이미지 컨테이너 */
.building-wrap {
  text-align:center;
  padding: 1rem 0;
  animation: glow-pulse 3s ease-in-out infinite;
}
.building-wrap img {
  width: 90%;
  max-width: 600px;
  filter: drop-shadow(0 0 40px #00E5FF88) drop-shadow(0 0 80px #00E5FF44);
}
.building-caption {
  font-size:0.7rem; letter-spacing:0.3em; color:#00E5FF55;
  text-transform:uppercase; margin-top:0.5rem;
}
@keyframes glow-pulse {
  0%,100% { filter: drop-shadow(0 0 20px #00E5FF66); }
  50%      { filter: drop-shadow(0 0 50px #00E5FFAA); }
}

/* 유리 카드 */
.glass-card {
  background: rgba(13,27,42,0.85);
  border: 1px solid rgba(0,229,255,0.18);
  border-radius: 14px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  backdrop-filter: blur(8px);
}

/* KPI 카드 */
.kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin:1rem 0; }
.kpi-card {
  background: rgba(0,229,255,0.06);
  border: 1px solid rgba(0,229,255,0.2);
  border-radius: 12px;
  padding: 1.2rem;
  text-align: center;
}
.kpi-label { font-size:0.8rem; color:#607D8B; letter-spacing:0.08em; margin-bottom:0.4rem; }
.kpi-value { font-size:2.4rem; font-weight:700; line-height:1; }
.kpi-delta { font-size:0.85rem; margin-top:0.3rem; }
.kpi-theory{ font-size:0.7rem; color:#455A64; margin-top:0.3rem; }

/* 등급 배지 */
.grade-S { color:#00E5FF; }
.grade-A { color:#00C853; }
.grade-B { color:#FFB300; }
.grade-C { color:#FF7043; }
.grade-F { color:#FF5252; }
.grade-q { color:#607D8B; }
.grade-badge {
  font-size: 5rem; font-weight:900; line-height:1;
  text-align:center; padding: 0.5rem;
}
.grade-label { font-size:1rem; text-align:center; color:#B0BEC5; }

/* 실무 해석 박스 */
.interp-box {
  background: rgba(0,229,255,0.05);
  border-left: 3px solid #00E5FF;
  border-radius: 0 8px 8px 0;
  padding: 0.8rem 1rem;
  margin: 0.5rem 0;
  font-size: 0.95rem;
  line-height: 1.7;
  color: #CFD8DC;
}
.interp-title { font-size:0.75rem; color:#00E5FF; letter-spacing:0.1em; margin-bottom:0.3rem; }

/* 탭 */
.stTabs [data-baseweb="tab"] {
  font-size:1rem !important; color:#607D8B !important; padding:0.6rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
  color:#00E5FF !important; border-bottom:2px solid #00E5FF !important;
}

/* 버튼 */
.stButton > button {
  background: rgba(0,229,255,0.12) !important;
  border: 1px solid rgba(0,229,255,0.4) !important;
  color: #00E5FF !important;
  border-radius: 8px !important;
  font-size: 1rem !important;
  padding: 0.5rem 1.5rem !important;
  transition: all 0.2s;
}
.stButton > button:hover {
  background: rgba(0,229,255,0.25) !important;
  border-color: #00E5FF !important;
}

/* 입력창 */
.stTextArea textarea, .stTextInput input {
  background: rgba(0,20,40,0.8) !important;
  border: 1px solid rgba(0,229,255,0.25) !important;
  color: #E0E6F0 !important;
  border-radius: 8px !important;
  font-size: 1rem !important;
}

/* 섹션 제목 */
.sec-title {
  font-size: 1.3rem; font-weight: 700; color: #00E5FF;
  border-bottom: 1px solid rgba(0,229,255,0.2);
  padding-bottom: 0.4rem; margin: 1.2rem 0 0.8rem;
}
.sec-sub { font-size:0.85rem; color:#455A64; margin-top:-0.5rem; margin-bottom:0.8rem; }

/* 비교 테이블 */
.cmp-table { width:100%; border-collapse:collapse; font-size:0.9rem; }
.cmp-table th { background:#0D1B2A; color:#00E5FF; padding:8px 12px; font-size:0.85rem; }
.cmp-table td { padding:7px 12px; border-bottom:1px solid rgba(255,255,255,0.05); }
.cmp-table tr:hover td { background:rgba(0,229,255,0.04); }
.win-a { color:#00E5FF; font-weight:700; }
.win-b { color:#00C853; font-weight:700; }
.win-tie{ color:#607D8B; }

/* Streamlit 기본 요소 색상 재정의 */
div[data-testid="metric-container"] { background: rgba(0,229,255,0.06); border-radius:10px; padding:1rem; }
div[data-testid="stSelectbox"] select { background:#0D1B2A !important; color:#E0E6F0 !important; }
label { color: #B0BEC5 !important; font-size: 0.95rem !important; }
.stSlider .st-aw { background: rgba(0,229,255,0.3) !important; }
.stSlider .st-ar { background: #00E5FF !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# 유틸 함수
# ──────────────────────────────────────────────────────────────────
def get_building_b64() -> str | None:
    candidates = [
        os.path.join(os.getcwd(), "건물_디자인.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "건물_디자인.png"),
        "건물_디자인.png",
        os.path.join(os.getcwd(), "건물 디자인.png"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            with open(c, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None


def delta_color(val: float, positive_good: bool = True) -> str:
    if val == 0: return "#607D8B"
    if positive_good:
        return "#00C853" if val > 0 else "#FF5252"
    else:
        return "#00C853" if val < 0 else "#FF5252"


def fmt_delta(val: float, pct: bool = True) -> str:
    if val == 0: return "변화 없음"
    sign = "+" if val > 0 else ""
    if pct:
        return f"{sign}{val:.2%}"
    return f"{sign}{val:.3f}"


def grade_color_class(g: str) -> str:
    return {"S": "grade-S", "A": "grade-A", "B": "grade-B",
            "C": "grade-C", "F": "grade-F"}.get(g, "grade-q")


# ──────────────────────────────────────────────────────────────────
# 세션 초기화
# ──────────────────────────────────────────────────────────────────
for k, v in {
    "result": None, "params": None, "interp": None,
    "sensitivity": None, "policy_text": "",
    "result_b": None, "params_b": None,
    "scenario_cmp": None,
    "proposal_text": None,
    "show_results": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ──────────────────────────────────────────────────────────────────
# 헤더
# ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hrd-header">
  <div class="hrd-super">Organization Digital Twin</div>
  <div class="hrd-title">HRD Policy Simulator</div>
  <div class="hrd-sub">Becker(1964) 인적자본론 &times; Herzberg(1968) 2요인론 &times; Meyer &amp; Allen(1991) 몰입 모형</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ──────────────────────────────────────────────────────────────────
# 상단 레이아웃: 건물(좌) + 입력(우)
# ──────────────────────────────────────────────────────────────────
col_img, col_input = st.columns([4, 5], gap="large")

with col_img:
    b64 = get_building_b64()
    if b64:
        st.markdown(f"""
        <div class="building-wrap">
          <img src="data:image/png;base64,{b64}" alt="Organization Digital Twin">
          <div class="building-caption">Virtual Human Capital Model</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center; padding:4rem; color:#1E3A5F;">
          <div style="font-size:6rem;">🏢</div>
          <div style="font-size:0.8rem; letter-spacing:0.3em; color:#00E5FF55; margin-top:1rem;">
            VIRTUAL HUMAN CAPITAL MODEL<br>
            <span style="font-size:0.65rem;">(건물_디자인.png를 같은 폴더에 넣어주세요)</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

with col_input:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">⚙️ HR 정책 입력</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">정책을 자유롭게 서술하세요 — AI가 30개 파라미터로 자동 수치화합니다</div>', unsafe_allow_html=True)

    policy_input = st.text_area(
        label="HR 정책 서술",
        value=st.session_state.policy_text,
        height=160,
        placeholder="예시: 전 직원 주 2회 재택근무 도입, 교육비 30% 증액, S고과자 인센티브 15% 추가 지급, 분기별 팀 회고 운영, 리더 코칭 프로그램 연 40시간...",
        label_visibility="collapsed",
    )

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza... (데모 실행 시 생략 가능)",
        label_visibility="collapsed",
    )

    btn_col1, btn_col2, btn_col3 = st.columns(3)
    with btn_col1:
        run_btn  = st.button("▶ 분석 시작", use_container_width=True)
    with btn_col2:
        demo_btn = st.button("💡 데모 실행", use_container_width=True)
    with btn_col3:
        reset_btn= st.button("↺ 초기화", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # 조직 현황 미니 요약
    st.markdown("""
    <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:0.5rem; margin-top:0.5rem;">
      <div style="background:rgba(0,229,255,0.05); border:1px solid rgba(0,229,255,0.15);
                  border-radius:8px; padding:0.7rem; text-align:center;">
        <div style="font-size:1.5rem; font-weight:700; color:#00E5FF;">400</div>
        <div style="font-size:0.72rem; color:#607D8B;">임직원 수</div>
      </div>
      <div style="background:rgba(0,229,255,0.05); border:1px solid rgba(0,229,255,0.15);
                  border-radius:8px; padding:0.7rem; text-align:center;">
        <div style="font-size:1.5rem; font-weight:700; color:#00E5FF;">41명</div>
        <div style="font-size:0.72rem; color:#607D8B;">연간 이직자 (현재)</div>
      </div>
      <div style="background:rgba(0,229,255,0.05); border:1px solid rgba(0,229,255,0.15);
                  border-radius:8px; padding:0.7rem; text-align:center;">
        <div style="font-size:1.5rem; font-weight:700; color:#00E5FF;">0.618</div>
        <div style="font-size:0.72rem; color:#607D8B;">평균 역량 (Baseline)</div>
      </div>
      <div style="background:rgba(0,229,255,0.05); border:1px solid rgba(0,229,255,0.15);
                  border-radius:8px; padding:0.7rem; text-align:center;">
        <div style="font-size:1.5rem; font-weight:700; color:#00E5FF;">0.622</div>
        <div style="font-size:0.72rem; color:#607D8B;">평균 몰입도 (Baseline)</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# 버튼 동작
# ──────────────────────────────────────────────────────────────────
if reset_btn:
    bar = st.progress(0, "초기화 중...")
    for i in range(0, 101, 20):
        time.sleep(0.05); bar.progress(i)
    for k in ["result","params","interp","sensitivity","policy_text",
              "result_b","params_b","scenario_cmp","proposal_text","show_results"]:
        st.session_state[k] = None if k != "policy_text" else ""
    st.session_state.show_results = False
    bar.empty()
    st.success("✅ 초기화 완료")
    st.rerun()

if demo_btn:
    bar = st.progress(0, "데모 실행 중...")
    st.session_state.params      = DEMO_PARAMS
    st.session_state.policy_text = "【데모】교육비 30% 증액, 연봉 5% 인상, S고과 10% 인센티브, 전부서 유연근무, 멘토링·EAP·사내공모 도입, 월 1회 팀 회고, 비전 공유 연 4회, 주 2일 재택근무"
    bar.progress(30, "파라미터 로딩...")
    res  = simulate(DEMO_PARAMS)
    bar.progress(60, "분석 중...")
    interp = build_interpretation(res, DEMO_PARAMS)
    sens   = sensitivity_analysis(DEMO_PARAMS)
    cmp    = compare_scenarios(DEMO_PARAMS, DEMO_SCENARIO_B)
    bar.progress(90, "결과 정리...")
    st.session_state.result       = res
    st.session_state.interp       = interp
    st.session_state.sensitivity  = sens
    st.session_state.scenario_cmp = cmp
    st.session_state.params_b     = DEMO_SCENARIO_B
    st.session_state.show_results = True
    bar.progress(100); bar.empty()
    st.success("✅ 데모 완료! 아래에서 결과를 확인하세요")
    st.rerun()

if run_btn:
    if not policy_input.strip():
        st.warning("정책을 입력하세요.")
    elif not api_key.strip():
        st.warning("Gemini API Key를 입력하세요. (없으면 💡 데모 실행을 사용하세요)")
    else:
        bar = st.progress(0, "AI 분석 중...")
        try:
            bar.progress(15, "Gemini가 정책을 읽는 중...")
            params = parse_policy(policy_input, api_key)
            st.session_state.params      = params
            st.session_state.policy_text = policy_input

            bar.progress(45, "수식 엔진 계산 중...")
            res = simulate(params)

            bar.progress(65, "실무 해석 생성 중...")
            interp = build_interpretation(res, params)

            bar.progress(80, "민감도 분석 중...")
            sens = sensitivity_analysis(params)

            st.session_state.result      = res
            st.session_state.interp      = interp
            st.session_state.sensitivity = sens
            st.session_state.show_results= True
            bar.progress(100); bar.empty()
            st.success("✅ 분석 완료!")
            st.rerun()
        except Exception as e:
            bar.empty()
            st.error(f"오류: {e}")


# ──────────────────────────────────────────────────────────────────
# 결과 영역
# ──────────────────────────────────────────────────────────────────
if st.session_state.show_results and st.session_state.result:
    res    = st.session_state.result
    params = st.session_state.params
    interp = st.session_state.interp or {}
    sens   = st.session_state.sensitivity
    cmp    = st.session_state.scenario_cmp

    st.divider()

    # ── 등급 + KPI 카드 ───────────────────────────────────────
    grade = res["grade"]
    grade_labels = {"S":"최우수","A":"우수","B":"양호","C":"보통","F":"재검토","?":"대기"}
    grade_descs  = {
        "S": "ROI 양수 + 이직 감소 + 몰입 향상 + 역량 향상",
        "A": "ROI 양수 + 핵심 지표 개선",
        "B": "역량·몰입 개선, 비용 효율 검토 필요",
        "C": "일부 지표 개선, 집중도 강화 필요",
        "F": "비용 과다·효과 미미, 전면 재검토",
    }
    g_class = grade_color_class(grade)

    gcol, kpi1, kpi2, kpi3, kpi4 = st.columns([1.5, 2, 2, 2, 2])

    with gcol:
        st.markdown(f"""
        <div style="text-align:center; padding:0.5rem;">
          <div style="font-size:0.8rem; color:#607D8B; letter-spacing:0.1em;">인사팀 승인 등급</div>
          <div class="grade-badge {g_class}">{grade}</div>
          <div class="grade-label">{grade_labels.get(grade,'')}</div>
          <div style="font-size:0.72rem; color:#455A64; margin-top:0.3rem;">{grade_descs.get(grade,'')}</div>
        </div>
        """, unsafe_allow_html=True)

    for col, (label, val, delta, theory, pos_good) in zip(
        [kpi1, kpi2, kpi3, kpi4],
        [
            ("📚 역량 향상",
             f"{res['new_comp']:.3f}",
             f"Δ {fmt_delta(res['delta_comp'])}",
             "Becker × Kirkpatrick",
             True),
            ("🔒 이직의향",
             f"{res['new_turn']:.3f}",
             f"이직자 {res['new_n_turn']}명 (Δ {res['turn_reduction']:+}명)",
             "Herzberg × Lee&Mitchell",
             False),
            ("💚 몰입도",
             f"{res['new_commit']:.3f}",
             f"Δ {fmt_delta(res['delta_commit'])}",
             "Meyer & Allen 3요소",
             True),
            ("💰 NET ROI",
             f"{res['roi']:.1f}%",
             f"순편익 {res['net_benefit']:+,}만원",
             "HR ROI 모델",
             True),
        ]
    ):
        dc = res['delta_comp'] if "역량" in label else \
             res['delta_turn'] if "이직" in label else \
             res['delta_commit'] if "몰입" in label else res['roi']
        vcolor = delta_color(dc, pos_good)
        with col:
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value" style="color:{vcolor};">{val}</div>
              <div class="kpi-delta" style="color:{vcolor};">{delta}</div>
              <div class="kpi-theory">{theory}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── 탭 구성 ──────────────────────────────────────────────
    tab_names = [
        "📊 비교 차트",
        "💡 실무 해석",
        "👥 직군별 분해",
        "💵 비용·편익",
        "📉 조건 변경 (What-if)",
        "🔀 A안 vs B안",
        "📖 이론 근거",
        "📝 인사팀 제안서",
        "📥 PDF 리포트",
    ]
    tabs = st.tabs(tab_names)

    # ────────────────────────────────────────────────────────
    # TAB 0: 비교 차트
    # ────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="sec-title">📊 Baseline vs 정책 적용 후 비교</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            # 막대 비교 차트
            labels  = ["평균 역량", "이직의향", "평균 몰입도"]
            base_v  = [BASELINE["competency"], BASELINE["turnover"], BASELINE["commitment"]]
            after_v = [res["new_comp"], res["new_turn"], res["new_commit"]]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Baseline (현재)", x=labels, y=base_v,
                marker_color="rgba(96,125,139,0.6)",
                marker_line_color="rgba(96,125,139,0.9)", marker_line_width=1,
                text=[f"{v:.3f}" for v in base_v], textposition="outside",
                textfont=dict(size=13, color="#B0BEC5"),
            ))
            fig.add_trace(go.Bar(
                name="정책 적용 후", x=labels, y=after_v,
                marker_color="rgba(0,229,255,0.6)",
                marker_line_color="#00E5FF", marker_line_width=1,
                text=[f"{v:.3f}" for v in after_v], textposition="outside",
                textfont=dict(size=13, color="#00E5FF"),
            ))
            fig.update_layout(
                barmode="group", template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(size=13, color="#B0BEC5"),
                legend=dict(orientation="h", y=1.1, font=dict(size=12)),
                margin=dict(t=30, b=30, l=10, r=10),
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            # 레이더 차트
            cats = ["역량", "이직 억제\n(낮을수록↑)", "몰입도", "ROI 효율", "비용 효율"]
            roi_norm   = min(max((res["roi"] + 50) / 150, 0), 1)
            cost_eff   = 1 - min(res["cost"]["total"] / 200_000, 1) if res["cost"]["total"] > 0 else 0.5
            base_radar = [BASELINE["competency"], 1 - BASELINE["turnover"],
                          BASELINE["commitment"], 0.33, 0.5]
            after_radar= [res["new_comp"], 1 - res["new_turn"],
                          res["new_commit"], roi_norm, cost_eff]

            fig2 = go.Figure()
            fig2.add_trace(go.Scatterpolar(
                r=base_radar + [base_radar[0]], theta=cats + [cats[0]],
                name="Baseline", fill="toself",
                fillcolor="rgba(96,125,139,0.2)", line=dict(color="#607D8B", width=2),
            ))
            fig2.add_trace(go.Scatterpolar(
                r=after_radar + [after_radar[0]], theta=cats + [cats[0]],
                name="정책 후", fill="toself",
                fillcolor="rgba(0,229,255,0.15)", line=dict(color="#00E5FF", width=2),
            ))
            fig2.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0,1], gridcolor="#1E3A5F", color="#455A64"),
                    angularaxis=dict(gridcolor="#1E3A5F", tickfont=dict(size=11, color="#B0BEC5")),
                    bgcolor="rgba(0,0,0,0)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(font=dict(size=12)),
                margin=dict(t=30, b=30), height=320,
            )
            st.plotly_chart(fig2, use_container_width=True)

        # 이직자 수 변화
        st.markdown('<div class="sec-title">👥 예상 이직자 수 변화</div>', unsafe_allow_html=True)
        fig3 = go.Figure()
        x_vals = ["Baseline (현재)", "정책 적용 후"]
        y_vals = [BASELINE["n_turnover"], res["new_n_turn"]]
        colors_ = ["#607D8B", "#00C853" if res["new_n_turn"] < BASELINE["n_turnover"] else "#FF5252"]
        fig3.add_trace(go.Bar(
            x=x_vals, y=y_vals, marker_color=colors_,
            text=[f"{v}명" for v in y_vals], textposition="outside",
            textfont=dict(size=16, color="#E0E6F0"),
            width=0.4,
        ))
        if res["turn_reduction"] > 0:
            fig3.add_annotation(
                x=1, y=res["new_n_turn"],
                text=f"↓ {res['turn_reduction']}명 감소<br>(이직비용 {res['benefit']['turnover_saving']:,}만원 절감)",
                showarrow=True, arrowhead=2, arrowcolor="#00E5FF",
                font=dict(size=13, color="#00E5FF"),
                ay=-40,
            )
        fig3.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(title="연간 이직자 수 (명)", gridcolor="#1E3A5F"),
            font=dict(size=13), margin=dict(t=20, b=20), height=260,
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ────────────────────────────────────────────────────────
    # TAB 1: 실무 해석 (A안)
    # ────────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="sec-title">💡 실무 해석 가이드</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">각 지표가 의미하는 것 + 인사팀이 주목할 포인트</div>', unsafe_allow_html=True)

        sections = [
            ("📚 역량 향상", "competency", "Becker 인적자본론에서 교육 투자 → 인적자본 축적 → 생산성 향상으로 이어지는 연결고리"),
            ("🔒 이직 억제", "turnover",   "Herzberg 2요인론에서 위생요인(급여)은 불만 방지, 동기요인(성장)은 적극 유지 효과"),
            ("💚 몰입도",    "commitment", "Meyer & Allen 정서적 몰입 — 직원이 '머물고 싶어서' 있는 상태. 장기 성과와 직결"),
            ("💰 투자 효과", "roi",        "이직비용 절감 + 핵심인재 잔류 + 생산성 향상의 합산. 비용 대비 편익 비율"),
        ]
        for title, key, theory in sections:
            msg = interp.get(key, "파라미터를 높이면 효과를 확인할 수 있습니다.")
            st.markdown(f"""
            <div class="interp-box">
              <div class="interp-title">{title}</div>
              <div style="font-size:0.9rem; margin-bottom:0.4rem;">{msg}</div>
              <div style="font-size:0.78rem; color:#455A64; margin-top:0.3rem;">📖 이론 근거: {theory}</div>
            </div>
            """, unsafe_allow_html=True)

        # 파라미터 인덱스 표시
        st.markdown('<div class="sec-title" style="margin-top:1.5rem;">🔢 AI 파싱 결과 — 30개 파라미터</div>', unsafe_allow_html=True)
        if params:
            col_p1, col_p2, col_p3 = st.columns(3)
            param_groups = {
                "📚 교육·학습": [
                    ("교육비 증가율", params.edu_cost_rate, "%"),
                    ("교육시간 목표", params.edu_hours, "시간"),
                    ("R&D 추가교육", params.rnd_extra_hours, "시간"),
                    ("온라인 학습 비중", params.online_ratio, "%"),
                    ("교육 이수율", params.completion_rate, "%"),
                    ("OJT 비중", params.ojt_ratio, "%"),
                ],
                "💰 보상·승진": [
                    ("연봉 인상률", params.salary_raise, "%"),
                    ("S고과 인센티브", params.sa_incentive, "%"),
                    ("A고과 인센티브", params.a_incentive, "%"),
                    ("승진 연수 단축", params.promotion_shortcut, "년"),
                    ("복지포인트 증가", params.welfare_score, "%"),
                    ("시장 대비 연봉", params.market_salary_pct, "%"),
                ],
                "🌱 조직문화": [
                    ("유연근무 범위", params.culture_scope, ""),
                    ("멘토링 운영", params.mentoring, ""),
                    ("사내 공모제", params.idea_system, ""),
                    ("EAP 확대", params.eap, ""),
                    ("팀 회고 주기", params.retro_freq, ""),
                    ("비전 공유", params.vision_sharing, "회/년"),
                    ("재택근무", params.remote_days_per_week, "일/주"),
                    ("연장근무 상한", params.overtime_cap_hours, "시간"),
                    ("리더 코칭", params.leader_coaching_hours, "시간"),
                    ("팀빌딩", params.team_building_freq, "회/년"),
                ],
            }
            for col, (grp, items) in zip([col_p1, col_p2, col_p3], param_groups.items()):
                with col:
                    st.markdown(f"**{grp}**")
                    for name, val, unit in items:
                        color = "#00E5FF" if (
                            (isinstance(val, float) and val > 0) or
                            (isinstance(val, str) and val not in ("", "아니오", "미도입", "없음", "0"))
                        ) else "#455A64"
                        disp = f"{val}{' '+unit if unit else ''}" if val else "—"
                        st.markdown(f'<div style="display:flex;justify-content:space-between;font-size:0.85rem;'
                                    f'padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.04);">'
                                    f'<span style="color:#607D8B;">{name}</span>'
                                    f'<span style="color:{color};font-weight:600;">{disp}</span></div>',
                                    unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────
    # TAB 2: 직군별 분해
    # ────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div class="sec-title">👥 직군별 효과 분해</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">R&D / 생산 / 영업 / 관리·지원 4개 직군별 분석</div>', unsafe_allow_html=True)

        dept_data = res["dept"]
        dept_notes = {
            "R&D":    "R&D 추가교육·멘토링 효과 최고. 학습민감도 가중치 1.3배 적용.",
            "생산":   "OJT·복지·EAP 민감도 높음. 문화 가중치 1.1배 적용.",
            "영업":   "시장 연봉·자율성 민감도 최고. 보상 가중치 1.3배 적용.",
            "관리/지원": "온라인 학습·회고·비전 공유 효과 높음. 문화 가중치 1.2배 적용.",
        }
        dept_icons = {"R&D":"🔬", "생산":"🏭", "영업":"💼", "관리/지원":"🗂️"}

        d_cols = st.columns(4)
        for col, (dept, dr) in zip(d_cols, dept_data.items()):
            with col:
                comp_c  = delta_color(dr["delta_comp"])
                turn_c  = delta_color(dr["delta_turn"], False)
                comm_c  = delta_color(dr["delta_commit"])
                st.markdown(f"""
                <div class="glass-card" style="text-align:center;">
                  <div style="font-size:2rem;">{dept_icons.get(dept,'🏢')}</div>
                  <div style="font-size:1.1rem; font-weight:700; color:#E0E6F0; margin:0.3rem 0;">{dept}</div>
                  <div style="font-size:0.8rem; color:#607D8B; margin-bottom:0.8rem;">{dr['n']}명</div>
                  <div style="border-top:1px solid rgba(0,229,255,0.1); padding-top:0.8rem;">
                    <div style="margin:0.4rem 0;">
                      <span style="font-size:0.75rem; color:#607D8B;">역량 Δ</span><br>
                      <span style="font-size:1.3rem; color:{comp_c}; font-weight:700;">{fmt_delta(dr['delta_comp'])}</span>
                    </div>
                    <div style="margin:0.4rem 0;">
                      <span style="font-size:0.75rem; color:#607D8B;">이직의향 Δ</span><br>
                      <span style="font-size:1.3rem; color:{turn_c}; font-weight:700;">{fmt_delta(dr['delta_turn'])}</span>
                    </div>
                    <div style="margin:0.4rem 0;">
                      <span style="font-size:0.75rem; color:#607D8B;">몰입도 Δ</span><br>
                      <span style="font-size:1.3rem; color:{comm_c}; font-weight:700;">{fmt_delta(dr['delta_commit'])}</span>
                    </div>
                  </div>
                  <div style="font-size:0.72rem; color:#455A64; margin-top:0.6rem; line-height:1.5;">{dept_notes.get(dept,'')}</div>
                </div>
                """, unsafe_allow_html=True)

        # 직군별 막대 비교
        st.markdown('<div class="sec-title" style="margin-top:1rem;">📊 직군별 변화량 비교</div>', unsafe_allow_html=True)
        dept_names = list(dept_data.keys())
        fig_d = go.Figure()
        for metric, label, color in [
            ("delta_comp",   "역량 향상 Δ",   "#00E5FF"),
            ("delta_turn",   "이직의향 Δ",    "#FF7043"),
            ("delta_commit", "몰입도 향상 Δ", "#00C853"),
        ]:
            vals = [dept_data[d][metric] for d in dept_names]
            fig_d.add_trace(go.Bar(
                name=label, x=dept_names, y=vals,
                marker_color=color, opacity=0.8,
                text=[f"{v:.3f}" for v in vals], textposition="outside",
                textfont=dict(size=11),
            ))
        fig_d.update_layout(
            barmode="group", template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#1E3A5F", tickfont=dict(size=12)),
            legend=dict(orientation="h", y=1.08, font=dict(size=12)),
            font=dict(size=13), margin=dict(t=30, b=20), height=300,
        )
        st.plotly_chart(fig_d, use_container_width=True)

    # ────────────────────────────────────────────────────────
    # TAB 3: 비용·편익
    # ────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="sec-title">💵 비용·편익 상세 분석</div>', unsafe_allow_html=True)

        cost = res["cost"]
        ben  = res["benefit"]

        m1, m2, m3, m4 = st.columns(4)
        for col, label, val, color in [
            (m1, "총 비용", f"{cost['total']:,}만원", "#FF5252"),
            (m2, "총 편익", f"{ben['total']:,}만원",  "#00C853"),
            (m3, "순편익",  f"{res['net_benefit']:,}만원",
             "#00C853" if res["net_benefit"] >= 0 else "#FF5252"),
            (m4, "NET ROI", f"{res['roi']:.1f}%",
             "#00C853" if res["roi"] >= 0 else "#FF5252"),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi-card">
                  <div class="kpi-label">{label}</div>
                  <div class="kpi-value" style="color:{color}; font-size:1.8rem;">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        c_col, b_col = st.columns(2)
        with c_col:
            st.markdown("**💸 비용 항목 내역**")
            brk = cost.get("breakdown", {})
            brk_items = [(k, v) for k, v in brk.items() if v > 0]
            if brk_items:
                fig_c = go.Figure(go.Pie(
                    labels=[k for k, _ in brk_items],
                    values=[v for _, v in brk_items],
                    hole=0.5,
                    marker_colors=["#00E5FF","#0091EA","#1565C0","#0D47A1",
                                   "#80DEEA","#4DD0E1","#26C6DA","#00BCD4","#00ACC1","#00838F",
                                   "#006064","#004D40"],
                    textfont=dict(size=12),
                ))
                fig_c.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10), height=280,
                    legend=dict(font=dict(size=11, color="#B0BEC5")),
                )
                st.plotly_chart(fig_c, use_container_width=True)
            else:
                st.info("비용 항목이 없습니다. 파라미터를 입력하세요.")

            st.markdown(f"""
            <div style="font-size:0.85rem; color:#607D8B; margin-top:0.5rem;">
            참고 (ROI 산식 별도): 보상 인상 {cost['salary_ref']:,}만원 / S·A 인센 {cost['incentive_ref']:,}만원
            </div>
            """, unsafe_allow_html=True)

        with b_col:
            st.markdown("**✅ 편익 항목 내역**")
            ben_items = [
                ("이직비용 절감", ben["turnover_saving"]),
                ("핵심인재 잔류 효과", ben["key_talent"]),
                ("생산성 향상 이득", ben["productivity"]),
            ]
            ben_active = [(k, v) for k, v in ben_items if v > 0]
            if ben_active:
                fig_b = go.Figure(go.Bar(
                    x=[k for k, _ in ben_active],
                    y=[v for _, v in ben_active],
                    marker_color=["#00C853","#00E5FF","#FFB300"],
                    text=[f"{v:,}만원" for _, v in ben_active],
                    textposition="outside",
                    textfont=dict(size=12, color="#E0E6F0"),
                ))
                fig_b.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(gridcolor="#1E3A5F", tickfont=dict(size=11)),
                    font=dict(size=12), margin=dict(t=10, b=10), height=280,
                )
                st.plotly_chart(fig_b, use_container_width=True)
            else:
                st.info("편익이 없습니다. 파라미터를 높여보세요.")

            st.markdown("""
            <div style="font-size:0.82rem; color:#455A64; margin-top:0.5rem; line-height:1.7;">
            • 이직비용: 채용+교육+손실 (Allen 2008, SHRM) 1인당 7,000만원<br>
            • 핵심인재 잔류: S/A 고과자 이탈 방지 × 비용 승수 2.0배<br>
            • 생산성: 역량향상률 × 인건비 × 전환율 3% (Becker 1964 보수적 추정)
            </div>
            """, unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────
    # TAB 4: 민감도 (What-if)
    # ────────────────────────────────────────────────────────
    with tabs[4]:
        st.markdown('<div class="sec-title">📉 조건 변경 시뮬레이션 (What-if)</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">이론 계수를 ±20% 변화시켰을 때 결과가 얼마나 달라지는지 강건성을 검증합니다</div>', unsafe_allow_html=True)

        if sens:
            coef_info = {
                "alpha": ("α 학습효과", "교육 → 역량 변환 효율 (Becker)", "#00E5FF"),
                "beta":  ("β 보상효과", "보상 → 이직 억제 탄력성 (Herzberg)", "#00C853"),
                "gamma": ("γ 문화효과", "조직문화 → 몰입 승수 (Meyer&Allen)", "#FFB300"),
            }
            for coef_key, (coef_name, coef_desc, coef_color) in coef_info.items():
                rows = sens.get(coef_key, [])
                if not rows: continue

                st.markdown(f"""
                <div style="margin:1rem 0 0.3rem;">
                  <span style="color:{coef_color}; font-size:1.1rem; font-weight:700;">{coef_name}</span>
                  <span style="color:#607D8B; font-size:0.85rem; margin-left:0.8rem;">{coef_desc}</span>
                </div>
                """, unsafe_allow_html=True)

                steps = [r["step_label"] for r in rows]
                deltas= [r["delta"] for r in rows]
                robs  = [r["robust"] for r in rows]
                bar_colors = []
                for r in robs:
                    if r == "기준": bar_colors.append("#607D8B")
                    elif "강건" in r: bar_colors.append(coef_color)
                    else: bar_colors.append("#FF5252")

                fig_s = go.Figure(go.Bar(
                    x=steps, y=deltas,
                    marker_color=bar_colors,
                    text=[f"{d:.4f}<br>{r}" for d, r in zip(deltas, robs)],
                    textposition="outside",
                    textfont=dict(size=11, color="#B0BEC5"),
                ))
                fig_s.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    yaxis=dict(gridcolor="#1E3A5F", title=rows[0]["label"], tickfont=dict(size=11)),
                    xaxis=dict(tickfont=dict(size=12)),
                    font=dict(size=12), margin=dict(t=10, b=10), height=240,
                )
                st.plotly_chart(fig_s, use_container_width=True)

            st.markdown("""
            <div class="interp-box" style="margin-top:0.5rem;">
              <div class="interp-title">🎯 면접 활용 포인트</div>
              계수를 ±20% 변화시켜도 역량·이직·몰입의 방향성(개선/악화)은 유지됩니다.
              절대 수치보다 방향의 강건성이 중요하며, 이는 Becker·Herzberg·Meyer&Allen 이론의
              메타분석 범위 내에서 도출한 값임을 확인했습니다.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("분석을 먼저 실행하세요.")

    # ────────────────────────────────────────────────────────
    # TAB 5: A안 vs B안 비교
    # ────────────────────────────────────────────────────────
    with tabs[5]:
        st.markdown('<div class="sec-title">🔀 A안 vs B안 — 정책 비교 시나리오</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">두 정책의 핵심 지표를 나란히 비교합니다. A안은 현재 분석된 정책, B안은 직접 입력하세요.</div>', unsafe_allow_html=True)

        # B안 파라미터 입력
        with st.expander("⚙️ B안 파라미터 직접 입력 (숫자만 입력)", expanded=not bool(cmp)):
            b_cols = st.columns(3)
            with b_cols[0]:
                st.markdown("**📚 교육·학습**")
                b_edu_cost   = st.number_input("교육비 증가율 (%)", 0.0, 100.0, 0.0, 5.0, key="b_edu_cost")
                b_edu_hours  = st.number_input("교육시간 목표 (시간)", 0.0, 200.0, 0.0, 10.0, key="b_edu_hours")
                b_ojt        = st.number_input("OJT 비중 (%)", 0.0, 100.0, 0.0, 5.0, key="b_ojt")
                b_completion = st.number_input("교육 이수율 (%)", 0.0, 100.0, 0.0, 5.0, key="b_completion")
                b_idp        = st.number_input("IDP 지원비 (만원/인)", 0.0, 500.0, 0.0, 50.0, key="b_idp")
            with b_cols[1]:
                st.markdown("**💰 보상·승진**")
                b_salary     = st.number_input("연봉 인상률 (%)", 0.0, 30.0, 0.0, 1.0, key="b_salary")
                b_sa_inc     = st.number_input("S고과 인센티브 (%)", 0.0, 50.0, 0.0, 5.0, key="b_sa_inc")
                b_a_inc      = st.number_input("A고과 인센티브 (%)", 0.0, 30.0, 0.0, 5.0, key="b_a_inc")
                b_welfare    = st.number_input("복지포인트 증가율 (%)", 0.0, 50.0, 0.0, 5.0, key="b_welfare")
                b_mkt        = st.number_input("시장 대비 연봉수준 (%)", 0.0, 130.0, 0.0, 5.0, key="b_mkt")
            with b_cols[2]:
                st.markdown("**🌱 조직문화**")
                b_scope   = st.selectbox("유연근무 범위", ["미도입","일부","전부서"], key="b_scope")
                b_mentor  = st.selectbox("멘토링", ["아니오","예"], key="b_mentor")
                b_eap     = st.selectbox("EAP 확대", ["아니오","예"], key="b_eap")
                b_idea    = st.selectbox("사내 공모제", ["아니오","예"], key="b_idea")
                b_retro   = st.selectbox("팀 회고 주기", ["없음","월1","격주","주1"], key="b_retro")
                b_remote  = st.number_input("재택근무 일/주", 0.0, 5.0, 0.0, 0.5, key="b_remote")
                b_vision  = st.number_input("비전 공유 (회/년)", 0.0, 12.0, 0.0, 1.0, key="b_vision")
                b_coach   = st.number_input("리더 코칭 (시간/년)", 0.0, 150.0, 0.0, 10.0, key="b_coach")

            if st.button("🔀 B안 비교 실행", use_container_width=True):
                pb = PolicyParams(
                    edu_cost_rate=b_edu_cost, edu_hours=b_edu_hours,
                    ojt_ratio=b_ojt, completion_rate=b_completion, idp_support_budget=b_idp,
                    salary_raise=b_salary, sa_incentive=b_sa_inc, a_incentive=b_a_inc,
                    welfare_score=b_welfare, market_salary_pct=b_mkt,
                    culture_scope=b_scope, mentoring=b_mentor, eap=b_eap,
                    idea_system=b_idea, retro_freq=b_retro,
                    remote_days_per_week=b_remote, vision_sharing=b_vision,
                    leader_coaching_hours=b_coach,
                )
                st.session_state.params_b     = pb
                st.session_state.scenario_cmp = compare_scenarios(params, pb)
                st.rerun()

        # 비교 결과 표시
        cmp = st.session_state.scenario_cmp
        if cmp:
            st.markdown(f'<div style="text-align:center; font-size:1.5rem; color:#00E5FF; '
                        f'font-weight:700; margin:1rem 0;">{cmp["overall"]}</div>',
                        unsafe_allow_html=True)

            st.markdown('<table class="cmp-table"><thead><tr>'
                        '<th>지표</th><th>A안 (현재 정책)</th><th>B안</th><th>방향</th><th>승자</th>'
                        '</tr></thead><tbody>', unsafe_allow_html=True)

            for row in cmp["rows"]:
                def fmt_v(v):
                    if isinstance(v, float):
                        if abs(v) > 100: return f"{v:,.0f}"
                        return f"{v:.4f}"
                    return str(v)

                winner = row["승자"]
                w_class = "win-a" if "A" in winner else ("win-b" if "B" in winner else "win-tie")
                st.markdown(
                    f'<tr><td>{row["지표"]}</td>'
                    f'<td>{fmt_v(row["A"])}</td>'
                    f'<td>{fmt_v(row["B"])}</td>'
                    f'<td style="color:#607D8B;">{row["방향"]}</td>'
                    f'<td class="{w_class}">{winner}</td></tr>',
                    unsafe_allow_html=True
                )
            st.markdown('</tbody></table>', unsafe_allow_html=True)

            # 비교 막대 차트
            ra = cmp["result_a"]
            rb = cmp["result_b"]
            metrics = ["delta_comp", "delta_commit", "roi"]
            labels_m= ["역량 향상 Δ", "몰입도 향상 Δ", "ROI (%)"]
            fig_cmp = go.Figure()
            fig_cmp.add_trace(go.Bar(
                name="A안", x=labels_m,
                y=[ra[m] for m in metrics],
                marker_color="#00E5FF", opacity=0.8,
                text=[f"{ra[m]:.3f}" for m in metrics], textposition="outside",
                textfont=dict(size=12),
            ))
            fig_cmp.add_trace(go.Bar(
                name="B안", x=labels_m,
                y=[rb[m] for m in metrics],
                marker_color="#00C853", opacity=0.8,
                text=[f"{rb[m]:.3f}" for m in metrics], textposition="outside",
                textfont=dict(size=12),
            ))
            fig_cmp.update_layout(
                barmode="group", template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#1E3A5F"),
                legend=dict(font=dict(size=13)),
                font=dict(size=13), margin=dict(t=20, b=20), height=280,
            )
            st.plotly_chart(fig_cmp, use_container_width=True)
        else:
            st.info("위에서 B안 파라미터를 입력하고 '🔀 B안 비교 실행' 버튼을 클릭하세요.")

    # ────────────────────────────────────────────────────────
    # TAB 6: 이론 근거
    # ────────────────────────────────────────────────────────
    with tabs[6]:
        st.markdown('<div class="sec-title">📖 이론 근거 — 5개 HR 이론</div>', unsafe_allow_html=True)

        theories = [
            ("📚 Becker 인적자본론 (1964)", "α = 0.20",
             "교육비를 투자하면 직원의 능력(인적자본)이 쌓이고, 이는 곧 생산성 향상으로 연결됩니다.",
             "역량 수식의 핵심 계수 α를 도출하는 이론적 근거. 메타분석(Bassi & McMurrer, 2007)에서 교육투자 ROI는 평균 20~45% 수준.",
             "#00E5FF",
             [("연결 파라미터", "교육비 증가율, 교육시간, OJT 비중, 이수율, IDP 지원비"),
              ("수식", "역량 Δ = α × 학습지수(L)"),
              ("학습지수 L", "교육시간/80×0.3 + 이수율/100×0.2 + OJT/100×0.2 + ..."),
              ]),
            ("🔒 Herzberg 2요인론 (1968)", "β = 0.72",
             "급여·복지 같은 위생요인(Hygiene)은 불만족을 막고, 성장·인정 같은 동기요인(Motivator)은 적극적으로 만족을 만듭니다.",
             "이직 억제 수식에 β가 적용됩니다. Griffeth et al.(2000) 메타분석에서 급여 만족이 이직 의도와 -0.20~-0.45 상관.",
             "#00C853",
             [("연결 파라미터", "연봉 인상률, S/A 인센티브, 복지포인트, 시장 연봉수준"),
              ("수식", "이직의향 Δ = -β × 보상지수(R)"),
              ("보상지수 R", "연봉인상/20×0.35 + S인센/30×0.20 + 시장연봉×0.15 + ..."),
              ]),
            ("💚 Meyer & Allen 3요소 몰입 (1991)", "γ = 0.58",
             "직원이 조직에 남는 이유는 3가지: 정서적(회사가 좋아서), 지속적(떠나면 손해라서), 규범적(의무감). 이 중 정서적 몰입이 성과와 가장 강하게 연결됩니다.",
             "조직문화 파라미터 → 몰입도 수식의 γ. Meyer et al.(2002) 메타분석에서 정서적 몰입 ↑ → 이직의향 ↓, 성과 ↑.",
             "#FFB300",
             [("연결 파라미터", "유연근무, 멘토링, 팀 회고, 비전 공유, EAP, WLB 지원"),
              ("수식", "몰입도 Δ = γ × 문화지수(C)"),
              ("문화지수 C", "유연근무×0.20 + 멘토링×0.15 + 회고주기 + 비전공유 + ..."),
              ]),
            ("🔄 Kirkpatrick 4단계 평가 (1959)", "L1~L4",
             "교육이 정말 효과 있었는지 4단계로 측정합니다: 반응(L1) → 학습(L2) → 행동(L3) → 결과(L4). 이 시뮬레이터는 L2·L3에 해당하는 역량·행동 변화를 추정합니다.",
             "교육 이수율·OJT·온라인 비중 파라미터 설계의 이론 기반.",
             "#9C27B0",
             [("L1 반응", "온라인 학습 비중 반영"),
              ("L2 학습", "교육 이수율, 교육시간 반영"),
              ("L3 행동", "OJT 비중, IDP 지원 반영"),
              ("L4 결과", "ROI 산식으로 추정"),
              ]),
            ("📍 Lee & Mitchell Unfolding Model (1994)", "Sigmoid",
             "이직은 단순히 급여가 낮아서가 아니라, 특정 충격 이벤트(shock) → 이미지 불일치 → 대안 탐색 → 이직 실행의 경로를 따릅니다.",
             "이직확률 0.30을 임계점으로 하는 Sigmoid 함수 모형의 이론 근거. 이직 결정의 비선형성을 반영.",
             "#FF7043",
             [("Sigmoid 함수", "이직자수 = N / (1 + exp(-10×(이직의향 - 0.30)))"),
              ("임계점", "이직의향 0.30 이상에서 실제 이직 급증"),
              ("반영 파라미터", "이직확률 분포 → 연간 이직자 수 산출"),
              ]),
        ]

        for name, coef, simple, academic, color, details in theories:
            st.markdown(f"""
            <div class="glass-card">
              <div style="display:flex; align-items:baseline; gap:0.8rem; margin-bottom:0.6rem;">
                <div style="font-size:1.1rem; font-weight:700; color:{color};">{name}</div>
                <div style="font-size:0.85rem; background:rgba(255,255,255,0.05);
                            padding:2px 10px; border-radius:20px; color:{color};">{coef}</div>
              </div>
              <div style="font-size:1rem; color:#E0E6F0; line-height:1.7; margin-bottom:0.6rem;">{simple}</div>
              <div style="font-size:0.83rem; color:#607D8B; line-height:1.6; border-top:1px solid rgba(255,255,255,0.05);
                          padding-top:0.5rem; margin-bottom:0.5rem;">{academic}</div>
            """, unsafe_allow_html=True)
            for k, v in details:
                st.markdown(f'<div style="font-size:0.82rem; color:#455A64; margin:2px 0;">'
                            f'<span style="color:#00E5FF80; margin-right:6px;">▸</span>'
                            f'<span style="color:#607D8B;">{k}:</span> {v}</div>',
                            unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────
    # TAB 7: 인사팀 제안서 (C안)
    # ────────────────────────────────────────────────────────
    with tabs[7]:
        st.markdown('<div class="sec-title">📝 인사팀 제안서 자동 생성</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">분석 결과를 바탕으로 실제 인사팀에 제출할 수 있는 정책 제안서 초안을 AI가 자동 생성합니다</div>', unsafe_allow_html=True)

        gen_col1, gen_col2 = st.columns([2, 1])
        with gen_col2:
            proposal_tone  = st.selectbox("문체", ["공식 보고서체", "실무 제안서체", "PT 발표 대본"], key="p_tone")
            proposal_pages = st.selectbox("분량", ["A4 1페이지 분량", "A4 2페이지 분량", "요약본 (5줄)"], key="p_pages")
            proposal_key   = st.text_input("Gemini API Key (제안서용)", type="password",
                                           placeholder="API Key 입력", key="p_api")

        with gen_col1:
            st.markdown(f"""
            <div class="interp-box">
              <div class="interp-title">📋 생성될 제안서 포함 내용</div>
              1. 정책 목적 및 배경 (현황 데이터 기반)<br>
              2. 핵심 정책 3~5가지 항목<br>
              3. 예상 효과: 역량 {fmt_delta(res['delta_comp'])} / 이직 {fmt_delta(res['delta_turn'])} / 몰입 {fmt_delta(res['delta_commit'])}<br>
              4. 비용·편익 요약 (ROI {res['roi']:.1f}%, 순편익 {res['net_benefit']:,}만원)<br>
              5. 이론적 근거 (Becker × Herzberg × Meyer&Allen)<br>
              6. 실행 일정 및 기대 효과
            </div>
            """, unsafe_allow_html=True)

        if st.button("📝 제안서 생성", use_container_width=True):
            key_to_use = proposal_key.strip() or ""
            if not key_to_use:
                st.warning("제안서 생성에는 Gemini API Key가 필요합니다.")
            else:
                with st.spinner("Gemini가 제안서를 작성 중입니다..."):
                    try:
                        import httpx, re as re_
                        prompt = f"""
당신은 대기업 HR 컨설턴트입니다. 아래 HRD 정책 시뮬레이션 결과를 바탕으로
인사팀에 제출할 정책 제안서를 작성하세요.

[문체: {proposal_tone}]
[분량: {proposal_pages}]

=== 입력 정책 ===
{st.session_state.policy_text or '(파라미터 직접 입력)'}

=== 시뮬레이션 결과 ===
- 인사팀 승인 등급: {res['grade']}등급
- 역량 향상: {res['delta_comp']:.2%} (Baseline {BASELINE['competency']:.3f} → {res['new_comp']:.3f})
- 이직의향 변화: {res['delta_turn']:.2%} (연간 이직자 {BASELINE['n_turnover']}명 → {res['new_n_turn']}명, {res['turn_reduction']}명 감소)
- 몰입도 향상: {res['delta_commit']:.2%} (Baseline {BASELINE['commitment']:.3f} → {res['new_commit']:.3f})
- 총 투자비용: {res['cost']['total']:,}만원
- 총 편익: {res['benefit']['total']:,}만원
- 순편익: {res['net_benefit']:,}만원
- NET ROI: {res['roi']:.1f}%

=== 직군별 효과 ===
R&D(136명): 역량Δ {res['dept']['R&D']['delta_comp']:.3f}, 이직Δ {res['dept']['R&D']['delta_turn']:.3f}, 몰입Δ {res['dept']['R&D']['delta_commit']:.3f}
생산(152명): 역량Δ {res['dept']['생산']['delta_comp']:.3f}, 이직Δ {res['dept']['생산']['delta_turn']:.3f}, 몰입Δ {res['dept']['생산']['delta_commit']:.3f}
영업(36명): 역량Δ {res['dept']['영업']['delta_comp']:.3f}, 이직Δ {res['dept']['영업']['delta_turn']:.3f}, 몰입Δ {res['dept']['영업']['delta_commit']:.3f}
관리/지원(76명): 역량Δ {res['dept']['관리/지원']['delta_comp']:.3f}, 이직Δ {res['dept']['관리/지원']['delta_turn']:.3f}, 몰입Δ {res['dept']['관리/지원']['delta_commit']:.3f}

=== 이론 근거 ===
- Becker(1964) 인적자본론: 학습→역량 효율 α=0.20
- Herzberg(1968) 2요인론: 보상→이직방지 탄력성 β=0.72
- Meyer&Allen(1991) 3요소 몰입: 문화→몰입 승수 γ=0.58

제안서를 완성된 형태로 작성하세요. 제목, 날짜, 작성자 포함.
"""
                        resp = httpx.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                            json={"contents": [{"parts": [{"text": prompt}]}],
                                  "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}},
                            headers={"Content-Type":"application/json", "x-goog-api-key": key_to_use},
                            timeout=45,
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        text = data["candidates"][0]["content"]["parts"][0]["text"]
                        st.session_state.proposal_text = text
                        st.rerun()
                    except Exception as e:
                        st.error(f"제안서 생성 실패: {e}")

        if st.session_state.proposal_text:
            st.markdown("""
            <div style="background:rgba(0,229,255,0.04); border:1px solid rgba(0,229,255,0.2);
                        border-radius:10px; padding:1.5rem; margin-top:0.5rem;
                        font-size:0.95rem; line-height:1.8; color:#E0E6F0; white-space:pre-wrap;">
            """, unsafe_allow_html=True)
            st.markdown(st.session_state.proposal_text)
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button(
                "📋 제안서 텍스트 복사 (다운로드)",
                data=st.session_state.proposal_text,
                file_name="HRD_정책제안서.txt",
                mime="text/plain",
                use_container_width=True,
            )

    # ────────────────────────────────────────────────────────
    # TAB 8: PDF 리포트 다운로드
    # ────────────────────────────────────────────────────────
    with tabs[8]:
        st.markdown('<div class="sec-title">📥 PDF 상세 리포트 다운로드</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">전사 KPI + 직군별 분해 + 비용편익 + 민감도 + 이론 근거 + 면접 활용 포인트를 포함한 완전한 리포트</div>', unsafe_allow_html=True)

        st.markdown("""
        <div class="interp-box">
          <div class="interp-title">📋 PDF 리포트 포함 내용</div>
          1. 표지 (생성 일시, 이론 기반 명시)<br>
          2. 입력 정책 원문<br>
          3. 인사팀 승인 예측 등급 (S/A/B/C/F)<br>
          4. 핵심 KPI 요약표 (Baseline vs 정책 후)<br>
          5. 실무 해석 가이드 (인사팀 주목 포인트)<br>
          6. 직군별 효과 분해 (R&D / 생산 / 영업 / 관리·지원)<br>
          7. 비용·편익 상세 분석 (HR ROI 모델)<br>
          8. 민감도 분석 (이론 계수 ±20% 강건성 검증)<br>
          9. 비교 시나리오 (A안 vs B안, 실행 시)<br>
          10. 이론 근거 (5개 HR 이론)<br>
          11. 면접 활용 포인트
        </div>
        """, unsafe_allow_html=True)

        if st.button("📄 PDF 리포트 생성", use_container_width=True):
            with st.spinner("PDF 생성 중... (한글 폰트 로딩)"):
                try:
                    from pdf_report import generate_pdf
                    pdf_bytes = generate_pdf(
                        policy_text=st.session_state.policy_text or "(데모)",
                        params=params,
                        result=res,
                        interp=interp,
                        sensitivity=sens,
                        scenario_cmp=cmp,
                    )
                    st.download_button(
                        label="⬇️ PDF 다운로드",
                        data=pdf_bytes,
                        file_name=f"HRD_Policy_Report_{res['grade']}등급.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success(f"✅ PDF 생성 완료 — 등급: {res['grade']}")
                except ImportError:
                    st.error("reportlab 패키지가 필요합니다: pip install reportlab")
                except Exception as e:
                    st.error(f"PDF 생성 실패: {e}")

else:
    # 결과 없을 때 안내
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem; color:#1E3A5F;">
      <div style="font-size:3rem; margin-bottom:1rem;">🔬</div>
      <div style="font-size:1.3rem; color:#263238; margin-bottom:0.5rem;">분석 대기 중</div>
      <div style="font-size:0.95rem; color:#37474F; line-height:1.8;">
        위 입력창에 HR 정책을 서술하고 <strong style="color:#00E5FF;">▶ 분석 시작</strong>을 클릭하거나,<br>
        <strong style="color:#00E5FF;">💡 데모 실행</strong>으로 샘플 결과를 먼저 확인하세요.
      </div>
    </div>
    """, unsafe_allow_html=True)
