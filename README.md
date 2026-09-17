# Multi-Agent Chaos Engineering

AI 에이전트 5개가 릴레이하며 EKS 마이크로서비스의 복원력을 자동으로 테스트하는 파이프라인

---

## 개요

기존 카오스 엔지니어링은 시스템 분석부터 실험 설계, 실행, 결과 분석까지 3~4주가 소요되었다.
이 프로젝트는 Strands Agents SDK + Amazon Bedrock + AWS FIS를 조합하여 전 과정을 AI 에이전트로 자동화하고, 수 시간 내 첫 실험까지 도달한다.

> "실패를 없애려 하지 말고, AI와 함께 실패를 설계하세요."

---

## 파이프라인 구조

```
Agent 1          Agent 2           Agent 3            Agent 4            Agent 5
Hypothesis  →  Prioritization  →  Experiment    →   Pre-flight    →   Learning &
Generator       Agent              Design            Validation         Iteration
(가설 생성)     (우선순위)          (실험 설계)        (사전 검증)         (학습 분석)
```

| Agent | 역할 | 사용 도구 |
|---|---|---|
| Agent 1 | EKS 리소스 탐색 → 장애 가설 5개 생성 | discover_eks_resources, get_fis_actions |
| Agent 2 | Impact/Likelihood/Safety 기반 우선순위 결정 | - |
| Agent 3 | FIS 실험 템플릿 생성 + 가드레일 검증 | get_fis_actions, create_fis_experiment |
| Agent 4 | 타깃 Pod 상태 검증 (실행 준비 확인) | discover_eks_resources |
| Agent 5 | 취약점 식별, 개선안, 복원력 점수 평가 | - |

---

## 기술 스택

| 기술 | 역할 |
|---|---|
| **Strands Agents SDK** | AI 에이전트 프레임워크 (도구 호출 + Agent Loop) |
| **Amazon Bedrock (Mantle)** | LLM 호스팅 (Qwen3 Coder 30B) |
| **AWS FIS** | 장애 주입 실험 서비스 |
| **Amazon EKS** | 테스트 대상 Kubernetes 클러스터 |
| **boto3 / kubectl** | AWS API + K8s 리소스 조회 |

---

## 테스트 대상

[AWS Retail Store Sample App](https://github.com/aws-containers/retail-store-sample-app) (EKS 배포)

```
UI → Catalog(MySQL) → Cart(DynamoDB) → Checkout(Redis, RabbitMQ) → Orders(PostgreSQL)
```

---

## 빠른 시작

### 사전 요구사항

- Python 3.10+
- AWS CLI + kubectl (EKS 연결 상태)
- Bedrock API Key

### 설치

```bash
pip install strands-agents[openai] boto3 python-dotenv
```

### 환경 변수 (.env)

```
AWS_BEARER_TOKEN_BEDROCK=<Bedrock API Key>
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE_EKS=<EKS 접근용 AWS 프로필>
EKS_REGION=ap-northeast-2
EKS_CLUSTER_NAME=<클러스터명>
EKS_NAMESPACE=retail-store
FIS_ROLE_ARN=arn:aws:iam::<ACCOUNT_ID>:role/ChaosAgentFISRole
```

### 실행

```bash
jupyter notebook test.ipynb
# Cell 0 ~ Cell 8 순서대로 실행
```

---

## 프로젝트 구조

```
├── test.ipynb              # 메인 파이프라인 노트북 (Cell 0~8)
├── .env                    # 환경 변수 (git 제외)
├── output/                 # 에이전트 실행 결과 저장
│   ├── hypothesis.json
│   ├── experiment.json
│   └── result.json
└── docs/
    ├── 2026-09-16-presentation-source.md   # 발표 스크립트 (슬라이드별 구성 + 스피커 노트)
    ├── images/                             # 발표용 도식 (SVG/PNG + 생성 스크립트)
    ├── notebooklm-ppt-source.md            # 발표 자료 원본
    ├── multi-agent-chaos-engineering-guide.md  # 파이프라인 상세 가이드
    ├── ai-resilience-testing.md            # 컨퍼런스 발표 정리
    ├── aws-resilience-references.md        # AWS 참고 문서 분석
    ├── strands-agents-sdk.md               # Strands SDK 사용법
    ├── v1-multi-agent-chaos-engineering.md  # v1 구현 정리
    └── v1-setup-guide.md                   # AWS 환경 세팅 가이드
```

---

## 시간 절감 효과

| 작업 | 기존 | AI 기반 |
|---|---|---|
| 시스템 분석 | 1~2주 | 수 분 |
| 가설 생성 | 수 시간~수 일 | 수 초 |
| 실험 설계 | 3~5일/건 | 수 초 |
| 안전 검증 | 1주/시나리오 | 수 시간 |
| **첫 실험까지** | **3~4주** | **수 시간** |

---

## 참고 자료

- [sample-strands-chaos-engineering-agents](https://github.com/aws-samples/sample-strands-chaos-engineering-agents) - 원본 레포
- [Strands Agents SDK](https://strandsagents.com/) - 프레임워크 문서
- [AWS Resilience Analysis Framework](https://docs.aws.amazon.com/prescriptive-guidance/latest/resilience-analysis-framework/) - SEEMS 분류
- [AWS Fault Isolation Boundaries](https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/) - 격리 경계

---

## License

MIT
