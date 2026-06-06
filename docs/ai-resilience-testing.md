# AI 기반 복원력 테스트 (Agentic AI with Resilience)

> AWS Summit 발표 기반 정리 - Multi-Agent Chaos Engineering

---

## 핵심 메시지

> "실패를 없애려 하지 말고, AI와 함께 실패를 설계하세요."

| 원칙 | 설명 |
|---|---|
| **보이지 않던 실패를 드러냅니다** | AI 에이전트가 숨은 취약점을 자동 탐지. 코드저장소 + AWS 리소스 교차 분석으로 파드/네트워크/DB/EC2 전 영역 커버 |
| **안전하게 실패를 제어합니다** | FIS 템플릿 + SSM Automation으로 통제된 카오스, 재현 가능한 복구. 근거(RCA) 기반 검증 사이클로 학습이 추적되는 실험 구조 |
| **AI는 팀의 일원입니다** | 멀티 에이전트가 반복/규모 담당, 엔지니어는 판단/전략에 집중. 첫 실험 3~4주 → 수 시간, 전체 사이클 최대 90% 단축 |

---

## 1. 배경: 장애 관리 철학

**Dr. Werner Vogels (VP and CTO, AWS):**

> "Everything fails all the time"
> "We needed to build systems that embrace failure as a natural occurrence."

**공유 책임 모델:**
- AWS: Reliability **of** the Cloud
- Customer: Reliability **in** the Cloud

---

## 2. 대상 애플리케이션 아키텍처

Amazon EKS 클러스터 기반 마이크로서비스 쇼핑몰 애플리케이션:

```
Users → ALB → [Amazon EKS Cluster]
                 ├── UI Service
                 ├── Catalog Service → MySQL
                 ├── Cart Service → DynamoDB
                 ├── Checkout Service → Redis, RabbitMQ
                 └── Orders Service → PostgreSQL
```

### 서비스 구성

| 서비스 | 역할 | 데이터스토어 |
|---|---|---|
| UI Service | 사용자 인터페이스 | - |
| Catalog Service | 상품 카탈로그 | MySQL |
| Cart Service | 장바구니 | DynamoDB |
| Checkout Service | 결제 처리 | Redis, RabbitMQ |
| Orders Service | 주문 관리 | PostgreSQL |

---

## 3. 복원력 라이프사이클 프레임워크

중심에 **Agentic AI**를 두고 5단계 순환 구조:

```
        ┌─── 목표 설정 ───┐
        │                  │
   대응 및 학습        설계 및 구현
        │                  │
        │   [Agentic AI]   │
        │                  │
       운영          평가 및 테스트
        └──────────────────┘
```

1. **목표 설정**: 복원력 목표(RTO/RPO) 정의
2. **설계 및 구현**: 장애 시나리오 설계, FIS 실험 템플릿 생성
3. **평가 및 테스트**: 카오스 실험 실행, 메트릭 수집
4. **운영**: 프로덕션 환경 모니터링
5. **대응 및 학습**: 결과 분석, 개선안 도출, 지식 축적

---

## 4. Multi-Agent Chaos Engineering 파이프라인

### 아키텍처 개요

```
[Amazon Bedrock - Multi-Agent Chaos Engineering]

Hypothesis     →  Prioritization  →  Experiment  →  Experiment   →  Learning &
Generator          Agent              Design         Execution       Iteration
                                                        │
                                                        ↓
                                                    [AWS FIS]
                                                        ↓
                                              [EKS Microservices]
```

### 에이전트 역할

| 에이전트 | 역할 |
|---|---|
| **Hypothesis Generator** | 시스템 인벤토리 분석, 장애 가설 자동 생성 |
| **Prioritization Agent** | 영향도/가능성 기반 우선순위 결정 |
| **Experiment Design** | AWS FIS 실험 템플릿 설계, SSM 문서 생성 |
| **Experiment Execution** | 가드레일 검증 후 실제 장애 주입, 메트릭 수집 |
| **Learning & Iteration** | 결과 분석, 취약점 도출, 개선안 제안 |

---

## 5. 에이전트 구현 - Strands Agents 프레임워크

