# 🔬 HRD Policy Simulator

**HR 정책의 효과를 AI와 이론 수식으로 정량화하는 조직 시뮬레이터**

> Becker(1964) 인적자본론 × Herzberg(1968) 2요인론 × Meyer & Allen(1991) 몰입 모형  
> 박찬윤 | 삼육대학교 | HRD/HR 포트폴리오

---

## 📌 프로젝트 배경

HR 아티클을 읽다가 생긴 한 가지 의문에서 출발했습니다.

> *"이 정책이 실제로 어떤 효과를 낼까? 숫자로 확인할 수 없을까?"*

단순한 정성적 분석에서 벗어나, **HR 이론 3개를 수식으로 연결**하고  
**Gemini AI가 자유 서술 정책을 30개 파라미터로 자동 수치화**하는 시뮬레이터를 만들었습니다.

**최종 목표**: 직원이 직접 정책을 시뮬레이션 → 결과가 좋으면 인사팀에 제안하는 **Bottom-up 제안 문화** 구축

---

## 🚀 라이브 데모

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hrd-becker-herzberg-meyer-allen-excel-streamlit.streamlit.app)

> API Key 없이 **💡 데모 실행** 버튼으로 바로 체험 가능

---

## 🎯 핵심 기능

| 기능 | 설명 |
|------|------|
| **AI 정책 파싱** | 자유 서술 → Gemini AI → 30개 파라미터 자동 수치화 |
| **수식 엔진** | Becker × Herzberg × Meyer&Allen 3개 이론 통합 계산 |
| **인사팀 승인 등급** | S / A / B / C / F 자동 판정 |
| **직군별 분해** | R&D / 생산 / 영업 / 관리·지원 4개 직군 개별 분석 |
| **비용·편익 분석** | 이직절감 + 핵심인재 잔류 + 생산성 향상 HR ROI 산출 |
| **A안 vs B안 비교** | 두 정책을 나란히 비교하는 시나리오 분석 |
| **조건 변경(What-if)** | 이론 계수 ±20% 변화 시 강건성 검증 |
| **실무 해석 가이드** | 각 KPI별 경영적 해석 + 인사팀 주목 포인트 자동 생성 |
| **인사팀 제안서** | 분석 결과 기반 제안서 초안 AI 자동 작성 |
| **PDF 리포트** | 11개 섹션 완전한 분석 리포트 다운로드 |

---

## 🧮 이론 수식 구조

```
역량 향상  Δcomp   = α × L(학습지수)          ← Becker 인적자본론
이직의향  Δturn   = -β × R(보상지수)          ← Herzberg 2요인론
몰입도    Δcommit = γ × C(문화지수)           ← Meyer & Allen 3요소

α = 0.20  (학습→역량 효율,   Becker 1964)
β = 0.72  (보상→이직 탄력성, Herzberg 1968 메타분석)
γ = 0.58  (문화→몰입 승수,   Meyer & Allen 1991 메타분석)

이직자 수 = Sigmoid 임계점 모형 (임계값 0.30, Lee & Mitchell 1994)
ROI = (이직절감 + 핵심인재잔류 + 생산성향상 - 총비용) / 총비용
```

---

## 📁 파일 구조

```
HRD-Becker-Herzberg-Meyer-Allen-Excel-Streamlit/
│
├── app.py               # Streamlit 메인 앱 (9개 탭)
├── simulator.py         # 수식 엔진 (30개 파라미터, 직군별 분해)
├── gemini_parser.py     # Gemini API 파싱 모듈
├── pdf_report.py        # PDF 리포트 생성 (한글 지원)
├── requirements.txt     # 의존성 패키지
├── NanumGothic.ttf      # PDF 한글 폰트
├── 건물_디자인.png       # 홀로그램 건물 이미지
└── README.md
```

---

## ⚡ 로컬 실행

