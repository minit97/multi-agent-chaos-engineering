#!/usr/bin/env python3
"""발표 자료용 기반 도식 생성 스크립트.

문구나 색을 바꾸고 싶으면 이 파일을 수정한 뒤 다시 실행한다.

    python3 docs/images/generate_diagrams.py

SVG를 먼저 만들고, rsvg-convert가 있으면 PNG도 함께 뽑는다.
SVG는 PowerPoint/Keynote에 그대로 삽입할 수 있고 도형으로 변환해 편집도 된다.
"""

import shutil
import subprocess
from pathlib import Path

OUT = Path(__file__).parent

FONT = "Apple SD Gothic Neo, Pretendard, Noto Sans KR, Malgun Gothic, sans-serif"

# AWS 계열 팔레트
INK = "#232F3E"      # 짙은 남색 - 기본 텍스트/강조 박스
ORANGE = "#FF9900"   # 강조, 흐름 화살표
BLUE = "#527FFF"     # 에이전트
TEAL = "#01A88D"     # 성공/완료
RED = "#D13212"      # 위험/취약점
GRAY = "#687078"     # 보조 텍스트
BODY = "#4A5561"     # 본문 텍스트
LINE = "#D5DBDB"     # 테두리
FILL = "#F7F8F8"     # 연한 배경
BLUE_BG = "#F2F7FF"
ORANGE_BG = "#FFF4E5"
TEAL_BG = "#E8F8F5"
RED_BG = "#FDF0EE"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def box(x, y, w, h, fill=FILL, stroke=LINE, sw=2, rx=12):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def txt(x, y, s, size=16, fill=BODY, anchor="start", weight="400", mono=False):
    family = "SFMono-Regular, Menlo, monospace" if mono else FONT
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="{family}">{esc(s)}</text>')


def circle_num(cx, cy, n, r=19, fill=BLUE):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>'
            + txt(cx, cy + 7, str(n), 19, "#FFFFFF", "middle", "700"))


def arrow(x1, y1, x2, y2, color=ORANGE, sw=3):
    return (f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{sw}" '
            f'fill="none" marker-end="url(#a-{color.lstrip("#")})"/>')


def header(w, title, subtitle=None):
    out = [txt(w / 2, 58, title, 34, INK, "middle", "700")]
    if subtitle:
        out.append(txt(w / 2, 92, subtitle, 18, GRAY, "middle"))
    return out


def svg(name, w, h, parts):
    markers = "".join(
        f'<marker id="a-{c.lstrip("#")}" markerWidth="12" markerHeight="12" '
        f'refX="9" refY="4" orient="auto"><path d="M0,0 L9,4 L0,8 Z" fill="{c}"/></marker>'
        for c in (ORANGE, BLUE, TEAL, RED, GRAY, INK)
    )
    body = "\n  ".join(parts)
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
           f'viewBox="0 0 {w} {h}" font-family="{FONT}">\n'
           f'  <defs>{markers}</defs>\n'
           f'  <rect width="{w}" height="{h}" fill="#FFFFFF"/>\n'
           f'  {body}\n</svg>\n')
    path = OUT / f"{name}.svg"
    path.write_text(doc, encoding="utf-8")
    return path