```python
agent = Agent(
    model=get_model(),
    tools=[
        use_aws,
        get_workload_tags
    ],
    system_prompt=SYSTEM_PROMPT,
    callback_handler=get_callback("ssm-inventory-analysis")
)
```

### 주요 도구

| 도구 | 용도 |
|---|---|
| `use_aws` | AWS API 호출 (EKS, FIS, SSM, CloudWatch 등) |
| `get_workload_tags` | 워크로드 태그 기반 리소스 탐색 |

---

## 6. 에이전트 안전 가드레일 (5대 원칙)

실험 설계와 실행 시 에이전트가 준수하는 원칙:

### 1. 타깃 사전 검증
네임스페이스, Pod 라벨, 리소스 상태를 실제 환경에서 확인한 뒤에만 실험을 생성합니다.
리소스가 존재하지 않거나 요건을 충족하지 않으면 실험 생성을 거부합니다.

### 2. 서비스별 안전 기준
노드 종료는 최소 2개 이상일 때만 허용하고, ELB는 2개 이상 AZ에 걸쳐있을 때만 AZ 장애를 허용하는 등 서비스 특성에 맞는 최소 요건을 적용합니다.

### 3. 위험 액션 자동 배제
`zonal-autoshift`, `inject-api-internal-error` 등 부적절하거나 신뢰성이 낮은 FIS 액션을 자동으로 배제합니다.

### 4. 폭발 반경 제어
개별 서비스 타깃만 허용하며, 앱 전체를 대상으로 하는 광범위한 라벨 셀렉터를 금지합니다.

### 5. 안전 우선 순위 배치
폭발 반경이 작고 롤백이 명확한 실험에 높은 우선순위를 부여하고, 고위험 실험은 후순위로 배치합니다.

---

## 7. 데모 흐름 (3단계)

> 가설부터 분석까지, Agent가 자율적으로 수행하는 복원력 테스트

### Step 1: 가설 생성 → 우선순위 → FIS 실험 설계
장애 가설을 자동으로 나열하고, 영향도/가능성 기반으로 순위를 매긴 뒤 AWS FIS 실험 템플릿을 생성

### Step 2: FIS 실험 생성 → 실제 장애 주입 실행
가드레일을 통과한 실험만 실제 환경에 주입, 실행 중 메트릭 수집

### Step 3: 결과 분석 → 취약점 및 개선안 도출
실행 결과를 가설과 비교 분석하여, 다음 테스트 또는 구조 개선안을 제안

---

## 8. 테스트 시나리오 예시

### 시나리오 1: Orders Service Pod 종료 (Priority 1)

| 항목 | 내용 |
|---|---|
| **가설** | Pod 종료 시 Kubernetes가 자동으로 새 Pod를 생성해 서비스가 복구된다 |
| **실험** | `aws:eks:pod-delete`로 Orders Service Pod 강제 종료 후 회복 시간 측정 |
| **예상 결과** | K8s가 30~60초 내 새 Pod 생성, 일시적 지연 후 정상 복구 |

### 시나리오 2: Catalog MySQL 데이터 손실 (Priority 8)

| 항목 | 내용 |
|---|---|
| **가설** | emptyDir 스토리지를 사용하는 DB Pod가 종료되면 모든 상품 데이터가 영구 손실된다 |
| **실험** | `aws:eks:pod-delete`로 Catalog MySQL Pod 강제 종료 후 데이터 영속성 검증 |
| **예상 결과** | Pod는 재생성되지만 emptyDir 휘발성으로 인해 상품 카탈로그 데이터 100% 손실 |

---

## 9. AI 기반 복원력 테스트의 시간 절감 효과

| 작업 단계 | 기존 방식 | AI 기반 방식 |
|---|---|---|
| 인벤토리 분석을 통한 시스템 탐색 | 1~2주 | **수 분** |
| 실험 가설 생성 | 수 시간 ~ 수 일 | **수 초** |
| SSM 문서 생성 및 테스트 | 실험 당 3~5일 | **수 초** |
| 안전성 검증 및 검토 | 시나리오 당 1주 | **수 시간** |
| **첫 번째 실험까지 총 소요 시간** | **3~4주** | **수 시간** |

