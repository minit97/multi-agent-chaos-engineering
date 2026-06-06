# V1: Multi-Agent Chaos Engineering 구현

> 5-Agent 아키텍처 기반 AI 복원력 테스트 파이프라인 (Mock 버전)

---

## 개요

| 항목 | 내용 |
|---|---|
| **버전** | v1 (Mock 도구 기반 시연) |
| **파일** | `test.ipynb` |
| **참조 레포** | https://github.com/aws-samples/sample-strands-chaos-engineering-agents |
| **프레임워크** | Strands Agents SDK |
| **모델** | Amazon Bedrock (Bearer Token 인증, us-east-1) |
| **상태** | 파이프라인 구조 검증 완료, 실제 AWS 연동 전 |

---

## 파이프라인 구조

```
┌────────────┐     ┌────────────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐
│  Agent 1   │────▶│    Agent 2     │────▶│   Agent 3    │────▶│  Agent 4   │────▶│   Agent 5    │
│ Hypothesis │     │ Prioritization │     │  Experiment  │     │ Execution  │     │  Learning &  │
│ Generator  │     │    Agent       │     │   Design     │     │   Agent    │     │  Iteration   │
└────────────┘     └────────────────┘     └──────────────┘     └────────────┘     └──────────────┘
     │                    │                      │                    │                    │
     └────────────────────┴──────────────────────┴────────────────────┴────────────────────┘
                                            [Database]
```

---

## 각 Cell 설명

### Cell 0: 환경 설정 확인

```python
from dotenv import load_dotenv
load_dotenv()
```

- `.env` 파일에서 `AWS_DEFAULT_REGION`, `AWS_BEARER_TOKEN_BEDROCK` 로드
- Bedrock 연결 정상 여부 확인

### Cell 1: 공통 도구 정의 (Mock)

4개의 시뮬레이션 도구:

| 도구 | 역할 | 실제 전환 시 |
|---|---|---|
| `discover_eks_resources` | EKS 클러스터 리소스 탐색 | boto3 EKS + kubectl |
| `get_fis_actions` | FIS 사용 가능 액션 조회 | `boto3 fis.list_actions()` |
| `save_to_database` | 실험 데이터 DB 저장 | pymysql (Aurora) 또는 DynamoDB |
| `execute_fis_experiment` | FIS 실험 실행 | `boto3 fis.start_experiment()` |

Mock 데이터로 반환하는 워크로드 구성:
- UI Service (2 replicas)
- Catalog Service → MySQL (emptyDir, 비영속)
- Cart Service → DynamoDB
- Checkout Service → Redis, RabbitMQ (각 1 replica)
- Orders Service → PostgreSQL (PVC, 영속)

### Cell 2: Agent 1 - Hypothesis Generator

**역할**: 워크로드 분석 → 장애 가설 5개 생성

**사용 도구**: `discover_eks_resources`, `save_to_database`

**출력 구조**:
```json
{
  "hypotheses": [
    {
      "id": "H-001",
      "title": "가설 제목",
      "service": "대상 서비스",
      "failure_domain": "컴퓨트|데이터|네트워크|종속성|리소스",
      "hypothesis": "만약 X하면 Y할 것이다",
      "blast_radius": "예상 영향 범위"
    }
  ]
}
```

**주목 포인트**:
- emptyDir 사용 DB의 데이터 영속성
- 단일 레플리카 서비스 가용성
- 서비스 간 종속성 체인

### Cell 3: Agent 2 - Prioritization Agent

**역할**: 가설 우선순위 결정 (Safety-first)

**사용 도구**: `save_to_database`

**점수 기준** (가중치):
| 기준 | 가중치 | 설명 |
|---|---|---|
| Impact | 40% | 비즈니스 영향도 |
| Likelihood | 25% | 실제 발생 가능성 |
| Safety | 20% | 안전한 실행 가능성 (안전할수록 높은 순위) |
| Learning Value | 15% | 얻을 수 있는 인사이트 |

**핵심 원칙**: 폭발 반경이 작고 롤백이 명확한 실험 → 높은 우선순위

### Cell 4: Agent 3 - Experiment Design Agent

**역할**: 가설 → AWS FIS 실험 템플릿 변환

**사용 도구**: `get_fis_actions`, `save_to_database`

**안전 가드레일 5원칙 적용**:
1. 타깃 사전 검증 (리소스 존재 확인)
2. 서비스별 안전 기준 (최소 레플리카 수)
3. 위험 액션 자동 배제 (zonal-autoshift 등)
4. 폭발 반경 제어 (단일 서비스만 타깃)
5. 안전 우선 순위 배치