# ---------------------------------------------------------------- 1. 4단계 사이클
def d1_chaos_cycle():
    W, H = 1200, 700
    p = header(W, "카오스 엔지니어링의 4단계 사이클",
               "일회성 이벤트가 아니라 반복되는 루프")

    p += [f'<circle cx="600" cy="392" r="84" fill="{INK}"/>',
          txt(600, 382, "반복", 20, "#FFFFFF", "middle", "700"),
          txt(600, 410, "Continuous", 15, "#B8C0C8", "middle")]

    steps = [
        (150, 160, 1, "정상 상태 정의", "Steady State — 평소를 숫자로",
         "예) 주문 성공률 99.9%", BLUE, BLUE_BG),
        (720, 160, 2, "가설 수립", '"만약 X가 실패하면 Y일 것이다"',
         "깨지는 순간이 가장 값진 결과", BLUE, BLUE_BG),
        (720, 490, 3, "실험 주입 및 측정", "통제된 조건에서 장애 주입",
         "1단계 지표가 얼마나 흔들리는지", ORANGE, ORANGE_BG),
        (150, 490, 4, "학습 및 개선", "취약점 수정 후 1단계로 복귀",
         "복구 시간·실패 건수·알람 지연", TEAL, TEAL_BG),
    ]
    for x, y, n, title, l1, l2 in [(s[0], s[1], s[2], s[3], s[4], s[5]) for s in steps]:
        pass
    for x, y, n, title, l1, l2, color, bg in steps:
        p += [box(x, y, 330, 124, bg, color, 2.5),
              circle_num(x + 36, y + 36, n, 19, color),
              txt(x + 66, y + 43, title, 22, INK, "start", "700"),
              txt(x + 30, y + 78, l1, 16, BODY),
              txt(x + 30, y + 103, l2, 15, GRAY)]

    p += [arrow(488, 212, 712, 212),
          arrow(885, 292, 885, 482),
          arrow(712, 552, 488, 552),
          arrow(315, 482, 315, 292)]

    p.append(txt(W / 2, 648, "출처: Principles of Chaos Engineering (Netflix, 2015)의 4원칙을 실행 순서로 재구성",
                 15, GRAY, "middle"))
    return svg("01-chaos-cycle", W, H, p)


# ------------------------------------------------------- 2. 5-Agent 파이프라인
def d2_pipeline():
    W, H = 1720, 880
    p = header(W, "5-Agent 파이프라인",
               "앞 에이전트의 출력 텍스트를 다음 프롬프트에 주입하는 순차 구조 (GraphBuilder 미사용)")

    agents = [
        ("Agent 1", "가설 생성", "Hypothesis\nGenerator",
         ["discover_eks_resources", "get_fis_actions", "save_to_database"], "Cell 2", "50.3s"),
        ("Agent 2", "우선순위", "Prioritization",
         ["save_to_database"], "Cell 3", "5.2s"),
        ("Agent 3", "실험 설계", "Experiment\nDesign",
         ["get_fis_actions", "create_fis_experiment", "save_to_database"], "Cell 4", "35.4s"),
        ("Agent 4", "사전 검증", "Pre-flight\nValidation",
         ["discover_eks_resources", "save_to_database"], "Cell 5", "7.6s"),
        ("Agent 5", "학습 분석", "Learning &\nIteration",
         ["save_to_database"], "Cell 6", "23.4s"),
    ]

    bw, gap, y0 = 268, 74, 150
    for i, (tag, ko, en, tools, cell, dur) in enumerate(agents):
        x = 40 + i * (bw + gap)
        p += [box(x, y0, bw, 152, BLUE_BG, BLUE, 2.5),
              txt(x + 18, y0 + 32, tag, 15, BLUE, "start", "700"),
              txt(x + bw - 18, y0 + 32, cell, 14, GRAY, "end"),
              txt(x + bw / 2, y0 + 74, ko, 26, INK, "middle", "700")]
        for j, ln in enumerate(en.split("\n")):
            p.append(txt(x + bw / 2, y0 + 104 + j * 21, ln, 15, GRAY, "middle"))

        # 도구 목록
        ty = y0 + 190
        p += [txt(x + bw / 2, ty, "사용 도구", 14, GRAY, "middle", "700")]
        for j, t in enumerate(tools):
            p += [box(x + 8, ty + 14 + j * 34, bw - 16, 27, "#FFFFFF", LINE, 1.5, 6),
                  txt(x + bw / 2, ty + 32 + j * 34, t, 13, INK, "middle", "400", mono=True)]

        # 소요 시간
        p.append(txt(x + bw / 2, y0 + 340, dur, 20, ORANGE, "middle", "700"))

        if i < len(agents) - 1:
            ax = x + bw + 8
            p += [arrow(ax, y0 + 76, ax + gap - 16, y0 + 76),
                  txt(ax + (gap - 16) / 2, y0 + 62, "텍스트", 12, GRAY, "middle")]

    # 하단 설명
    p += [box(40, 560, 1640, 92, FILL, LINE, 2),
          txt(64, 592, "에이전트 간 데이터 전달", 18, INK, "start", "700"),
          txt(64, 624, 'hypothesis_output = hypothesis_result.message["content"][0]["text"]   →   다음 프롬프트에 f-string으로 주입',
              15, BODY, "start", "400", mono=True)]

    p += [box(40, 676, 800, 88, TEAL_BG, TEAL, 2),
          txt(64, 708, "실행 결과 (실측)", 17, INK, "start", "700"),
          txt(64, 740, "5개 에이전트 합계 약 122초 · 전체 노트북 약 152초 · 토큰 33,731", 15, BODY)]

    p += [box(880, 676, 800, 88, ORANGE_BG, ORANGE, 2),
          txt(904, 708, "중간 산출물", 17, INK, "start", "700"),
          txt(904, 740, "output/hypothesis.json · experiment.json · result.json 으로 저장", 15, BODY)]

    p.append(txt(W / 2, 806, "공유 메모리·메시지 큐·벡터 DB 없음. 단순 텍스트 전달만으로 동작한다.",
                 16, GRAY, "middle"))
    return svg("02-agent-pipeline", W, H, p)