> 전체 사이클 최대 **90% 단축**

---

## 10. 우리 프로젝트에 적용할 구현 계획

### 필요한 AWS 서비스

| 서비스 | 용도 |
|---|---|
| Amazon Bedrock | LLM 기반 에이전트 호스팅 |
| AWS FIS (Fault Injection Service) | 장애 주입 실험 실행 |
| AWS SSM (Systems Manager) | Automation 문서 기반 실험 실행 |
| Amazon EKS | 대상 마이크로서비스 클러스터 |
| Amazon CloudWatch | 메트릭 수집 및 모니터링 |

### Strands Agents 기반 구현 구조

```python
from strands import Agent
from strands.multiagent import GraphBuilder

# 1. Hypothesis Generator Agent
hypothesis_agent = Agent(
    name="hypothesis_generator",
    system_prompt="시스템 인벤토리를 분석하여 장애 가설을 생성하는 전문가입니다.",
    tools=[use_aws, get_workload_tags]
)

# 2. Prioritization Agent
prioritization_agent = Agent(
    name="prioritization_agent",
    system_prompt="장애 가설의 영향도와 가능성을 평가하여 우선순위를 결정합니다."
)

# 3. Experiment Design Agent
design_agent = Agent(
    name="experiment_designer",
    system_prompt="AWS FIS 실험 템플릿과 SSM 문서를 설계합니다.",
    tools=[use_aws]
)

# 4. Experiment Execution Agent
execution_agent = Agent(
    name="experiment_executor",
    system_prompt="가드레일을 검증한 후 FIS 실험을 실행하고 메트릭을 수집합니다.",
    tools=[use_aws]
)

# 5. Learning & Iteration Agent
learning_agent = Agent(
    name="learning_agent",
    system_prompt="실험 결과를 분석하여 취약점과 개선안을 도출합니다.",
    tools=[use_aws]
)

# Graph 구성
builder = GraphBuilder()
builder.add_node(hypothesis_agent, "hypothesis")
builder.add_node(prioritization_agent, "prioritization")
builder.add_node(design_agent, "design")
builder.add_node(execution_agent, "execution")
builder.add_node(learning_agent, "learning")

builder.add_edge("hypothesis", "prioritization")
builder.add_edge("prioritization", "design")
builder.add_edge("design", "execution")
builder.add_edge("execution", "learning")

builder.set_entry_point("hypothesis")
builder.set_execution_timeout(900)

graph = builder.build()

# 실행
result = graph("EKS 클러스터의 복원력을 테스트하세요")
```

### 가드레일 구현 예시

```python
from strands import tool, ToolContext

@tool(context=True)
def validate_experiment_safety(
    experiment_config: dict,
    tool_context: ToolContext
) -> dict:
    """실험 안전성을 검증합니다.
    Args:
        experiment_config: FIS 실험 설정
    """
    violations = []

    # 1. 타깃 사전 검증
    if not experiment_config.get("target_verified"):
        violations.append("타깃 리소스가 검증되지 않았습니다")

    # 2. 서비스별 안전 기준
    min_replicas = experiment_config.get("target_min_replicas", 1)
    if min_replicas < 2:
        violations.append("최소 2개 이상의 레플리카가 필요합니다")

    # 3. 위험 액션 배제
    blocked_actions = ["zonal-autoshift", "inject-api-internal-error"]
    if experiment_config.get("action") in blocked_actions:
        violations.append(f"차단된 액션: {experiment_config['action']}")

    # 4. 폭발 반경 제어
    if experiment_config.get("selector_scope") == "cluster-wide":
        violations.append("클러스터 전체 대상 셀렉터는 금지됩니다")

    return {
        "safe": len(violations) == 0,
        "violations": violations
    }
```

---

## 참고 자료

- AWS FIS Documentation: https://docs.aws.amazon.com/fis/
- Strands Agents SDK: https://strandsagents.com/
- Resilience Lifecycle Whitepaper (AWS)
- Werner Vogels: "Everything fails all the time"