### 1. 저장소 클론
```bash
git clone https://github.com/chanyoon22/HRD-Becker-Herzberg-Meyer-Allen-Excel-Streamlit-.git
cd HRD-Becker-Herzberg-Meyer-Allen-Excel-Streamlit-
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 앱 실행
```bash
python -m streamlit run app.py
```

### 4. 브라우저에서 확인
```
http://localhost:8501
```

> **Gemini API Key**: [Google AI Studio](https://aistudio.google.com/app/apikey)에서 무료 발급  
> API Key 없이도 **💡 데모 실행**으로 모든 기능 체험 가능

---

## 🏗️ 기술 스택

| 구분 | 사용 기술 |
|------|----------|
| **Frontend** | Streamlit 1.32+, Plotly (바차트·레이더·파이차트) |
| **AI** | Google Gemini 2.5 Flash API |
| **수식 엔진** | Python (math, dataclasses) |
| **PDF 생성** | ReportLab (한글 NanumGothic 폰트) |
| **데이터** | 400명 합성 데이터 (Seed=42, SK하이닉스 조직구조 기반) |

---

## 📊 가상 기업 설정

| 항목 | 값 |
|------|----|
| 총 임직원 | 400명 |
| 직군 구성 | R&D 136명 / 생산 152명 / 영업 36명 / 관리·지원 76명 |
| 평균 연봉 | 7,000만원 |
| Baseline 역량 | 0.618 |
| Baseline 몰입도 | 0.622 |
| Baseline 이직의향 | 0.284 |
| 연간 이직자 | 41명 (10.2%) |
| S+A 고과자 | 132명 (33%) |

> 실제 기업의 조직구조를 참고한 합성 데이터 (Seed=42 고정, 재현 가능)

---

## 🎓 이론 근거 및 출처

| 이론 | 핵심 개념 | 계수 | 출처 |
|------|----------|------|------|
| **Becker 인적자본론** | 교육투자 → 역량 축적 → 생산성 | α=0.20 | Becker(1964), Bassi & McMurrer(2007) |
| **Herzberg 2요인론** | 위생요인(불만방지) vs 동기요인(만족창출) | β=0.72 | Herzberg(1968), Griffeth et al.(2000) |
| **Meyer & Allen 몰입** | 정서적·지속적·규범적 몰입 3요소 | γ=0.58 | Meyer & Allen(1991), Meyer et al.(2002) |
| **Kirkpatrick 4단계** | 반응→학습→행동→결과 | L1~L4 | Kirkpatrick(1959) |
| **Lee & Mitchell** | 충격이벤트 → 이직 Unfolding | Sigmoid | Lee & Mitchell(1994) |

---

## 💼 포트폴리오 포인트

이 프로젝트가 대기업 HRD/HR 면접에서 어필할 수 있는 이유:

1. **AI 리터러시**: Gemini API를 활용해 자연어 정책을 정형 데이터로 변환
2. **HR 이론 이해**: 단순 암기가 아닌, 수식으로 구현할 수 있는 수준의 이론 이해
3. **데이터 기반 사고**: 정성적 정책을 정량적 KPI로 연결하는 논리 구조
4. **현업 감각**: 직군별 분해, 비용·편익 분석, 면접 활용 포인트까지 실무 관점 반영
5. **Bottom-up 제안**: 직원 누구나 쓸 수 있는 툴로 설계 → 조직문화 혁신 제안

---

## 🔮 향후 개선 계획

- [ ] 실제 직원 데이터 연동 (Excel 업로드 → 시뮬레이션)
- [ ] 정책 히스토리 저장 및 비교 (DB 연동)
- [ ] 시계열 시뮬레이션 (6개월 단위 효과 발현 추이)
- [ ] 팀 단위 마이크로 시뮬레이션

---

## 👨‍💻 만든 사람

**박찬윤**  
삼육대학교  

[![GitHub](https://img.shields.io/badge/GitHub-chanyoon22-181717?logo=github)](https://github.com/chanyoon22)

---

*"데이터로 증명하는 HR — 정성적 직관을 정량적 근거로"*