# ------------------------------------------------------------- 3. 기술 스택 3층
def d3_tech_stack():
    W, H = 1440, 860
    p = header(W, "기술 스택 3층 구조",
               "두뇌 · 손발 · 실행기로 역할이 나뉘고, LLM과 대상 클러스터는 리전도 다르다")

    layers = [
        ("Amazon Bedrock", "두뇌", "LLM이 분석·판단·생성",
         "Mantle OpenAI 호환 엔드포인트 · qwen.qwen3-coder-30b-a3b-instruct", ORANGE, ORANGE_BG),
        ("Strands Agents SDK", "손발", "에이전트가 도구를 호출하며 작업 수행",
         "@tool 데코레이터로 등록한 파이썬 함수 6개 · Agent Loop", BLUE, BLUE_BG),
        ("AWS FIS", "실행기", "실제 AWS 리소스에 장애 주입",
         "실험 템플릿 생성 · IAM Role로 권한 범위 한정", TEAL, TEAL_BG),
        ("Amazon EKS", "대상", "테스트 대상 워크로드",
         "Retail Store Sample App · retail-store 네임스페이스 · Pod 10개", INK, FILL),
    ]
    y = 150
    for i, (name, role, desc, detail, color, bg) in enumerate(layers):
        p += [box(120, y, 1200, 122, bg, color, 2.5),
              box(120, y, 150, 122, color, color, 0, 12),
              txt(195, y + 70, role, 28, "#FFFFFF", "middle", "700"),
              txt(300, y + 48, name, 25, INK, "start", "700"),
              txt(300, y + 80, desc, 17, BODY),
              txt(300, y + 106, detail, 15, GRAY)]
        if i < len(layers) - 1:
            p.append(arrow(720, y + 126, 720, y + 154, GRAY, 2.5))
        y += 156

    # 리전 안내
    p += [box(120, 772, 585, 62, "#FFFFFF", ORANGE, 2),
          txt(144, 800, "LLM 호출", 15, ORANGE, "start", "700"),
          txt(144, 822, "us-east-1 (Bedrock Mantle)", 16, INK, "start", "400", mono=True)]
    p += [box(735, 772, 585, 62, "#FFFFFF", TEAL, 2),
          txt(759, 800, "EKS / FIS", 15, TEAL, "start", "700"),
          txt(759, 822, "ap-northeast-2 (boto3 · kubectl)", 16, INK, "start", "400", mono=True)]
    return svg("03-tech-stack", W, H, p)


