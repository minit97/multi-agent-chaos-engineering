# Multi-Agent Chaos Engineering 파이프라인 분석 가이드

> `test.ipynb` 노트북을 주니어 레벨에서 이해할 수 있도록 분석한 문서입니다.

---

## 한 줄 요약

**AI 에이전트 5개가 릴레이하면서 EKS 클러스터에 "일부러 장애를 주입"하고, 시스템이 잘 버티는지 자동으로 검증하는 파이프라인**입니다.

---

## 목차

1. [이 코드가 뭘 하는 건가요?](#1-이-코드가-뭘-하는-건가요)
2. [사전 지식: 핵심 용어 정리](#2-사전-지식-핵심-용어-정리)
3. [전체 아키텍처](#3-전체-아키텍처)
4. [셀별 상세 분석](#4-셀별-상세-분석)
5. [에이전트 간 데이터 흐름](#5-에이전트-간-데이터-흐름)
6. [사용된 기술 스택](#6-사용된-기술-스택)
7. [실행하려면 뭐가 필요한가요?](#7-실행하려면-뭐가-필요한가요)
8. [자주 묻는 질문](#8-자주-묻는-질문)

---

## 1. 이 코드가 뭘 하는 건가요?

### 카오스 엔지니어링이란?

넷플릭스에서 시작된 개념으로, **"일부러 장애를 만들어서 시스템이 잘 버티는지 확인"** 하는 테스트 방법론입니다.

예를 들어:
- "주문 서비스 Pod을 삭제하면 어떻게 될까?" → 자동 복구되는지 확인
- "DB에 CPU 부하를 주면?" → 다른 서비스가 영향받는지 확인
- "네트워크를 끊으면?" → 타임아웃 처리가 제대로 되는지 확인

### 이 노트북의 접근 방식

보통 카오스 엔지니어링은 사람이 수동으로 "어디를 테스트할지" 결정하고, "어떻게 테스트할지" 설계합니다. 이 노트북은 **그 전 과정을 AI 에이전트에게 맡깁니다.**

```
사람이 하던 일                     이 노트북에서는
─────────────────                ──────────────────────
"어디가 약할까?" 고민    →    Agent 1이 자동으로 분석
"뭐부터 테스트하지?"     →    Agent 2가 우선순위 결정
"FIS 실험 어떻게 짜지?"  →    Agent 3이 자동 설계
"실행하고 모니터링"      →    Agent 4가 자동 실행
"결과 분석 및 보고서"    →    Agent 5가 자동 분석
```

---

## 2. 사전 지식: 핵심 용어 정리

| 용어 | 설명 |
|---|---|
| **Strands Agents SDK** | AWS가 만든 AI 에이전트 프레임워크. LLM에 도구(함수)를 줘서 자율적으로 작업하게 함 |
| **EKS** | AWS의 Kubernetes 관리 서비스. 컨테이너화된 앱을 실행하는 플랫폼 |
| **FIS** | AWS Fault Injection Service. AWS 리소스에 장애를 주입하는 서비스 |
| **Pod** | Kubernetes에서 실행되는 컨테이너의 최소 단위 |
| **Deployment** | Pod을 몇 개 유지할지 관리하는 Kubernetes 리소스 |
| **namespace** | Kubernetes에서 리소스를 논리적으로 구분하는 공간 (폴더 같은 것) |
| **@tool 데코레이터** | Strands에서 파이썬 함수를 에이전트가 쓸 수 있는 "도구"로 등록하는 문법 |
| **system_prompt** | 에이전트에게 "너는 ~~ 전문가야" 라고 역할을 부여하는 지시문 |
| **emptyDir** | Pod이 죽으면 데이터도 같이 사라지는 임시 저장소. 데이터 영속성 문제의 원인 |
| **blast radius** | 장애가 영향을 미치는 범위. 좁을수록 안전 |

---

## 3. 전체 아키텍처

### 파이프라인 흐름

```
┌─────────────────┐
│   Cell 0        │  환경 설정 (.env 로드, 자격 증명 확인)
└────────┬────────┘
         ▼
┌─────────────────┐
│   Cell 1        │  공통 도구 6개 정의 (AWS API 연동 함수들)
└────────┬────────┘
         ▼
┌─────────────────┐
│   Cell 2        │  Agent 1: 가설 생성
│   Hypothesis    │  "어디가 약한지?" → 가설 5개 생성
│   Generator     │  도구: discover_eks_resources, get_fis_actions, save_to_database
└────────┬────────┘
         ▼  (가설 목록을 다음 에이전트에 전달)
┌─────────────────┐
│   Cell 3        │  Agent 2: 우선순위 결정
│   Prioritization│  "뭐부터 테스트?" → 점수 매기고 순위 정렬
│   Agent         │  도구: save_to_database
└────────┬────────┘
         ▼  (순위 결과를 다음 에이전트에 전달)
┌─────────────────┐
│   Cell 4        │  Agent 3: 실험 설계
│   Experiment    │  "FIS 실험 어떻게 짤까?" → 실제 FIS 템플릿 생성
│   Design        │  도구: get_fis_actions, create_fis_experiment, save_to_database
└────────┬────────┘
         ▼  (FIS 템플릿 정보를 다음 에이전트에 전달)
┌─────────────────┐
│   Cell 5        │  Agent 4: 실험 실행
│   Experiment    │  "실행 + 모니터링" → FIS 실험 시작/상태 확인
│   Execution     │  도구: discover_eks_resources, run_fis_experiment,
│                 │        check_fis_experiment_status, save_to_database
└────────┬────────┘
         ▼  (실행 결과를 다음 에이전트에 전달)
┌─────────────────┐
│   Cell 6        │  Agent 5: 학습 및 분석
│   Learning &    │  "무엇을 배웠나?" → 취약점/개선안/다음 실험 제안
│   Iteration     │  도구: save_to_database
└────────┬────────┘
         ▼
┌─────────────────┐
│   Cell 7        │  요약 출력 + 토큰 사용량 리포트
└─────────────────┘
┌─────────────────┐
│   Cell 8        │  리소스 정리 가이드
└─────────────────┘
```

---

## 4. 셀별 상세 분석

### Cell 0: 환경 설정

```python
from dotenv import load_dotenv
load_dotenv()
```

**하는 일**: 프로젝트 루트의 `.env` 파일에서 환경 변수를 불러옵니다.

필요한 환경 변수:

| 변수명 | 용도 |
|---|---|
| `AWS_DEFAULT_REGION` | Bedrock API 호출 리전 (예: `us-east-1`) |
| `AWS_BEARER_TOKEN_BEDROCK` | Bedrock API Key (LLM 호출용) |
| `AWS_PROFILE_EKS` | EKS/FIS 접근용 AWS 프로파일 |
| `EKS_REGION` | EKS 클러스터가 있는 리전 |
| `EKS_CLUSTER_NAME` | 대상 EKS 클러스터 이름 |
| `FIS_ROLE_ARN` | FIS 실험 실행용 IAM Role ARN |

---

### Cell 1: 공통 도구 정의

이 셀이 가장 길고 중요합니다. **에이전트가 실제로 사용할 "손과 발"** 을 정의합니다.

#### LLM 모델 설정

```python
bedrock_model = OpenAIModel(
    client_args={
        "base_url": "https://bedrock-mantle.us-east-1.api.aws/v1",
        "api_key": os.getenv("AWS_BEARER_TOKEN_BEDROCK"),
    },
    model_id="qwen.qwen3-coder-30b-a3b-instruct"
)
```

주목할 점:
- `BedrockModel` 대신 `OpenAIModel`을 사용합니다
- Bedrock Mantle 엔드포인트를 거치면 OpenAI 호환 API로 Bedrock 모델을 호출할 수 있습니다
- 사용 모델은 Qwen3 Coder 30B (비교적 가벼운 모델)

#### 도구 6개 요약

| 도구 | 기능 | 사용하는 에이전트 |
|---|---|---|
| `discover_eks_resources` | `kubectl get all`로 Pod/Service/Deployment 현황 조회 | Agent 1, 4 |
| `get_fis_actions` | 사용 가능한 FIS 액션 목록 조회 (예: pod-delete, cpu-stress) | Agent 1, 3 |
| `create_fis_experiment` | FIS 실험 템플릿 생성 (실제 AWS API 호출) | Agent 3 |
| `run_fis_experiment` | FIS 실험 실행 (실제 장애 주입 시작) | Agent 4 |
| `check_fis_experiment_status` | 실행 중인 실험 상태 확인 | Agent 4 |
| `save_to_database` | 결과를 로컬 JSON 파일로 저장 (`output/` 폴더) | 모든 에이전트 |

#### @tool 데코레이터 작동 원리

```python
@tool
def discover_eks_resources(target_namespace: str = "retail-store") -> str:
    """EKS 클러스터의 리소스를 탐색합니다.
    Args:
        target_namespace: 탐색할 Kubernetes 네임스페이스
    """
```

- `@tool`: 이 함수를 Strands 에이전트가 사용할 수 있는 도구로 등록
- **docstring이 매우 중요**: LLM이 "이 도구가 뭘 하는지" 이해하는 데 docstring을 읽습니다
- **타입 힌트도 중요**: `target_namespace: str`로 LLM이 어떤 인자를 넘겨야 하는지 파악합니다
- **반환값은 항상 문자열**: LLM이 읽을 수 있어야 하므로 JSON 문자열로 반환

---

### Cell 2: Agent 1 - 가설 생성 에이전트

```python
hypothesis_agent = Agent(
    model=bedrock_model,                    # 어떤 LLM 사용
    system_prompt="당신은 카오스 엔지니어링 가설 생성 전문가...",  # 역할 부여
    tools=[discover_eks_resources, get_fis_actions, save_to_database],  # 사용 가능한 도구
    callback_handler=None                   # 스트리밍 출력 끄기
)
```

**이 에이전트가 하는 일:**

1. `discover_eks_resources` 도구로 EKS 클러스터 현황 파악
   - 어떤 Deployment가 있는지
   - 각 서비스의 레플리카 수는 몇 개인지
   - emptyDir 같은 위험 요소가 있는지
2. `get_fis_actions` 도구로 사용 가능한 FIS 액션 확인
3. 분석 결과를 바탕으로 가설 5개 생성
   - 형태: "만약 X가 발생하면 Y일 것이다"
   - 예: "만약 orders Pod을 삭제하면 30초 내 자동 복구될 것이다"
4. `save_to_database`로 결과 저장

**system_prompt에서 지정하는 장애 도메인 5가지:**
- 컴퓨트 (Pod 삭제, CPU 부하)
- 데이터 (emptyDir 데이터 유실)
- 네트워크 (네트워크 지연/차단)
- 종속성 (서비스 간 연쇄 장애)
- 리소스 (메모리/디스크 고갈)

---

### Cell 3: Agent 2 - 우선순위 결정 에이전트

**이 에이전트가 하는 일:**

Agent 1이 만든 가설들을 받아서 **"뭐부터 테스트할지"** 순서를 매깁니다.

점수 기준 (가중치):

| 기준 | 가중치 | 설명 |
|---|---|---|
| 영향도 (Impact) | 40% | 장애 시 비즈니스에 미치는 피해 |
| 가능성 (Likelihood) | 25% | 실제로 이 장애가 일어날 확률 |
| 안전성 (Safety) | 20% | 실험을 안전하게 실행할 수 있는지 |
| 학습 가치 (Learning Value) | 15% | 이 실험으로 얻을 수 있는 인사이트 |

**핵심 원칙: Safety-first** → 폭발 반경이 작고 롤백이 쉬운 실험이 먼저!

#### 에이전트 간 데이터 전달 방식

```python
hypothesis_output = hypothesis_result.message["content"][0]["text"]
```

Agent 1의 실행 결과에서 텍스트를 추출해서, Agent 2의 프롬프트에 문자열로 주입합니다. 에이전트끼리 직접 통신하는 게 아니라 **이전 결과를 다음 프롬프트에 붙여넣는 방식**입니다.

---

### Cell 4: Agent 3 - 실험 설계 에이전트

**이 에이전트가 하는 일:**

우선순위 상위 2개 가설을 **실제 AWS FIS 실험 템플릿으로 변환**합니다.

작업 순서:
1. `get_fis_actions`로 사용 가능한 EKS FIS 액션 확인
2. 안전 가드레일 5원칙 검증
3. `create_fis_experiment`로 **실제 FIS 템플릿 생성** (AWS API 호출!)

**안전 가드레일 5원칙:**

| 원칙 | 내용 |
|---|---|
| 1. 타깃 사전 검증 | 대상 리소스가 실제로 존재하는지 확인 |
| 2. 서비스별 안전 기준 | 최소 레플리카 수를 확인 (1개뿐이면 위험) |
| 3. 위험 액션 자동 배제 | 너무 위험한 액션은 차단 |
| 4. 폭발 반경 제어 | 한 번에 하나의 서비스만 타깃 |
| 5. 안전 우선 순위 배치 | 저위험 실험부터 순서대로 실행 |

---

### Cell 5: Agent 4 - 실험 실행 에이전트

**이 에이전트가 하는 일:**

설계된 FIS 실험을 **실제로 실행**하고 모니터링합니다.

실행 순서:
1. `discover_eks_resources` → 실행 **전** Pod 상태 기록 (비교 기준)
2. `run_fis_experiment` → FIS 실험 시작 (장애 주입!)
3. `check_fis_experiment_status` → 실험 진행 상태 확인
4. `discover_eks_resources` → 실행 **후** Pod 상태 확인 (복구 여부 체크)

**실행 전 체크리스트:**
- 타깃 리소스가 현재 존재하는가?
- 레플리카가 최소 2개 이상인가?
- 중단 조건(Stop Condition)이 설정되었는가?
- 롤백 계획이 명확한가?

---

### Cell 6: Agent 5 - 학습 및 분석 에이전트

**이 에이전트가 하는 일:**

모든 실험 결과를 종합 분석하여 **보고서를 작성**합니다.

분석 항목:
1. **발견된 취약점** → 심각도(HIGH/MEDIUM/LOW) 분류
2. **개선 권고사항** → 구체적인 해결 방법 제시
3. **복원력 성숙도 점수** → 1~10점 평가
4. **다음 실험 제안** → 이번에 못한 추가 테스트 제안
5. **아키텍처 개선안** → 구조적 변경 권고

---

### Cell 7: 요약 및 토큰 사용량

파이프라인 완료 후 각 에이전트별 토큰 사용량을 보여줍니다.

실제 실행 결과 예시:

| 에이전트 | 입력 토큰 | 출력 토큰 |
|---|---|---|
| Hypothesis Generator | 7,631 | 2,136 |
| Prioritization Agent | 3,684 | 1,088 |
| Experiment Design | 10,049 | 966 |
| Experiment Execution | 6,499 | 135 |
| Learning & Iteration | 2,565 | 885 |
| **합계** | **30,428** | **5,210** |
| **총 토큰** | **35,638** | |

전체 파이프라인이 약 3.5만 토큰으로 동작합니다.

---

### Cell 8: 리소스 정리

테스트 후 비용 절감을 위한 AWS 리소스 삭제 가이드입니다. EKS 클러스터, NAT Gateway 등은 시간당 과금되므로 테스트 후 반드시 정리해야 합니다.

---

## 5. 에이전트 간 데이터 흐름

```
Agent 1 (가설 생성)
  │
  │  hypothesis_result.message["content"][0]["text"]
  │  → 가설 5개 JSON
  ▼
Agent 2 (우선순위 결정)
  │
  │  priority_result.message["content"][0]["text"]
  │  → 점수 매기고 순위 정렬된 JSON
  ▼
Agent 3 (실험 설계)
  │
  │  design_result.message["content"][0]["text"]
  │  → FIS 실험 템플릿 ID + 설정 JSON
  ▼
Agent 4 (실험 실행)
  │
  │  execution_result.message["content"][0]["text"]
  │  → 실행 결과 + 전/후 상태 비교 JSON
  ▼
Agent 5 (학습 분석)
  │
  │  → 취약점/개선안/다음 실험 제안 JSON
  ▼
output/ 폴더에 모든 데이터 누적 저장
```

전달 방식은 **파이프라인 패턴** (이전 출력 → 다음 입력)이며, 각 에이전트는 독립적으로 실행됩니다. 공유 메모리나 메시지 큐 없이, 단순히 **이전 결과 문자열을 다음 프롬프트에 포함**시키는 방식입니다.

---

## 6. 사용된 기술 스택

| 기술 | 역할 | 왜 사용했는지 |
|---|---|---|
| **Strands Agents SDK** | AI 에이전트 프레임워크 | 도구 호출 + 자율 판단 루프 제공 |
| **Bedrock Mantle** | LLM 호출 엔드포인트 | OpenAI 호환 API로 Bedrock 모델 사용 |
| **Qwen3 Coder 30B** | LLM 모델 | 비교적 가벼우면서 코딩/분석 능력 보유 |
| **AWS FIS** | 장애 주입 서비스 | Pod 삭제, CPU 스트레스 등 실제 장애 시뮬레이션 |
| **AWS EKS** | Kubernetes 클러스터 | 테스트 대상 워크로드 실행 환경 |
| **boto3** | AWS SDK for Python | FIS/EKS API 호출 |
| **kubectl** | Kubernetes CLI | Pod/Service 현황 조회 |
| **python-dotenv** | 환경 변수 관리 | `.env` 파일에서 시크릿 로드 |

---

## 7. 실행하려면 뭐가 필요한가요?

### 필수 요건

1. **Python 3.10+** 및 패키지 설치:
   ```bash
   pip install strands-agents python-dotenv boto3
   ```

2. **`.env` 파일** (프로젝트 루트):
   ```
   AWS_BEARER_TOKEN_BEDROCK=발급받은_Bedrock_API_키
   AWS_DEFAULT_REGION=us-east-1
   AWS_PROFILE_EKS=your-aws-profile
   EKS_REGION=ap-northeast-2
   EKS_CLUSTER_NAME=your-cluster-name
   EKS_NAMESPACE=retail-store
   FIS_ROLE_ARN=arn:aws:iam::ACCOUNT_ID:role/ChaosAgentFISRole
   ```

3. **AWS 리소스** (실제 실행 시):
   - EKS 클러스터 (워크로드 배포된 상태)
   - FIS IAM Role (`ChaosAgentFISRole`)
   - kubectl이 클러스터에 연결된 상태

### 비용 참고

| 항목 | 대략적 비용 |
|---|---|
| Bedrock LLM 호출 (3.5만 토큰) | 거의 무시할 수준 |
| EKS 클러스터 | ~$0.10/시간 (클러스터) + EC2 노드 비용 |
| FIS 실험 | 무료 (실험 자체에는 비용 없음) |
| NAT Gateway | ~$0.045/시간 + 데이터 전송 |

테스트 후 EKS 클러스터와 NAT Gateway는 반드시 삭제하세요!

---

## 8. 자주 묻는 질문

### Q: 에이전트가 "자율적으로" 도구를 쓴다는 게 무슨 말인가요?

코드에서 "이 도구를 써라"고 직접 호출하지 않습니다. 에이전트(LLM)가 프롬프트를 읽고 **스스로 판단해서** 어떤 도구를 언제 사용할지 결정합니다. 예를 들어 Agent 1에게 "리소스를 분석해줘"라고 하면, LLM이 `discover_eks_resources`를 호출하기로 결정하고, 결과를 보고 `get_fis_actions`도 호출할지 결정합니다.

### Q: 왜 BedrockModel 대신 OpenAIModel을 쓰나요?

Bedrock Mantle이라는 엔드포인트를 사용하면, Bedrock의 모든 모델을 **OpenAI 호환 API** 형태로 호출할 수 있습니다. Qwen 같은 일부 모델은 이 방식이 더 잘 맞을 수 있고, Bedrock API Key(Bearer Token)와도 바로 호환됩니다.

### Q: 에이전트 5개를 꼭 따로 만들어야 하나요? 1개로 안 되나요?

기술적으로는 1개로도 가능하지만, 분리하는 이유가 있습니다:

- **역할 분리**: 각 에이전트의 system_prompt가 짧고 명확해짐
- **디버깅 용이**: 어떤 단계에서 문제가 생겼는지 바로 파악 가능
- **유연한 교체**: 특정 에이전트만 다른 모델로 교체 가능
- **토큰 효율성**: 컨텍스트 윈도우를 낭비하지 않음

### Q: `callback_handler=None`은 왜 설정하나요?

기본값으로 Strands는 LLM 응답을 스트리밍으로 출력합니다. `None`으로 설정하면 중간 출력 없이 최종 결과만 받습니다. 노트북에서 깔끔하게 실행하려면 이 설정이 유용합니다.

### Q: `save_to_database`가 진짜 DB가 아니라 JSON 파일인데요?

맞습니다. 이 예제에서는 간단하게 로컬 `output/` 폴더에 JSON 파일로 저장합니다. 프로덕션에서는 DynamoDB나 RDS 등 실제 DB로 교체할 수 있습니다. 도구의 내부 구현만 바꾸면 에이전트 코드는 수정할 필요 없습니다.

### Q: 실제로 장애가 주입되나요? 위험하지 않나요?

현재 Cell 5는 **Pre-flight Validation (사전 검증) 모드**로 동작합니다. 실제 FIS 실험을 실행하지 않고, 타깃 리소스의 존재 여부와 상태만 확인합니다. 실제 장애 주입을 하려면 별도로 FIS 콘솔에서 실험을 시작해야 합니다.

안전하게 사용하려면:
- 테스트 전용 EKS 클러스터에서만 실행
- FIS 실험 템플릿에 stop condition 설정
- 중요 서비스가 없는 네임스페이스에서만 테스트

---

## 9. 에이전트가 아키텍처를 파악하는 방법

에이전트는 미리 아키텍처를 아는 것이 아니라, **매번 실시간으로 클러스터를 조회**해서 파악합니다.

### 동작 흐름

```
에이전트가 discover_eks_resources("retail-store") 호출
        ↓
내부적으로 kubectl get all -n retail-store -o json 실행
        ↓
실제 클러스터에서 응답:
  - Deployments: carts, catalog, checkout, orders, ui
  - StatefulSets: catalog-mysql, orders-postgresql, orders-rabbitmq
  - Pods: 10개 (각각 Running 상태)
  - Services: 각 서비스의 ClusterIP
        ↓
JSON으로 정리해서 에이전트에게 반환
        ↓
에이전트(LLM)가 이 정보를 보고 추론:
  - "catalog과 catalog-mysql이 있으니 DB 종속성이 있겠군"
  - "orders-postgresql은 PVC가 있으니 영속 스토리지를 쓰는구나"
  - "checkout-redis는 레플리카 1개뿐이니 SPOF 위험이 있겠다"
```

### 알 수 있는 것 vs 추론하는 것

| 확정적으로 아는 것 (API 응답) | 추론하는 것 (LLM 판단) |
|---|---|
| Pod 이름, 상태 (Running/Pending) | 서비스 간 종속성 관계 |
| 레플리카 수 | 장애 시 영향 범위 |
| StatefulSet의 volumeClaimTemplates 유무 | 데이터 영속성 위험도 |
| 라벨 (app.kubernetes.io/name=xxx) | 비즈니스 중요도 |
| 서비스 타입 (ClusterIP/LoadBalancer) | 사용자 영향도 |

### 한계

- 서비스 간 **네트워크 호출 관계**는 Pod 이름/라벨에서 추론할 뿐 확정적으로 알지 못함
- 소스 코드를 분석하지 않으므로 **내부 로직**은 모름
- 원본 레포(`sample-strands-chaos-engineering-agents`)에서는 소스 코드 레포까지 분석하여 종속성을 더 정확하게 파악

### 더 정확한 분석을 위한 확장 방법

1. **소스 코드 분석 도구 추가**: 서비스 코드에서 다른 서비스를 호출하는 부분을 탐색
2. **Service Mesh(Istio) 연동**: 실제 트래픽 흐름 기반으로 종속성 맵 구축
3. **CloudWatch/X-Ray 연동**: 분산 트레이싱 데이터로 호출 관계 확인
4. **태그 기반 메타데이터**: 워크로드 태그에 종속성 정보를 명시

---

## 10. EKS Auto Mode에서의 제약사항

현재 클러스터(`<YOUR_CLUSTER_NAME>`)는 EKS Auto Mode로 생성되어 다음 제약이 있습니다:

| 항목 | 일반 EKS | EKS Auto Mode (현재) |
|---|---|---|
| 노드 관리 | Managed Node Group | Karpenter NodePool |
| FIS Pod 액션 (pod-delete 등) | addon 설치 후 사용 가능 | ❌ Pod Identity Agent 미동작 |
| FIS 노드 종료 | terminate-nodegroup-instances | ❌ Nodegroup 없음 |
| EC2 인스턴스 종료 | ec2:terminate-instances | ✅ 가능 (직접 인스턴스 타깃) |

### 현재 채택한 접근

- Cell 4: FIS 실험 템플릿은 정상 생성됨 (AWS 콘솔에서 확인 가능)
- Cell 5: FIS 실행 대신 **Pre-flight Validation**으로 타깃 상태만 검증
- 실제 장애 주입은 `aws:ec2:terminate-instances`로 노드 레벨에서 가능

### FIS Pod 액션을 사용하려면

EKS를 일반 모드(Managed Node Group)로 재생성하면 Pod 수준 장애 주입이 가능합니다:
```bash
eksctl create cluster --name chaos-cluster --region ap-northeast-2 \
  --nodegroup-name workers --node-type t3.medium --nodes 3 --managed
```
