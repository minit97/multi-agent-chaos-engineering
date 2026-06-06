# AWS 복원력 테스트 참고 자료 분석

> 컨퍼런스 세션 발표자 참고 문서 3개에 대한 분석

---

## 목차

1. [Multi-Agent Chaos Engineering (AWS Builder Center)](#1-multi-agent-chaos-engineering)
2. [AWS Fault Isolation Boundaries (Whitepaper)](#2-aws-fault-isolation-boundaries)
3. [Resilience Analysis Framework (Prescriptive Guidance)](#3-resilience-analysis-framework)

---

## 1. Multi-Agent Chaos Engineering

- **URL**: https://builder.aws.com/content/31mgtbvETKMwTF1MyZIxQP6dWIC/multi-agent-chaos-engineering
- **GitHub**: https://github.com/aws-samples/sample-strands-chaos-engineering-agents
- **라이선스**: Apache-2.0 (aws-samples)

### 개요

Strands Agents SDK와 Amazon Bedrock을 기반으로 구축된 AI 기반 카오스 엔지니어링 플랫폼. 5개의 전문 에이전트가 협업하여 AWS 워크로드의 복원력을 체계적으로 테스트한다.

### 기술 스택

| 구성 요소 | 기술 |
|---|---|
| Framework | AWS Strands Agents SDK |
| Models | Amazon Bedrock (Claude 3.5 Sonnet 기본값) |
| Database | Amazon Aurora Serverless v2 (MySQL) |
| Chaos Engineering | AWS Fault Injection Service (FIS) |
| Infrastructure | AWS CDK (TypeScript) |
| Integration | Model Context Protocol (MCP) servers |
| Interface | Jupyter Notebook |
| Observability | CloudWatch Logs (구조화된 JSON 로깅) |

### 5-Agent 아키텍처

```
┌────────────────┐    ┌────────────────────┐    ┌──────────────────┐
│   Hypothesis   │───▶│   Prioritization   │───▶│   Experiment     │
│   Generator    │    │   Agent            │    │   Design Agent   │
└────────────────┘    └────────────────────┘    └──────────────────┘
                                                         │
                                                         ▼
┌────────────────┐                              ┌──────────────────┐
│   Learning &   │◀────────────────────────────│   Experiments    │
│   Iteration    │                              │   Agent          │
└────────────────┘                              └──────────────────┘
```

| 에이전트 | 역할 |
|---|---|
| **Hypothesis Generator** | AWS 워크로드 인벤토리 분석, 장애 가설 자동 생성 |
| **Prioritization Agent** | 영향도/가능성 기반 우선순위 결정 |
| **Experiment Design Agent** | FIS 실험 템플릿 및 SSM 문서 설계 |
| **Experiments Agent** | 가드레일 검증 후 FIS 실험 실행, DB 상태 업데이트 |
| **Learning & Iteration** | 결과 분석, 취약점 식별, 다음 실험 제안 |

### 핵심 특징

- **Multi-Agent Architecture**: 카오스 엔지니어링 각 단계별 전문 에이전트
- **Notebook-Driven**: Jupyter Notebook으로 전체 워크플로우 실행
- **End-to-End Execution**: 가설 생성 → 실험 실행 → 결과 분석 자동화
- **AWS Native**: FIS, IAM, SSM 등 AWS 기본 서비스 활용
- **Safety-First**: 태그 기반 리소스 필터링으로 안전한 실험
- **Traceability**: Aurora DB에 모든 실험 이력 추적

### 대상 워크로드

[AWS Containers Retail Store Sample App](https://github.com/aws-containers/retail-store-sample-app)을 기본 테스트 대상으로 사용:
- Amazon EKS 기반 마이크로서비스
- UI → Catalog(MySQL) → Cart(DynamoDB) → Checkout(Redis, RabbitMQ) → Orders(PostgreSQL)

### 실행 방법 (개략)

```bash
# 1. 인프라 배포 (CDK)
cd infrastructure
cdk deploy

# 2. Jupyter Notebook 실행
jupyter notebook chaos-engineering-workflow.ipynb
```

Notebook 내에서:
1. 워크로드 태그 기반 리소스 탐색
2. 가설 생성 및 우선순위 결정
3. FIS 실험 설계 및 안전성 검증
4. 실험 실행 및 메트릭 수집
5. 결과 분석 및 개선안 도출

---

## 2. AWS Fault Isolation Boundaries

- **URL**: https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/abstract-and-introduction.html
- **발행일**: 2022년 11월 16일
- **유형**: AWS Whitepaper

### 개요

AWS의 장애 격리 경계(Fault Isolation Boundaries)에 대한 심층 가이드. AZ, 리전, 컨트롤 플레인, 데이터 플레인 등 다양한 격리 구조를 설명하고, 이를 활용한 고가용성/재해복구 아키텍처 설계 방법을 제시한다.

### 핵심 개념

#### 장애 격리 경계 유형

| 경계 유형 | 설명 | 격리 수준 |
|---|---|---|
| **Availability Zone (AZ)** | 독립 전력/냉각/네트워크를 가진 데이터센터 클러스터 | 물리적 인프라 장애 격리 |
| **Region** | 지리적으로 분리된 AZ 클러스터 | 자연재해/대규모 장애 격리 |
| **Control Plane** | 리소스 생성/변경/삭제 처리 (API) | 관리 작업 장애 격리 |
| **Data Plane** | 실제 데이터 처리/전달 | 런타임 장애 격리 |

#### 서비스 범위 (Service Scope)

| 범위 | 예시 | 장애 영향 범위 |
|---|---|---|
| **Zonal** | EC2 인스턴스, EBS 볼륨 | 단일 AZ |
| **Regional** | S3, DynamoDB, ALB | 단일 리전 |
| **Global** | Route 53, CloudFront, IAM | 글로벌 |

### 카오스 테스트에 적용할 핵심 원칙

#### 1. AZ 독립성 검증
```
실험: 단일 AZ의 모든 리소스 격리 (FIS: aws:ec2:terminate-instances)
검증: 나머지 AZ에서 서비스 정상 동작 확인
목표: AZ 장애 시 서비스 연속성 확보
```

#### 2. Control Plane vs Data Plane 분리
```
실험: Control Plane 장애 시뮬레이션
검증: 기존 실행 중인 워크로드(Data Plane)는 영향 없음 확인
교훈: 새 리소스 생성은 불가해도 기존 서비스는 계속 동작해야 함
```

#### 3. 정적 안정성 (Static Stability)
```
원칙: 장애 발생 시 스케일링 없이도 현재 트래픽 처리 가능해야 함
예시: 3AZ 배포 시 2AZ만으로도 전체 트래픽 수용 가능한 용량 확보
```

### Well-Architected Framework 연계

복원력 관련 6개 Pillar 중 **Reliability Pillar** 핵심 질문:
- 워크로드가 단일 AZ 손실을 견딜 수 있는가?
- 종속성의 장애 격리 경계를 이해하고 있는가?
- 컨트롤 플레인 종속성을 최소화했는가?

---

## 3. Resilience Analysis Framework

- **URL**: https://docs.aws.amazon.com/prescriptive-guidance/latest/resilience-analysis-framework/introduction.html
- **발행일**: 2023년 9월
- **저자**: John Formento, Bruno Emer, Steven Hooper, Jason Barto, Michael Haken (AWS)
- **유형**: AWS Prescriptive Guidance

### 개요

분산 시스템의 장애 모드를 일관되고 반복 가능한 방식으로 분석하는 프레임워크. 워크로드 설계부터 운영까지 전체 라이프사이클에 적용하여 복원력을 지속적으로 개선한다.

### 5대 복원력 속성 (Desired Properties)

| 속성 | 설명 | 위반 시 결과 |
|---|---|---|
| **Redundancy (중복성)** | 단일 장애점(SPOF) 제거를 위한 이중화 | 단일 컴포넌트 장애 → 시스템 중단 |
| **Sufficient Capacity (충분한 용량)** | 의도대로 기능하기 위한 충분한 리소스 | 리소스 고갈 → 서비스 불가 |
| **Timely Output (적시 응답)** | 합리적 시간 내 응답 | 지연 → 사용자 경험 저하 |
| **Correct Output (정확한 출력)** | 의도된 기능의 올바른 결과 | 오류 → 데이터 불일치 |
| **Fault Isolation (장애 격리)** | 의도된 컨테이너 내로 장애 범위 제한 | 장애 전파 → 연쇄 장애 |

### SEEMS 장애 분류 체계

| 분류 | 위반 속성 | 정의 |
|---|---|---|
| **S**ingle Points of Failure | Redundancy | 중복성 부재로 단일 컴포넌트 장애가 시스템을 중단시킴 |
| **E**xcessive Load | Sufficient Capacity | 과도한 수요로 리소스가 기능 수행 불가 (쓰로틀링, 요청 거부) |
| **E**xcessive Latency | Timely Output | 처리/네트워크 지연이 예상 시간 또는 SLO/SLA 초과 |
| **M**isconfiguration & Bugs | Correct Output | 소프트웨어 버그 또는 설정 오류로 잘못된 출력 |
| **S**hared Fate | Fault Isolation | 장애가 의도된 격리 경계를 넘어 다른 부분으로 전파 |

### 프레임워크 적용 질문 체크리스트

#### Single Points of Failure (SPOF)
- [ ] 컴포넌트가 중복성을 갖추고 있는가?
- [ ] 컴포넌트가 장애 시 무엇이 발생하는가?
- [ ] 단일 AZ의 부분/전체 손실을 견딜 수 있는가?

#### Excessive Latency (과도한 지연)
- [ ] 컴포넌트가 지연 증가를 경험하면 무엇이 발생하는가?
- [ ] 적절한 타임아웃과 재시도 전략이 있는가?
- [ ] Fast fail vs Slow fail - 연쇄 효과가 있는가?
- [ ] 가장 비용이 큰 요청은 무엇인가?

#### Excessive Load (과도한 부하)
- [ ] 무엇이 이 컴포넌트를 압도할 수 있는가?
- [ ] 성공하지 못할 작업에 리소스 낭비를 방지하는가?
- [ ] Circuit breaker가 구성되어 있는가?
- [ ] 극복할 수 없는 백로그가 생길 수 있는가?
- [ ] 어떤 한도/서비스 쿼터를 초과할 수 있는가?

#### Misconfiguration & Bugs (설정 오류/버그)
- [ ] 잘못된 설정/버그가 프로덕션에 배포되는 것을 방지하는가?
- [ ] 배포 롤백 또는 트래픽 전환이 자동으로 가능한가?
- [ ] 운영자 실수 방지를 위한 가드레일이 있는가?
- [ ] 만료될 수 있는 항목(인증서, 자격증명)은 무엇인가?

#### Shared Fate (공유 운명)
- [ ] 장애 격리 경계는 어디인가?
- [ ] 변경 사항이 격리 경계보다 작은 단위로 배포되는가?
- [ ] 이 컴포넌트가 다른 워크로드와 공유되는가?
- [ ] 어떤 컴포넌트가 이것과 밀접하게 결합되어 있는가?
- [ ] 부분적/회색 장애(gray failure) 시 무엇이 발생하는가?

### 완화 전략 평가 매트릭스

장애 모드를 식별한 후 각각에 대해 평가:

| 평가 항목 | 질문 |
|---|---|
| **영향도 (Impact)** | 이 장애가 발생하면 사용자에게 어떤 영향이 있는가? |
| **가능성 (Likelihood)** | 이 장애가 발생할 확률은 얼마나 되는가? |
| **탐지 가능성 (Detectability)** | 이 장애를 얼마나 빨리 탐지할 수 있는가? |
| **예방적 통제 (Preventive)** | 장애 발생을 사전에 방지할 수 있는 통제는? |
| **교정적 통제 (Corrective)** | 장애 발생 후 복구할 수 있는 통제는? |

### 반복적 개선 프로세스

```
┌─────────────────────────────────────────────────────┐
│  1. 워크로드 문서화 (아키텍처, 종속성, 사용자 스토리)  │
│                        ↓                             │
│  2. SEEMS 기반 질문으로 장애 모드 식별                │
│                        ↓                             │
│  3. 영향도/가능성 기반 우선순위 결정                   │
│                        ↓                             │
│  4. 완화 전략 수립 (예방적 + 교정적 통제)             │
│                        ↓                             │
│  5. 카오스 테스트로 검증                              │
│                        ↓                             │
│  6. 결과 반영 및 다음 반복 (주간/격주 주기 권장)       │
└─────────────────────────────────────────────────────┘
```

---

## 3개 문서의 관계와 활용 전략

### 문서 간 관계도

```
┌──────────────────────────────────┐
│  Resilience Analysis Framework   │  ← 무엇을 분석하고 어떤 질문을 할 것인가
│  (분석 방법론)                    │
└───────────────┬──────────────────┘
                │ 장애 모드 식별 → 가설 생성
                ▼
┌──────────────────────────────────┐
│  Fault Isolation Boundaries      │  ← AWS 인프라의 격리 경계를 이해
│  (인프라 이해)                    │
└───────────────┬──────────────────┘
                │ 격리 경계 기반 실험 설계
                ▼
┌──────────────────────────────────┐
│  Multi-Agent Chaos Engineering   │  ← AI로 자동화된 실험 실행
│  (자동화 실행)                    │
└──────────────────────────────────┘
```

### 우리 프로젝트에 적용하는 흐름

| 단계 | 참고 문서 | 활동 |
|---|---|---|
| **1단계** | Resilience Analysis Framework | SEEMS 체크리스트로 EKS 마이크로서비스의 장애 모드 식별 |
| **2단계** | Fault Isolation Boundaries | AZ/리전/컨트롤플레인 경계 관점에서 취약점 분류 |
| **3단계** | Multi-Agent Chaos Engineering | Strands Agents로 자동화된 가설 생성 → FIS 실험 → 결과 분석 |

### 즉시 활용 가능한 리소스

| 리소스 | URL | 용도 |
|---|---|---|
| Chaos Engineering Agents (코드) | https://github.com/aws-samples/sample-strands-chaos-engineering-agents | 포크 후 커스터마이징 |
| Retail Store Sample App | https://github.com/aws-containers/retail-store-sample-app | 테스트 대상 워크로드 |
| Strands Agents SDK | https://github.com/awslabs/strands | 에이전트 프레임워크 |
| AWS MCP Servers | https://github.com/awslabs/mcp | MCP 도구 통합 |
| AWS FIS Docs | https://docs.aws.amazon.com/fis/ | FIS 액션 레퍼런스 |
| Well-Architected Reliability Pillar | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/ | 아키텍처 검토 |

---

## 부록: AI 에이전트가 생성할 FIS 실험 유형 예시

### EKS 관련 FIS 액션

| FIS 액션 | 설명 | SEEMS 분류 |
|---|---|---|
| `aws:eks:pod-delete` | Pod 강제 종료 | SPOF |
| `aws:eks:pod-network-latency` | Pod 네트워크 지연 주입 | Excessive Latency |
| `aws:eks:pod-network-blackhole` | Pod 네트워크 차단 | SPOF, Shared Fate |
| `aws:eks:pod-cpu-stress` | Pod CPU 스트레스 | Excessive Load |
| `aws:eks:pod-memory-stress` | Pod 메모리 스트레스 | Excessive Load |
| `aws:eks:node-terminate` | 노드 종료 | SPOF, Shared Fate |

### RDS/Aurora 관련 FIS 액션

| FIS 액션 | 설명 | SEEMS 분류 |
|---|---|---|
| `aws:rds:failover-db-cluster` | DB 클러스터 페일오버 | SPOF |
| `aws:rds:reboot-db-instances` | DB 인스턴스 재부팅 | Excessive Latency |

### 네트워크 관련 FIS 액션

| FIS 액션 | 설명 | SEEMS 분류 |
|---|---|---|
| `aws:network:disrupt-connectivity` | 네트워크 연결 중단 | Shared Fate |
| `aws:network:route-table-disrupt-cross-region-connectivity` | 리전 간 연결 중단 | Shared Fate |