# ------------------------------------------------------------ 4. Agent Loop
def d4_agent_loop():
    W, H = 1400, 760
    p = header(W, "Strands Agent Loop",
               '코드가 "이 도구를 써라"고 지시하지 않는다. LLM이 스스로 판단해 호출한다.')

    p += [box(60, 300, 200, 100, FILL, GRAY, 2),
          txt(160, 340, "프롬프트", 21, INK, "middle", "700"),
          txt(160, 368, "입력", 15, GRAY, "middle")]

    p += [box(360, 280, 250, 140, BLUE_BG, BLUE, 2.5),
          txt(485, 330, "LLM 추론", 24, INK, "middle", "700"),
          txt(485, 362, "도구를 쓸지,", 15, BODY, "middle"),
          txt(485, 384, "답을 낼지 판단", 15, BODY, "middle")]

    p += [box(730, 170, 270, 130, ORANGE_BG, ORANGE, 2.5),
          txt(865, 214, "도구 호출", 23, INK, "middle", "700"),
          txt(865, 246, "kubectl / boto3 실행", 15, BODY, "middle"),
          txt(865, 272, "결과를 문자열로 반환", 15, GRAY, "middle")]

    p += [box(730, 400, 270, 130, TEAL_BG, TEAL, 2.5),
          txt(865, 444, "최종 응답", 23, INK, "middle", "700"),
          txt(865, 476, "더 쓸 도구가 없다고", 15, BODY, "middle"),
          txt(865, 502, "판단하면 종료", 15, GRAY, "middle")]

    p += [box(1060, 400, 280, 130, FILL, GRAY, 2),
          txt(1200, 444, "다음 에이전트로", 20, INK, "middle", "700"),
          txt(1200, 476, "message[\"content\"][0]", 13, BODY, "middle", "400", mono=True),
          txt(1200, 500, "[\"text\"]", 13, BODY, "middle", "400", mono=True)]

    p += [arrow(268, 350, 352, 350, GRAY, 2.5),
          arrow(612, 320, 722, 250),
          arrow(612, 380, 722, 450, TEAL),
          arrow(1008, 465, 1052, 465, GRAY, 2.5)]

    # 되돌아오는 루프 (위쪽으로 돌려 다른 요소와 겹치지 않게)
    p.append(f'<path d="M865,166 L865,132 L485,132 L485,274" stroke="{ORANGE}" '
             f'stroke-width="3" fill="none" stroke-dasharray="7,5" marker-end="url(#a-FF9900)"/>')
    p.append(txt(675, 122, "결과를 다시 추론에 반영 — 더 쓸 도구가 없다고 판단할 때까지 반복",
                 16, ORANGE, "middle", "700"))

    p += [box(60, 590, 1280, 116, FILL, LINE, 2),
          txt(84, 622, "@tool 데코레이터가 하는 일", 18, INK, "start", "700"),
          txt(84, 654, "타입 힌트와 docstring을 읽어 LLM이 이해할 수 있는 도구 스펙(JSON 스키마)을 자동 생성한다.", 16, BODY),
          txt(84, 682, "따라서 docstring을 잘 쓰는 것이 곧 도구 품질이다. 반환값은 LLM이 읽도록 문자열로 맞춘다.", 16, GRAY)]
    return svg("04-agent-loop", W, H, p)


