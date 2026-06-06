# AI 기반 복원력 테스트: Multi-Agent Chaos Engineering

## 발표 개요

이 발표는 AI 에이전트를 활용하여 AWS EKS 마이크로서비스의 복원력을 자동으로 테스트하는 시스템을 소개한다. Strands Agents SDK와 AWS FIS를 결합하여, 기존 3~4주 걸리던 카오스 엔지니어링 사이클을 수 시간으로 단축하는 방법을 다룬다.

핵심 메시지: **"실패를 없애려 하지 말고, AI와 함께 실패를 설계하세요."**

---

## 1. 카오스 엔지니어링 소개

### 카오스 엔지니어링이란?

넷플릭스에서 시작된 개념으로, **일부러 장애를 만들어서 시스템이 잘 버티는지 확인**하는 테스트 방법론이다.

예를 들어:
- "주문 서비스 Pod을 삭제하면 자동 복구되는가?"
- "DB에 CPU 부하를 주면 다른 서비스가 영향받는가?"
- "네트워크를 끊으면 타임아웃 처리가 제대로 되는가?"

### 왜 필요한가?

AWS CTO Werner Vogels는 "Everything fails all the time"이라고 말했다. 모든 것은 결국 장애가 발생한다. 중요한 것은 장애를 막는 것이 아니라, 장애가 발생했을 때 시스템이 스스로 복구할 수 있도록 설계하는 것이다.

AWS 공유 책임 모델에서:
- AWS: 클라우드의 신뢰성(Reliability **of** the Cloud)
- 고객: 클라우드 안에서의 신뢰성(Reliability **in** the Cloud)

즉 EKS 클러스터 위에 올라간 우리 서비스의 복원력은 우리가 직접 검증해야 한다.

### 기존 카오스 엔지니어링의 한계

기존에는 시스템 분석부터 실험 설계, 실행, 결과 분석까지 전부 사람이 수동으로 수행해야 했다. 첫 번째 실험까지 3~4주가 소요되었다.

| 기존 방식 | AI 기반 방식 |
|---|---|
| "어디가 약할까?" 사람이 고민 | Agent 1이 자동 분석 |
| "뭐부터 테스트하지?" 사람이 결정 | Agent 2가 우선순위 결정 |
| "FIS 실험 어떻게 짜지?" 사람이 설계 | Agent 3이 자동 설계 |
| "실행하고 모니터링" 사람이 수행 | Agent 4가 자동 검증 |
| "결과 분석 및 보고서" 사람이 작성 | Agent 5가 자동 분석 |

---

## 2. 구현 방법: 5-Agent 파이프라인

### 전체 접근 방식

5개의 전문 AI 에이전트가 릴레이 방식으로 협업하는 파이프라인을 구축한다. 각 에이전트는 고유한 역할을 가지며, 이전 에이전트의 출력이 다음 에이전트의 입력으로 전달된다.

### 파이프라인 흐름

Agent 1(가설 생성) → Agent 2(우선순위) → Agent 3(실험 설계) → Agent 4(실행/검증) → Agent 5(학습/분석)

### 각 에이전트의 역할

**Agent 1: Hypothesis Generator** - EKS 클러스터의 실제 아키텍처를 kubectl로 실시간 탐색하고, 5개 장애 도메인(컴퓨트, 데이터, 네트워크, 종속성, 리소스)을 커버하는 가설을 자동 생성한다.

**Agent 2: Prioritization Agent** - Safety-first 원칙에 따라 가설 우선순위를 결정한다. 영향도(40%), 가능성(25%), 안전성(20%), 학습가치(15%) 가중치를 적용한다. 폭발 반경이 작은 실험부터 시작한다.

**Agent 3: Experiment Design Agent** - 가설을 실행 가능한 AWS FIS 실험 템플릿으로 변환한다. 안전 가드레일 5원칙을 검증하고, 실제 AWS FIS API를 호출하여 템플릿을 생성한다.

**Agent 4: Pre-flight Validation** - 실험 실행 전 타깃 리소스의 존재 여부와 상태를 검증한다. Pod 수, Running 상태, 레플리카 수를 확인하여 실험 준비 완료 여부를 판단한다.

**Agent 5: Learning & Iteration** - 실험 결과를 종합 분석하여 취약점 식별, 개선 권고, 복원력 점수 평가, 다음 반복 실험 제안을 수행한다.

### 에이전트 간 데이터 전달 방식

각 에이전트는 독립적으로 실행되며, 이전 에이전트의 출력 텍스트를 다음 에이전트의 프롬프트에 문자열로 주입하는 파이프라인 패턴이다. 공유 메모리나 메시지 큐 없이 단순한 텍스트 전달로 동작한다.

### 에이전트가 아키텍처를 파악하는 방법

에이전트는 미리 아키텍처를 아는 것이 아니라, 매번 실시간으로 클러스터를 조회해서 파악한다.

1. `discover_eks_resources("retail-store")` 도구 호출
2. 내부적으로 `kubectl get all -n retail-store -o json` 실행
3. 실제 클러스터에서 Deployment, StatefulSet, Pod, Service 정보 수신
4. JSON으로 정리하여 에이전트에게 반환
5. LLM이 서비스 간 종속성, 스토리지 유형, SPOF 위험 등을 추론