**출력**: FIS 실험 템플릿 (액션, 타깃, Stop Condition, 안전 검증 포함)

### Cell 5: Agent 4 - Experiment Execution Agent

**역할**: FIS 실험 실행 + 모니터링

**사용 도구**: `discover_eks_resources`, `execute_fis_experiment`, `save_to_database`

**실행 전 체크리스트**:
- [ ] 타깃 리소스 현재 존재 확인
- [ ] 레플리카 수 >= 2 확인
- [ ] Stop Condition 설정 확인
- [ ] 롤백 계획 확인
- [ ] dry_run 먼저 실행

**현재 상태**: `dry_run=True` (실제 장애 주입 없이 검증만)

### Cell 6: Agent 5 - Learning & Iteration Agent

**역할**: 결과 분석 → 취약점 식별 → 개선안 도출

**사용 도구**: `save_to_database`

**분석 관점**:
- 발견된 취약점 + 심각도 (HIGH/MEDIUM/LOW)
- 구체적 개선 권고사항 + 예상 노력
- 복원력 성숙도 점수 (1-10)
- 다음 반복 실험 제안
- 아키텍처 수준 개선 권고

### Cell 7: 파이프라인 요약

- 전체 실행 흐름 시각화
- 에이전트별 토큰 사용량 집계

### Cell 8: AWS 세팅 가이드

실제 FIS 실험 실행을 위해 필요한 AWS 설정 안내.

---

## 현재 환경 상태

| 항목 | 상태 | 비고 |
|---|---|---|
| Bedrock 접근 | ✅ 완료 | Bearer Token 인증 |
| 리전 설정 | ✅ 완료 | us-east-1 |
| Strands SDK | ✅ 완료 | Agent 정상 동작 확인 |
| FIS IAM Role | ❌ 미설정 | `ChaosAgentFISRole` 생성 필요 |
| FIS 권한 | ❌ 미설정 | 사용자에게 fis:* 권한 추가 필요 |
| EKS 클러스터 | ❌ 미배포 | 테스트 워크로드 배포 필요 |
| EKS FIS Addon | ❌ 미설치 | `aws-fis-pod-action` 설치 필요 |
| Aurora DB | ❌ 미배포 | 선택사항 (DynamoDB 대체 가능) |

---

## V2 로드맵

### Phase 1: AWS 인프라 세팅
- [ ] FIS IAM Role 생성 (`ChaosAgentFISRole`)
- [ ] 사용자 IAM 정책에 FIS/EKS 권한 추가
- [ ] EKS 클러스터 생성 또는 기존 클러스터 활용
- [ ] EKS FIS Addon 설치 (`aws-fis-pod-action`)

### Phase 2: 테스트 워크로드 배포
- [ ] [Retail Store Sample App](https://github.com/aws-containers/retail-store-sample-app) EKS 버전 배포
- [ ] 워크로드 태그 설정 (`Environment=test, Application=retail-store`)

### Phase 3: Mock → 실제 도구 전환
- [ ] `discover_eks_resources` → boto3 EKS API 호출
- [ ] `get_fis_actions` → `boto3.client('fis').list_actions()`
- [ ] `save_to_database` → DynamoDB 또는 Aurora 연동
- [ ] `execute_fis_experiment` → `boto3.client('fis').start_experiment()`

### Phase 4: 실제 실험 실행
- [ ] `dry_run=False`로 전환
- [ ] CloudWatch 알람 기반 Stop Condition 설정
- [ ] 실험 결과 모니터링 대시보드 구성

### Phase 5: 자동화 및 CI/CD 통합
- [ ] 워크플로우 오케스트레이터 구현 (GraphBuilder 활용)
- [ ] 정기 실행 스케줄러 (EventBridge)
- [ ] Slack/Teams 알림 연동

---

## 참고 자료

| 자료 | URL |
|---|---|
| 원본 레포 | https://github.com/aws-samples/sample-strands-chaos-engineering-agents |
| Retail Store App | https://github.com/aws-containers/retail-store-sample-app |
| Strands Agents SDK | https://strandsagents.com/ |
| AWS FIS 문서 | https://docs.aws.amazon.com/fis/ |
| Resilience Analysis Framework | https://docs.aws.amazon.com/prescriptive-guidance/latest/resilience-analysis-framework/ |
| Fault Isolation Boundaries | https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/ |