# ---------------------------------------------------------------- 5. FIS 구조
def d5_fis():
    W, H = 1500, 900
    p = header(W, "AWS FIS: 실험 템플릿의 3요소와 실행 흐름",
               "장애를 코드로 선언하면 AWS가 주입과 원복을 대신 수행한다")

    comps = [
        ("Actions", "무엇을 할지", "aws:eks:pod-cpu-stress",
         'duration: "PT5M"', ORANGE, ORANGE_BG),
        ("Targets", "누구에게", "resourceType: aws:eks:pod",
         "selectorType: labelSelector", BLUE, BLUE_BG),
        ("Stop Conditions", "언제 멈출지", "source: aws:cloudwatch:alarm",
         "알람이 울리면 즉시 중단·원복", TEAL, TEAL_BG),
    ]
    for i, (name, role, l1, l2, color, bg) in enumerate(comps):
        x = 60 + i * 470
        p += [box(x, 140, 440, 170, bg, color, 2.5),
              txt(x + 24, 180, name, 24, INK, "start", "700"),
              txt(x + 440 - 24, 180, role, 16, color, "end", "700"),
              box(x + 20, 202, 400, 40, "#FFFFFF", LINE, 1.5, 6),
              txt(x + 36, 228, l1, 14, INK, "start", "400", mono=True),
              box(x + 20, 250, 400, 40, "#FFFFFF", LINE, 1.5, 6),
              txt(x + 36, 276, l2, 14, BODY, "start", "400", mono=True)]

    # 실행 4단계
    p.append(txt(W / 2, 370, "실행 흐름", 22, INK, "middle", "700"))
    steps = ["실험 템플릿 정의", "실험 시작 (장애 주입)", "진행 상태·메트릭 모니터링", "자동 종료 및 원복"]
    for i, s in enumerate(steps):
        x = 60 + i * 358
        p += [box(x, 400, 320, 96, FILL, LINE, 2),
              circle_num(x + 40, 440, i + 1, 18, INK),
              txt(x + 70, 447, s, 17, INK, "start", "700")]
        if i < 3:
            p.append(arrow(x + 328, 448, x + 350, 448))
    p.append(f'<path d="M1454,448 L1476,448 L1476,528 L220,528 L220,500" stroke="{ORANGE}" '
             f'stroke-width="2.5" fill="none" stroke-dasharray="7,5" marker-end="url(#a-FF9900)"/>')
    p.append(txt(848, 521, "개선 후 다시 실험", 14, ORANGE, "middle", "700"))

    # 우리 프로젝트에서의 실제 값
    p += [box(60, 566, 1380, 148, RED_BG, RED, 2.5),
          txt(84, 600, "우리 코드의 실제 설정 (정직하게)", 19, INK, "start", "700"),
          txt(84, 634, 'stopConditions=[{"source": "none"}]   ← 중단 조건을 걸지 않았다', 16, RED, "start", "700", mono=True),
          txt(84, 666, "FIS가 제공하는 안전장치 중 가장 중요한 것을 아직 쓰지 않고 있다. 지금은 실행 전 검증으로만 막는다.", 16, BODY),
          txt(84, 694, "CloudWatch 알람 기반 Stop Condition 자동 생성이 다음 과제다.", 16, GRAY)]

    p += [box(60, 738, 1380, 120, FILL, LINE, 2),
          txt(84, 772, "우리 파이프라인이 실제로 호출하는 FIS API", 18, INK, "start", "700"),
          txt(84, 806, "fis.list_actions()  ·  fis.create_experiment_template()", 16, INK, "start", "400", mono=True),
          txt(84, 836, "fis.start_experiment() / fis.get_experiment() 은 함수로 정의했으나 에이전트에 연결하지 않았다 (미실행)", 15, GRAY)]
    return svg("05-fis-structure", W, H, p)