확정적으로 아는 것(Pod 이름, 상태, 레플리카 수)과 추론하는 것(서비스 간 종속성, 비즈니스 중요도)을 구분하며 분석한다.

---

## 3. 활용 스택: AWS Bedrock + Strands Agents + FIS

### Amazon Bedrock

LLM 모델 호스팅 서비스이다. 이 프로젝트에서는 Bedrock Mantle 엔드포인트를 통해 OpenAI 호환 API로 모델을 호출한다. Bedrock API Key를 사용하여 인증하며, 별도 IAM 설정 없이 LLM을 사용할 수 있다.

사용 모델: Qwen3 Coder 30B (Bedrock Mantle에서 OpenAI Chat Completions API로 호출)

역할: 모든 에이전트의 "두뇌" 역할. 프롬프트를 읽고, 도구 호출 여부를 판단하고, 분석 결과를 생성한다.

### Strands Agents SDK

AWS가 만든 오픈소스 AI 에이전트 프레임워크이다. LLM에 도구(함수)를 제공하면, 에이전트가 자율적으로 추론과 도구 호출을 반복하는 Agent Loop 구조로 동작한다.

핵심 개념:
- **@tool 데코레이터**: 파이썬 함수를 에이전트가 사용할 수 있는 도구로 등록
- **Agent Loop**: 입력 → LLM 추론 → 도구 호출 → 결과 전달 → 다시 추론 → ... → 최종 응답
- **자율 판단**: 코드에서 "이 도구를 써라"고 명시하지 않아도, LLM이 스스로 판단하여 도구를 선택

에이전트 생성은 매우 간결하다:
```python
agent = Agent(
    model=bedrock_model,      # 어떤 LLM을 사용할지
    system_prompt="역할...",   # 에이전트에게 부여할 역할
    tools=[도구1, 도구2],      # 사용 가능한 도구 목록
)
```

사용 도구 목록:
| 도구 | 기능 |
|---|---|
| discover_eks_resources | kubectl로 Pod/Service/Deployment 현황 조회 |
| get_fis_actions | 사용 가능한 FIS 액션 목록 조회 |
| create_fis_experiment | FIS 실험 템플릿 실제 생성 (AWS API 호출) |
| save_to_database | 실험 데이터 저장 |

### AWS FIS (Fault Injection Service)

AWS 리소스에 장애를 주입하는 서비스이다. "실험 템플릿"을 정의하고 실행하면, 지정된 리소스에 실제 장애가 발생한다.

FIS의 동작 방식:
1. 실험 템플릿 생성 (어떤 액션을, 어떤 타깃에, 얼마나)
2. 실험 시작 (실제 장애 주입)
3. 실험 모니터링 (진행 상태/메트릭 수집)
4. 실험 완료 (장애 해제, 시스템 복구 확인)

EKS 관련 FIS 액션:
| 액션 | 효과 |
|---|---|
| aws:eks:pod-delete | Pod 강제 삭제 |
| aws:eks:pod-cpu-stress | CPU 부하 주입 |
| aws:eks:pod-memory-stress | 메모리 부하 주입 |
| aws:eks:pod-network-latency | 네트워크 지연 주입 |
| aws:eks:pod-network-packet-loss | 패킷 손실 주입 |
| aws:ec2:terminate-instances | 워커 노드 종료 |

### 3개 서비스의 조합

```
[Bedrock - 두뇌]     → LLM이 분석/판단/생성
[Strands - 손발]     → 에이전트가 도구를 호출하며 작업 수행
[FIS - 실행기]       → 실제 AWS 리소스에 장애 주입
```

---

## 4. 테스트 인프라 구조와 서비스 의존성

### 대상 애플리케이션: Retail Store Sample App

AWS에서 공식 제공하는 마이크로서비스 쇼핑몰 애플리케이션이다. Amazon EKS 클러스터 위에서 동작한다.

### 서비스 구조

```
Users → ALB → [Amazon EKS Cluster - retail-store namespace]
                 ├── UI Service (프론트엔드)
                 ├── Catalog Service → MySQL (상품 카탈로그)
                 ├── Cart Service → DynamoDB (장바구니)
                 ├── Checkout Service → Redis, RabbitMQ (결제 처리)
                 └── Orders Service → PostgreSQL (주문 관리)
```

### 서비스 의존성 맵

| 서비스 | 의존하는 것 | 의존 장애 시 영향 |
|---|---|---|
| UI | Catalog, Cart, Checkout, Orders | 전체 화면 불가 |
| Catalog | MySQL | 상품 조회 불가 |
| Cart | DynamoDB | 장바구니 기능 중단 |
| Checkout | Redis + RabbitMQ + Orders | 결제 전체 중단 |
| Orders | PostgreSQL | 주문 생성/조회 불가 |

### 발견된 아키텍처 취약점

