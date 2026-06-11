"""
pdf_report.py — PDF 상세 리포트 생성 v4
한글 NanumGothic 폰트 | 전사 + 직군별 + 비용편익 + 민감도 + 실무해석
"""

import io
import os
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

from simulator import BASELINE, ORG, PolicyParams, build_interpretation


def _find_font() -> str | None:
    """NanumGothic.ttf 경로 탐색"""
    candidates = [
        os.path.join(os.getcwd(), "NanumGothic.ttf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "NanumGothic.ttf"),
        "NanumGothic.ttf",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _register_font():
    font_path = _find_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("NanumGothic", font_path))
            return "NanumGothic"
        except Exception:
            pass
    return "Helvetica"


def generate_pdf(
    policy_text: str,
    params: PolicyParams,
    result: dict,
    interp: dict,
    sensitivity: dict | None = None,
    scenario_cmp: dict | None = None,
) -> bytes:
    """PDF 리포트 바이트 반환"""
    if not REPORTLAB_OK:
        raise ImportError("reportlab 패키지가 필요합니다: pip install reportlab")

    buf   = io.BytesIO()
    font  = _register_font()
    doc   = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    # ── 색상 팔레트 ─────────────────────────────────────────
    C_NAVY    = colors.HexColor("#090B10")
    C_CYAN    = colors.HexColor("#00E5FF")
    C_PANEL   = colors.HexColor("#0D1B2A")
    C_BORDER  = colors.HexColor("#1E3A5F")
    C_GREEN   = colors.HexColor("#00C853")
    C_RED     = colors.HexColor("#FF5252")
    C_AMBER   = colors.HexColor("#FFB300")
    C_GRAY    = colors.HexColor("#B0BEC5")
    C_WHITE   = colors.white

    def sty(name, size, bold=False, color=None, align="LEFT", leading=None):
        # NanumGothic Bold TTF가 없으면 일반 폰트 사용 (bold는 <b> 태그로 처리)
        fname = font
        return ParagraphStyle(
            name,
            fontName=fname,
            fontSize=size,
            textColor=color or C_NAVY,
            alignment={"LEFT": 0, "CENTER": 1, "RIGHT": 2}.get(align, 0),
            leading=leading or size * 1.4,
            spaceAfter=2,
        )

    s_title   = sty("title",   22, color=C_NAVY,   align="CENTER")
    s_sub     = sty("sub",     11, color=C_GRAY,   align="CENTER")
    s_h1      = sty("h1",      14, color=colors.HexColor("#0077AA"))
    s_h2      = sty("h2",      11, color=colors.HexColor("#004466"))
    s_body    = sty("body",    10, color=C_NAVY,   leading=15)
    s_small   = sty("small",    9, color=C_GRAY)
    s_grade   = sty("grade",   36, color=C_CYAN,   align="CENTER")
    s_interp  = sty("interp",  10, color=colors.HexColor("#1A237E"), leading=16)

    def H(text, level=1): return Paragraph(text, s_h1 if level == 1 else s_h2)
    def P(text): return Paragraph(text, s_body)
    def SP(h=0.3): return Spacer(1, h*cm)
    def HR(): return HRFlowable(width="100%", thickness=0.5, color=C_BORDER)

    # ── KPI 색상 ────────────────────────────────────────────
    def delta_color(val, positive_is_good=True):
        if val == 0: return C_GRAY
        if positive_is_good:
            return C_GREEN if val > 0 else C_RED
        else:
            return C_GREEN if val < 0 else C_RED

    def pct(val): return f"{val:+.2%}" if val != 0 else "변화 없음"
    def won(val): return f"{val:+,.0f}만원" if val != 0 else "0만원"

    grade_color = {"S": C_CYAN, "A": C_GREEN, "B": C_AMBER, "C": C_AMBER, "F": C_RED}

    # ── 스타일 헬퍼 ────────────────────────────────────────
    def kpi_table(rows):
        t = Table(rows, colWidths=[4.5*cm, 3*cm, 3*cm, 3*cm, 3.5*cm])
        t.setStyle(TableStyle([
            ("FONTNAME",    (0,0), (-1,-1), font),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("BACKGROUND",  (0,0), (-1,0),  C_PANEL),
            ("TEXTCOLOR",   (0,0), (-1,0),  C_CYAN),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F7FA")]),
            ("GRID",        (0,0), (-1,-1), 0.3, C_BORDER),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
        ]))
        return t

    # ─────────────────────────────────────────────────────────
    story = []

    # ▌표지
    story += [
        SP(1),
        Paragraph("HRD Policy Simulator", s_title),
        Paragraph("정책 효과 상세 분석 리포트", s_sub),
        SP(0.3),
        Paragraph(f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", s_small),
        Paragraph("박찬윤 | 삼육대학교 | Becker × Kirkpatrick × Herzberg × Meyer&Allen", s_small),
        SP(0.5), HR(), SP(0.5),
    ]

    # ▌입력 정책
    story += [H("📝 입력 정책"), P(policy_text or "(데모 모드)"), SP(0.3), HR(), SP(0.3)]

    # ▌승인 등급
    g = result["grade"]
    g_col = grade_color.get(g, C_GRAY)
    grade_sty = ParagraphStyle("gs", fontName=font, fontSize=72,
                               textColor=g_col, alignment=1, leading=90)
    grade_label_sty = ParagraphStyle("gl", fontName=font, fontSize=14,
                                     textColor=g_col, alignment=1, leading=20)
    grade_labels = {"S":"최우수", "A":"우수", "B":"양호", "C":"보통", "F":"재검토"}
    story += [
        H("🏆 인사팀 승인 예측 등급"),
        SP(0.6),
        Paragraph(g, grade_sty),
        SP(0.3),
        Paragraph(grade_labels.get(g, ""), grade_label_sty),
        SP(0.4),
        P(interp.get("grade", "")),
        SP(0.5), HR(), SP(0.3),
    ]

    # ▌핵심 KPI 요약
    story += [H("📊 핵심 KPI — Baseline vs 정책 후")]
    kpi_rows = [
        ["지표", "Baseline", "정책 후", "변화 (Δ)", "이론 근거"],
        ["📚 평균 역량",
         f"{BASELINE['competency']:.3f}",
         f"{result['new_comp']:.3f}",
         pct(result['delta_comp']),
         "Becker × Kirkpatrick"],
        ["🔒 이직의향",
         f"{BASELINE['turnover']:.3f}",
         f"{result['new_turn']:.3f}",
         pct(result['delta_turn']),
         "Herzberg × Lee&Mitchell"],
        ["👥 예상 이직자",
         f"{BASELINE['n_turnover']}명",
         f"{result['new_n_turn']}명",
         f"{result['turn_reduction']}명 감소",
         "Sigmoid 임계점 모형"],
        ["💚 평균 몰입도",
         f"{BASELINE['commitment']:.3f}",
         f"{result['new_commit']:.3f}",
         pct(result['delta_commit']),
         "Meyer & Allen 3요소"],
        ["💰 NET ROI",
         "—",
         f"{result['roi']:.1f}%",
         won(result['net_benefit']),
         "HR ROI 모델"],
    ]
    story.append(kpi_table(kpi_rows))
    story += [SP(0.3), HR(), SP(0.3)]

    # ▌실무 해석 가이드 (A안)
    story += [H("💡 실무 해석 가이드 — 인사팀이 주목할 포인트")]
    for key, label in [
        ("competency", "📚 역량 향상"),
        ("turnover",   "🔒 이직 억제"),
        ("commitment", "💚 몰입도"),
        ("roi",        "💰 투자 대비 효과"),
    ]:
        msg = interp.get(key, "")
        if msg:
            interp_sty = ParagraphStyle(
                f"i_{key}", fontName=font, fontSize=10,
                textColor=colors.HexColor("#1A237E"), leading=16,
                spaceBefore=4, leftIndent=10,
                borderPad=6, borderColor=C_BORDER, borderWidth=0.5,
            )
            story.append(Paragraph(f"<b>{label}</b>  {msg}", s_body))
            story.append(SP(0.2))
    story += [SP(0.2), HR(), SP(0.3)]

    # ▌직군별 효과 분해
    story += [H("👥 직군별 효과 분해")]
    dept_rows = [["직군", "인원", "역량 향상 Δ", "이직억제 Δ", "몰입향상 Δ", "특이사항"]]
    dept_notes = {
        "R&D":    "R&D 추가교육·멘토링 효과 最高",
        "생산":   "OJT·복지·EAP 민감도 高",
        "영업":   "시장연봉·자율성 민감도 最高",
        "관리/지원": "온라인학습·회고·비전 몰입↑",
    }
    for dept, dr in result["dept"].items():
        dept_rows.append([
            dept,
            f"{dr['n']}명",
            pct(dr['delta_comp']),
            pct(dr['delta_turn']),
            pct(dr['delta_commit']),
            dept_notes.get(dept, ""),
        ])
    t2 = Table(dept_rows, colWidths=[2.5*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 5.5*cm])
    t2.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), font),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("BACKGROUND",(0,0), (-1,0), C_PANEL),
        ("TEXTCOLOR", (0,0), (-1,0), C_CYAN),
        ("ALIGN",     (0,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("GRID",      (0,0), (-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [t2, SP(0.3), HR(), SP(0.3)]

    # ▌비용·편익 분석
    story += [H("💵 비용·편익 분석 — HR ROI 모델")]
    cost = result["cost"]
    ben  = result["benefit"]
    cost_rows = [
        ["항목", "금액 (만원)", "구분"],
        ["① 교육비 증가분",        f"{cost['edu_total']:,}",      "비용"],
        ["② 문화 프로그램",        f"{cost['culture_total']:,}",  "비용"],
        ["③ 연봉 인상 비용",       f"{cost['salary_cost']:,}",    "비용"],
        ["④ 인센티브 비용",        f"{cost['incentive_cost']:,}", "비용"],
        ["── 총 비용",             f"{cost['total']:,}",          "📌 비용 합계"],
        ["⑤ 이직비용 절감",        f"{ben['turnover_saving']:,}", "편익"],
        ["⑥ 핵심인재 잔류",        f"{ben['key_talent']:,}",     "편익"],
        ["⑦ 생산성 이득",          f"{ben['productivity']:,}",   "편익"],
        ["── 총 편익",             f"{ben['total']:,}",           "✅ 편익 합계"],
        ["💵 순편익 (편익-비용)",  f"{result['net_benefit']:,}",  "순편익"],
        ["🏆 NET ROI",             f"{result['roi']:.1f}%",       "ROI"],
    ]
    t3 = Table(cost_rows, colWidths=[6*cm, 4*cm, 7*cm])
    t3.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), font),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("BACKGROUND",(0,0), (-1,0), C_PANEL),
        ("TEXTCOLOR", (0,0), (-1,0), C_CYAN),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F5F7FA")]),
        ("BACKGROUND",(0,5), (-1,5), colors.HexColor("#E3F2FD")),
        ("BACKGROUND",(0,9), (-1,9), colors.HexColor("#E8F5E9")),
        ("BACKGROUND",(0,10),(-1,10),colors.HexColor("#FFF8E1")),
        ("BACKGROUND",(0,11),(-1,11),colors.HexColor("#E0F7FA")),
        ("GRID",      (0,0), (-1,-1), 0.3, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story += [t3, SP(0.3), HR(), SP(0.3)]

    # ▌민감도 분석
    if sensitivity:
        story += [H("📉 민감도 분석 — 이론 계수 ±20% 강건성 검증")]
        story.append(P("현재 정책 파라미터를 유지한 채 이론 계수만 변화시켜 결과의 안정성을 검증합니다."))
        story.append(SP(0.2))
        for coef_key, coef_label in [("alpha","α 학습효과"),("beta","β 보상효과"),("gamma","γ 문화효과")]:
            rows = sensitivity.get(coef_key, [])
            if not rows: continue
            story.append(Paragraph(f"▸ {coef_label}", s_h2))
            tbl_rows = [["변화율", "계수값", rows[0]["label"], "기준 대비", "ROI", "강건성"]]
            for r in rows:
                tbl_rows.append([
                    r["step_label"],
                    str(r["coef_val"]),
                    str(r["delta"]),
                    str(r["diff"]) if r["diff"] is not None else "—",
                    f"{r['roi']:.1f}%",
                    r["robust"],
                ])
            t4 = Table(tbl_rows, colWidths=[2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm, 5.5*cm])
            t4.setStyle(TableStyle([
                ("FONTNAME", (0,0), (-1,-1), font),
                ("FONTSIZE", (0,0), (-1,-1), 8),
                ("BACKGROUND",(0,0),(-1,0), C_PANEL),
                ("TEXTCOLOR", (0,0),(-1,0), C_CYAN),
                ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.white, colors.HexColor("#F5F7FA")]),
                ("BACKGROUND",(0,3),(-1,3), colors.HexColor("#E8F5E9")),
                ("GRID", (0,0),(-1,-1), 0.3, C_BORDER),
                ("TOPPADDING",    (0,0),(-1,-1), 4),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ]))
            story += [t4, SP(0.2)]
        story += [SP(0.2), HR(), SP(0.3)]

    # ▌비교 시나리오
    if scenario_cmp:
        story += [H("🔀 A안 vs B안 비교 시나리오")]
        cmp_header = ["지표", "A안", "B안", "방향", "승자"]
        cmp_rows   = [cmp_header]
        for row in scenario_cmp.get("rows", []):
            a_val = row["A"]
            b_val = row["B"]
            def fmt(v):
                if isinstance(v, float):
                    return f"{v:.4f}" if abs(v) < 1000 else f"{v:,.0f}"
                return str(v)
            cmp_rows.append([row["지표"], fmt(a_val), fmt(b_val), row["방향"], row["승자"]])
        t5 = Table(cmp_rows, colWidths=[4*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm])
        t5.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,-1), font),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BACKGROUND",(0,0),(-1,0), C_PANEL),
            ("TEXTCOLOR", (0,0),(-1,0), C_CYAN),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F5F7FA")]),
            ("GRID",(0,0),(-1,-1),0.3,C_BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ]))
        story += [t5, SP(0.2)]
        story.append(Paragraph(f"종합 판정: {scenario_cmp.get('overall','')}", s_h2))
        story += [SP(0.3), HR(), SP(0.3)]

    # ▌이론 근거
    story += [H("📖 이론 근거 — 5개 HR 이론")]
    theories = [
        ("Becker 인적자본론 (1964)", "α=0.20",
         "교육 투자 → 인적자본 축적 → 생산성 향상. 역량 수식의 핵심 계수 α를 도출하는 근거."),
        ("Kirkpatrick 4단계 평가 (1959)", "L1~L4",
         "반응(L1)→학습(L2)→행동(L3)→결과(L4). 교육 이수율·OJT·온라인 비중 파라미터의 이론 기반."),
        ("Herzberg 2요인론 (1968)", "β=0.72",
         "위생요인(급여·복지)은 불만족 방지, 동기요인(성장·인정)은 만족 창출. 이직 억제 수식 근거."),
        ("Meyer & Allen 3요소 몰입 (1991)", "γ=0.58",
         "정서적·지속적·규범적 몰입의 3요소. 조직문화 파라미터가 몰입도에 미치는 영향의 이론 기반."),
        ("Lee & Mitchell Unfolding Model (1994)", "Sigmoid",
         "충격 이벤트 → 이직 의도 → 실제 이직의 비선형 경로. Sigmoid 임계점 모형(0.30)의 이론 근거."),
    ]
    for name, coef, desc in theories:
        story.append(Paragraph(f"▸ <b>{name}</b>  [{coef}]", s_body))
        story.append(Paragraph(desc, s_small))
        story.append(SP(0.1))

    story += [SP(0.3), HR(), SP(0.3)]

    # ▌면접 활용 포인트
    story += [H("🎯 면접 활용 포인트")]
    tips = [
        "\"이론 계수를 ±20% 변화시켜도 역량·이직·몰입의 방향성은 유지됩니다. 계수의 강건성이 정책의 신뢰도를 뒷받침합니다.\"",
        "\"Becker·Herzberg·Meyer&Allen 3개 이론을 단일 수식 엔진에 통합하여 HR 정책의 복합 효과를 정량화했습니다.\"",
        "\"직원이 정책을 직접 시뮬레이션하고 인사팀에 제안하는 Bottom-up 문화 구축을 목표로 설계했습니다.\"",
        f"\"400명 합성 데이터(Seed=42, SK하이닉스 조직구조 기반) 위에서 개인별 역량·이직확률·몰입도를 시뮬레이션합니다.\"",
    ]
    for tip in tips:
        story.append(Paragraph(f"• {tip}", s_body))
        story.append(SP(0.1))

    # ▌푸터
    story += [
        SP(0.5), HR(), SP(0.2),
        Paragraph("HRD Policy Simulator | 박찬윤 | 삼육대학교", s_small),
        Paragraph("Becker(1964) × Kirkpatrick(1959) × Herzberg(1968) × Meyer&Allen(1991) × Lee&Mitchell(1994)", s_small),
    ]

    doc.build(story)
    return buf.getvalue()