# ------------------------------------------------------- 6. 테스트 대상 아키텍처
def d6_target():
    W, H = 1500, 900
    p = header(W, "테스트 대상: Retail Store Sample App on Amazon EKS",
               "에이전트가 kubectl로 직접 읽어낸 실제 구성 — Pod 10개 / 모든 서비스 레플리카 1개")

    p += [box(60, 150, 190, 74, FILL, GRAY, 2),
          txt(155, 196, "Users", 22, INK, "middle", "700"),
          arrow(258, 187, 300, 187, GRAY, 2.5),
          box(310, 150, 150, 74, FILL, GRAY, 2),
          txt(385, 196, "ALB", 22, INK, "middle", "700")]

    # EKS 경계
    p += [f'<rect x="60" y="254" width="1380" height="440" rx="16" fill="#FBFCFC" '
          f'stroke="{INK}" stroke-width="2.5" stroke-dasharray="9,6"/>',
          txt(84, 286, "Amazon EKS Cluster  ·  namespace: retail-store  ·  ap-northeast-2 (Auto Mode)",
              17, INK, "start", "700")]

    p.append(arrow(385, 232, 385, 310, GRAY, 2.5))

    # UI
    p += [box(240, 320, 290, 80, BLUE_BG, BLUE, 2.5),
          txt(385, 355, "ui", 23, INK, "middle", "700"),
          txt(385, 382, "프론트엔드 · replica 1", 14, GRAY, "middle")]

    services = [
        ("catalog", "상품 카탈로그", "catalog-mysql", "MySQL · emptyDir", RED, "데이터 영구 손실"),
        ("carts", "장바구니", "DynamoDB", "AWS 관리형", GRAY, None),
        ("checkout", "결제 처리", "checkout-redis", "Redis · replica 1", RED, "SPOF"),
        ("orders", "주문 관리", "orders-postgresql", "PostgreSQL · PVC", TEAL, None),
    ]
    for i, (name, role, store, store_desc, color, warn) in enumerate(services):
        x = 100 + i * 340
        p += [box(x, 450, 290, 82, BLUE_BG, BLUE, 2.5),
              txt(x + 145, 484, name, 22, INK, "middle", "700"),
              txt(x + 145, 510, role, 14, GRAY, "middle"),
              arrow(x + 145, 534, x + 145, 576, GRAY, 2),
              box(x, 586, 290, 82, "#FFFFFF" if color == GRAY else (RED_BG if color == RED else TEAL_BG),
                  color, 2.5),
              txt(x + 145, 618, store, 18, INK, "middle", "700"),
              txt(x + 145, 644, store_desc, 14, GRAY, "middle")]
        if warn:
            p += [box(x + 60, 676, 170, 30, RED, RED, 0, 15),
                  txt(x + 145, 696, warn, 14, "#FFFFFF", "middle", "700")]
        # UI -> service
        p.append(arrow(385, 402, x + 145, 442, GRAY, 1.8))

    # checkout -> orders 연쇄
    p.append(f'<path d="M1070,491 L1140,491" stroke="{RED}" stroke-width="2.5" fill="none" '
             f'marker-end="url(#a-D13212)"/>')
    p.append(txt(1105, 478, "의존", 13, RED, "middle", "700"))

    p += [box(60, 730, 1380, 128, FILL, LINE, 2),
          txt(84, 764, "에이전트가 확정적으로 아는 것  vs  추론하는 것", 19, INK, "start", "700"),
          txt(84, 798, "확정 (kubectl 응답): Pod 이름·상태·레플리카 수·라벨·StatefulSet의 volumeClaimTemplates 유무", 16, BODY),
          txt(84, 828, "추론 (LLM 판단): 서비스 간 호출 관계·장애 영향 범위·비즈니스 중요도 — 소스 코드는 읽지 않는다", 16, GRAY)]
    return svg("06-target-architecture", W, H, p)


# 발표 자료에서 각 도식이 쓰이는 슬라이드 번호.
# docs/2026-09-16-presentation-source.md 의 슬라이드 구성이 바뀌면 여기도 맞춘다.
SLIDE_OF = {
    "01-chaos-cycle": 7,
    "03-tech-stack": 14,
    "04-agent-loop": 16,
    "05-fis-structure": 18,
    "02-agent-pipeline": 20,
    "06-target-architecture": 25,
}


def export_for_ppt(made):
    """PPT 삽입용으로 슬라이드 번호를 붙인 사본을 ppt/ 에 만든다.

    파일명이 slide-07-... 형태라 정렬하면 발표 순서대로 나온다.
    """
    dest = OUT / "ppt"
    dest.mkdir(exist_ok=True)
    for old in dest.iterdir():
        if old.is_file():
            old.unlink()

    for path in made:
        stem = path.stem
        slide = SLIDE_OF.get(stem)
        if slide is None:
            print(f"  [건너뜀] {stem} — SLIDE_OF에 슬라이드 번호가 없다")
            continue
        topic = stem.split("-", 1)[1]
        for ext in (".svg", ".png"):
            src = path.with_suffix(ext)
            if src.exists():
                shutil.copy2(src, dest / f"slide-{slide:02d}-{topic}{ext}")
    return dest


def main():
    made = [d1_chaos_cycle(), d2_pipeline(), d3_tech_stack(),
            d4_agent_loop(), d5_fis(), d6_target()]

    conv = shutil.which("rsvg-convert")
    for path in made:
        line = f"  {path.name}"
        if conv:
            png = path.with_suffix(".png")
            subprocess.run([conv, "-w", "1800", str(path), "-o", str(png)], check=True)
            line += f"  →  {png.name}"
        print(line)
    print(f"\n{len(made)}개 도식 생성 완료: {OUT}")

    dest = export_for_ppt(made)
    print(f"PPT 삽입용 사본 (슬라이드 번호순): {dest}")


if __name__ == "__main__":
    main()