1. **Catalog MySQL의 emptyDir 사용** - Pod 재시작 시 상품 데이터 영구 손실 (PersistentVolume 미사용)
2. **Redis/RabbitMQ 단일 레플리카** - SPOF(단일 장애점), 해당 Pod 장애 시 결제 전체 중단
3. **서비스 간 종속성 체인** - Checkout → Redis → RabbitMQ → Orders, 하나만 죽어도 연쇄 장애

### 인프라 현황

| 항목 | 설정 |
|---|---|
| EKS 클러스터 | <YOUR_CLUSTER_NAME> (ap-northeast-2, Auto Mode) |
| Kubernetes 버전 | 1.35 |
| 노드 | Karpenter 관리 (general-purpose + system) |
| Pod 수 | 10개 (retail-store namespace) |
| FIS Role | ChaosAgentFISRole (EKS/Network/SSM/EC2 권한) |

---

## 5. 에이전트 역할 상세와 FIS 연동

### Agent 1: Hypothesis Generator → FIS 연동

Agent 1은 `get_fis_actions` 도구로 실제 사용 가능한 FIS 액션을 확인하고, 각 가설에 적합한 FIS 액션을 매핑한다.

예시 출력:
```json
{
  "id": "H-001",
  "title": "카트 서비스 Pod 삭제 시 체크아웃 영향",
  "service": "carts",
  "failure_domain": "compute",
  "hypothesis": "만약 carts Pod가 삭제되면 체크아웃이 불가할 것이다",
  "impact_score": 8,
  "likelihood_score": 7,
  "suggested_fis_action": "aws:eks:pod-delete",
  "label_selector": "app.kubernetes.io/name=carts"
}
```

### Agent 3: Experiment Design → FIS 템플릿 생성

Agent 3은 `create_fis_experiment` 도구로 **실제 AWS FIS 콘솔에 실험 템플릿을 생성**한다.

생성되는 FIS 템플릿 구조:
```json
{
  "actions": {
    "action-1": {
      "actionId": "aws:eks:pod-delete",
      "targets": {"Pods": "target-pods"}
    }
  },
  "targets": {
    "target-pods": {
      "resourceType": "aws:eks:pod",
      "parameters": {
        "clusterIdentifier": "arn:aws:eks:...:cluster/<YOUR_CLUSTER_NAME>",
        "namespace": "retail-store",
        "selectorType": "labelSelector",
        "selectorValue": "app.kubernetes.io/name=orders"
      }
    }
  },
  "roleArn": "arn:aws:iam::...:role/ChaosAgentFISRole"
}
```

### 안전 가드레일 5대 원칙 (Agent 3이 적용)

1. **타깃 사전 검증** - 대상 리소스 존재 확인, 없으면 실험 거부
2. **서비스별 안전 기준** - 최소 레플리카 수 확인, 단일 레플리카면 주의
3. **위험 액션 자동 배제** - zonal-autoshift 등 신뢰성 낮은 액션 차단
4. **폭발 반경 제어** - 한 번에 하나의 서비스만 타깃, 전체 클러스터 금지
5. **안전 우선 순위 배치** - 저위험 실험부터 실행, 고위험은 후순위

### Agent 4: Pre-flight Validation → 실행 전 검증

실제 실험 실행 전에 타깃의 현재 상태를 확인한다:
- Pod가 존재하고 Running 상태인지
- 레플리카 수가 충분한지
- 네임스페이스가 올바른지

검증 완료 후 FIS 콘솔에서 실험을 시작할 수 있다.

### Agent 5: Learning & Iteration → 결과 분석

실험 결과를 종합하여:
- 발견된 취약점을 HIGH/MEDIUM/LOW로 분류
- 각 취약점에 대한 구체적 개선 권고사항 제시
- 현재 복원력 성숙도 점수(1-10) 평가
- 다음 반복 실험에서 수행할 추가 테스트 제안
- 아키텍처 수준의 개선안 도출

---

## 6. 시간 절감 효과

| 작업 | 기존 방식 | AI 기반 |
|---|---|---|
| 시스템 분석/탐색 | 1~2주 | 수 분 |
| 실험 가설 생성 | 수 시간~수 일 | 수 초 |
| FIS 실험 설계 | 실험 당 3~5일 | 수 초 |
| 안전성 검증 | 시나리오 당 1주 | 수 시간 |
| **첫 실험까지 총 소요** | **3~4주** | **수 시간** |

전체 사이클 최대 **90% 단축**.

전체 파이프라인 실행에 약 3.5만 토큰 사용 (비용 거의 무시 수준).

---

## 7. 핵심 요약

| 항목 | 내용 |
|---|---|
| 해결하는 문제 | 카오스 엔지니어링의 높은 진입 장벽과 긴 소요 시간 |
| 해결 방법 | 5개 AI 에이전트가 릴레이로 전 과정 자동화 |
| 사용 기술 | Strands Agents SDK + Amazon Bedrock + AWS FIS + Amazon EKS |
| 성과 | 3~4주 → 수 시간 (90% 단축) |
| 안전 장치 | 5대 가드레일 원칙으로 통제된 실험 보장 |

**결론: 장애는 피할 수 없지만 준비할 수는 있다. AI 에이전트와 함께라면 그 준비를 훨씬 빠르고 체계적으로 할 수 있다.**
