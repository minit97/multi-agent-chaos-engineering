# Strands Agents SDK 사용 가이드

> 공식 문서: https://strandsagents.com/docs/user-guide/quickstart/overview/

Strands Agents SDK는 AI 에이전트를 빠르게 빌드, 관리, 평가, 배포할 수 있는 오픈소스 SDK이다. Python과 TypeScript를 지원한다.

---

## 목차

1. [설치 및 빠른 시작](#1-설치-및-빠른-시작)
2. [핵심 개념: Agent Loop](#2-핵심-개념-agent-loop)
3. [모델 프로바이더](#3-모델-프로바이더)
4. [도구 (Tools)](#4-도구-tools)
5. [MCP (Model Context Protocol) 도구](#5-mcp-model-context-protocol-도구)
6. [Structured Output](#6-structured-output)
7. [스트리밍](#7-스트리밍)
8. [상태 관리 (State Management)](#8-상태-관리-state-management)
9. [세션 관리 (Session Management)](#9-세션-관리-session-management)
10. [대화 관리 (Conversation Management)](#10-대화-관리-conversation-management)
11. [Hooks & Plugins](#11-hooks--plugins)
12. [멀티 에이전트 시스템](#12-멀티-에이전트-시스템)
13. [Observability](#13-observability)
14. [배포](#14-배포)

---

## 1. 설치 및 빠른 시작

### 설치

```bash
# 기본 설치
pip install strands-agents

# 특정 모델 프로바이더 포함
pip install 'strands-agents[bedrock]'
pip install 'strands-agents[openai]'
pip install 'strands-agents[anthropic]'

# 모든 프로바이더 포함
pip install 'strands-agents[all]'
```

### 최소 예제

```python
from strands import Agent

agent = Agent()
agent("안녕하세요, 무엇을 도와드릴까요?")
```

### 도구가 포함된 예제

```python
from strands import Agent, tool

@tool
def weather_forecast(city: str, days: int = 3) -> str:
    """도시의 날씨 예보를 가져옵니다.
    Args:
        city: 도시 이름
        days: 예보 일수
    """
    return f"{city}의 향후 {days}일 날씨 예보..."

agent = Agent(tools=[weather_forecast])
agent("서울 날씨 알려줘")
```

---

## 2. 핵심 개념: Agent Loop

Agent Loop는 Strands의 핵심 실행 원리이다. 모델을 호출하고, 도구 사용 여부를 확인하고, 도구를 실행한 후 결과를 다시 모델에 전달하는 순환 구조로 동작한다.

```
[입력] → [추론(LLM)] → [도구 선택] → [도구 실행] → [추론(LLM)] → ... → [최종 응답]
```

### 동작 원리

1. 사용자 요청 수신
2. 모델이 요청 분석 후 도구 호출 또는 응답 생성 결정
3. 도구 호출 시: 도구 실행 → 결과를 대화 이력에 추가 → 모델 재호출
4. 최종 응답 시: 루프 종료 및 결과 반환

### Stop Reasons (종료 사유)

| Stop Reason | 설명 |
|---|---|
| `end_turn` | 정상 종료, 최종 응답 생성 완료 |
| `tool_use` | 도구 실행 필요 (루프 계속) |
| `cancelled` | `agent.cancel()`에 의한 외부 취소 |
| `max_tokens` | 토큰 제한 초과 |
| `stop_sequence` | 설정된 중단 시퀀스 감지 |
| `content_filtered` | 안전 메커니즘에 의한 차단 |

### 취소 (Cancellation)

```python
import threading
import time
from strands import Agent

def timeout_watchdog(agent: Agent, timeout: float) -> None:
    time.sleep(timeout)
    agent.cancel()

agent = Agent()
watchdog = threading.Thread(target=timeout_watchdog, args=(agent, 30.0))
watchdog.start()

result = agent("대규모 데이터 분석")
if result.stop_reason == "cancelled":
    print("타임아웃으로 에이전트 취소됨")
```

---

## 3. 모델 프로바이더

Strands는 다양한 모델 프로바이더를 통합 인터페이스로 지원한다.

### 지원 프로바이더

| 프로바이더 | Python | TypeScript |
|---|---|---|
| Amazon Bedrock | ✅ | ✅ |
| OpenAI | ✅ | ✅ |
| Anthropic | ✅ | ✅ |
| Google | ✅ | ✅ |
| Ollama | ✅ | ❌ |
| LiteLLM | ✅ | ❌ |
| llama.cpp | ✅ | ❌ |
| MistralAI | ✅ | ❌ |
| SageMaker | ✅ | ❌ |

### 사용 예시

```python
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.models.openai import OpenAIModel

# Bedrock 사용
bedrock_model = BedrockModel(model_id="anthropic.claude-sonnet-4-20250514-v1:0")
agent = Agent(model=bedrock_model)

# OpenAI 사용 (모델만 교체하면 됨)
openai_model = OpenAIModel(
    client_args={"api_key": "<KEY>"},
    model_id="gpt-4o"
)
agent = Agent(model=openai_model)
```

---

## 4. 도구 (Tools)

### 4.1 함수 데코레이터 방식 (권장)

```python
from strands import tool

@tool
def calculate_area(shape: str, radius: float = None) -> float:
    """도형의 넓이를 계산합니다.
    Args:
        shape: 도형 종류 (circle, rectangle)
        radius: 원의 반지름
    """
    if shape == "circle":
        return 3.14159 * radius ** 2
    return 0.0
```

### 4.2 이름/설명 오버라이드

```python
@tool(name="get_weather", description="지정된 위치의 날씨 예보를 가져옵니다")
def weather_forecast(city: str, days: int = 3) -> str:
    """날씨 예보 구현."""
    return f"{city}의 향후 {days}일 날씨 예보..."
```

### 4.3 비동기 도구

```python
import asyncio
from strands import Agent, tool

@tool
async def call_api() -> str:
    """비동기 API 호출."""
    await asyncio.sleep(5)
    return "API 결과"

async def main():
    agent = Agent(tools=[call_api])
    await agent.invoke_async("API를 호출해줘")

asyncio.run(main())
```

### 4.4 ToolContext (실행 컨텍스트 접근)

```python
from strands import tool, Agent, ToolContext

@tool(context=True)
def get_self_name(tool_context: ToolContext) -> str:
    return f"에이전트 이름: {tool_context.agent.name}"

agent = Agent(tools=[get_self_name], name="MyAgent")
agent("너의 이름이 뭐야?")
```

### 4.5 클래스 기반 도구

```python
from strands import Agent, tool

class DatabaseTools:
    def __init__(self, connection_string):
        self.connection = self._connect(connection_string)

    def _connect(self, conn_str):
        return {"connected": True}

    @tool
    def query_database(self, sql: str) -> dict:
        """SQL 쿼리를 실행합니다.
        Args:
            sql: 실행할 SQL 쿼리
        """
        return {"results": f"쿼리 결과: {sql}"}

db_tools = DatabaseTools("connection_string")
agent = Agent(tools=[db_tools.query_database])
```

### 4.6 도구 스트리밍 (중간 결과 전송)

```python
from strands import tool

@tool
async def process_dataset(records: int) -> str:
    """레코드를 처리하며 진행 상황을 업데이트합니다."""
    for i in range(records):
        await asyncio.sleep(0.1)
        if i % 10 == 0:
            yield f"처리 중: {i}/{records}"
    yield f"완료: {records}건 처리됨"
```

---

## 5. MCP (Model Context Protocol) 도구

MCP는 외부 도구 서버와 통신하는 표준 프로토콜이다.

### 기본 사용법

```python
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.tools.mcp import MCPClient

mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="uvx",
        args=["awslabs.aws-documentation-mcp-server@latest"]
    )
))

# 자동 라이프사이클 관리 (권장)
agent = Agent(tools=[mcp_client])
agent("AWS Lambda란 무엇인가요?")
```

### 수동 컨텍스트 관리

```python
with mcp_client:
    tools = mcp_client.list_tools_sync()
    agent = Agent(tools=tools)
    agent("AWS Lambda란?")
```

### 전송 방식 (Transport)

#### stdio (로컬 프로세스)

```python
from mcp import stdio_client, StdioServerParameters

mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(command="uvx", args=["server@latest"])
))
```

#### Streamable HTTP

```python
from mcp.client.streamable_http import streamablehttp_client

mcp_client = MCPClient(
    lambda: streamablehttp_client("http://localhost:8000/mcp")
)
```

#### SSE (Server-Sent Events)

```python
from mcp.client.sse import sse_client

mcp_client = MCPClient(lambda: sse_client("http://localhost:8000/sse"))
```

### 다수의 MCP 서버 사용

```python
agent = Agent(tools=[sse_mcp_client, stdio_mcp_client])
```

### 도구 필터링 및 네임스페이스

```python
# 특정 도구만 로드
filtered_client = MCPClient(
    lambda: stdio_client(...),
    tool_filters={"allowed": ["search_documentation"]}
)

# 접두사로 충돌 방지
aws_client = MCPClient(lambda: stdio_client(...), prefix="aws_docs")
```

### MCP 서버 구현

```python
from mcp.server import FastMCP

mcp = FastMCP("Calculator Server")

@mcp.tool(description="계산기 도구")
def calculator(x: int, y: int) -> int:
    return x + y

mcp.run(transport="sse")
```

---

## 6. Structured Output

스키마 정의를 통해 타입 안전한 구조화된 응답을 받을 수 있다.

### 기본 사용법

```python
from pydantic import BaseModel, Field
from strands import Agent

class PersonInfo(BaseModel):
    name: str = Field(description="이름")
    age: int = Field(description="나이")
    occupation: str = Field(description="직업")

agent = Agent()
result = agent(
    "김철수는 30세 소프트웨어 엔지니어입니다",
    structured_output_model=PersonInfo
)

person = result.structured_output
print(f"이름: {person.name}")       # "김철수"
print(f"나이: {person.age}")        # 30
print(f"직업: {person.occupation}") # "소프트웨어 엔지니어"
```

### 도구와 결합

```python
from strands import Agent
from strands_tools import calculator
from pydantic import BaseModel, Field

class MathResult(BaseModel):
    operation: str = Field(description="수행된 연산")
    result: int = Field(description="연산 결과")

agent = Agent(tools=[calculator])
res = agent("42 + 8은?", structured_output_model=MathResult)
```

### 에이전트 레벨 기본값

```python
agent = Agent(structured_output_model=PersonInfo)
result = agent("김철수는 30세 소프트웨어 엔지니어입니다")
```

---

## 7. 스트리밍

### Async Iterator 방식

```python
import asyncio
from strands import Agent

agent = Agent(callback_handler=None)

async def stream_response():
    async for event in agent.stream_async("2+2를 계산해줘"):
        if "data" in event:
            print(event["data"], end="")
        elif "result" in event:
            print("\n완료!")

asyncio.run(stream_response())
```

### FastAPI 연동

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from strands import Agent

app = FastAPI()

@app.post("/stream")
async def stream_response(prompt: str):
    async def generate():
        agent = Agent(callback_handler=None)
        async for event in agent.stream_async(prompt):
            if "data" in event:
                yield event["data"]

    return StreamingResponse(generate(), media_type="text/plain")
```

### 이벤트 종류

| 이벤트 | 설명 |
|---|---|
| `init_event_loop` | 이벤트 루프 초기화 |
| `start_event_loop` | 이벤트 루프 사이클 시작 |
| `data` | 텍스트 청크 생성 |
| `current_tool_use` | 도구 사용 중 |
| `message` | 새 메시지 생성 |
| `result` | 에이전트 실행 완료 |
| `force_stop` | 강제 종료 |

---

## 8. 상태 관리 (State Management)

Strands는 3가지 형태의 상태를 유지한다.

### 8.1 대화 이력 (Conversation History)

```python
from strands import Agent

agent = Agent()
agent("안녕!")

# 대화 이력 접근
print(agent.messages)

# 기존 메시지로 에이전트 초기화
agent = Agent(messages=[
    {"role": "user", "content": [{"text": "내 이름은 철수야"}]},
    {"role": "assistant", "content": [{"text": "안녕하세요 철수님!"}]}
])
```

### 8.2 에이전트 상태 (Agent State)

대화 컨텍스트 외부의 키-값 저장소. 모델에 전달되지 않지만 도구와 앱 로직에서 접근 가능.

```python
from strands import Agent

agent = Agent(state={"user_preferences": {"theme": "dark"}, "session_count": 0})

# 상태 접근 및 수정
agent.state.get("user_preferences")  # {"theme": "dark"}
agent.state.set("last_action", "login")
agent.state.delete("last_action")
```

### 8.3 호출 상태 (Invocation State)

단일 호출 내에서 유지되는 컨텍스트. 도구에서 `tool_context.invocation_state`로 접근.

```python
from strands import Agent, tool, ToolContext

@tool(context=True)
def api_call(query: str, tool_context: ToolContext) -> dict:
    """사용자 컨텍스트를 활용한 API 호출.
    Args:
        query: 검색 쿼리
    """
    user_id = tool_context.invocation_state.get("user_id")
    return {"user_id": user_id, "query": query}

agent = Agent(tools=[api_call])
result = agent("내 프로필 조회", user_id="user123")
```

---

## 9. 세션 관리 (Session Management)

에이전트 상태와 대화 이력을 영속적으로 저장/복원.

### FileSessionManager

```python
from strands import Agent
from strands.session.file_session_manager import FileSessionManager

session_manager = FileSessionManager(
    session_id="test-session",
    storage_dir="/path/to/sessions"
)

agent = Agent(session_manager=session_manager)
agent("안녕!")  # 자동으로 세션에 저장됨
```

### S3SessionManager

```python
from strands.session.s3_session_manager import S3SessionManager

session_manager = S3SessionManager(
    session_id="user-456",
    bucket="my-agent-sessions",
    prefix="production/",
    region_name="us-west-2"
)

agent = Agent(session_manager=session_manager)
```

### 커스텀 세션 저장소

`SessionRepository` 인터페이스를 구현하여 어떤 백엔드든 사용 가능:

```python
from strands.session.session_repository import SessionRepository
from strands.session.repository_session_manager import RepositorySessionManager

class CustomSessionRepository(SessionRepository):
    def create_session(self, session): ...
    def read_session(self, session_id): ...
    # ... 기타 메서드 구현

custom_repo = CustomSessionRepository()
session_manager = RepositorySessionManager(
    session_id="user-789",
    session_repository=custom_repo
)
```

---

## 10. 대화 관리 (Conversation Management)

토큰 제한 내에서 대화 이력을 효율적으로 관리하는 전략.

### NullConversationManager

대화 이력을 수정하지 않음. 짧은 대화나 디버깅에 적합.

### SlidingWindowConversationManager (기본값)

```python
from strands import Agent
from strands.agent.conversation_manager import SlidingWindowConversationManager

conversation_manager = SlidingWindowConversationManager(
    window_size=40,
    should_truncate_results=True
)
agent = Agent(conversation_manager=conversation_manager)
```

**주요 기능:**
- 최근 N개 메시지 유지
- 도구 결과 자동 축약
- 컨텍스트 윈도우 초과 시 오래된 메시지 제거
- `per_turn` 파라미터로 매 턴마다 관리 가능

### SummarizingConversationManager

오래된 메시지를 요약하여 보존:

```python
from strands import Agent
from strands.agent.conversation_manager import SummarizingConversationManager

conversation_manager = SummarizingConversationManager(
    summary_ratio=0.3,
    preserve_recent_messages=10
)
agent = Agent(conversation_manager=conversation_manager)
```

### Proactive Context Compression

모델 호출 전에 미리 컨텍스트를 압축:

```python
conversation_manager = SlidingWindowConversationManager(
    window_size=50,
    proactive_compression={"compression_threshold": 0.7}
)
```

---

## 11. Hooks & Plugins

### Hooks

에이전트 라이프사이클 이벤트에 콜백을 등록.

```python
from strands import Agent
from strands.hooks import BeforeInvocationEvent, BeforeToolCallEvent

agent = Agent()

def log_tool_call(event: BeforeToolCallEvent) -> None:
    print(f"도구 호출: {event.tool_use['name']}")

agent.add_hook(log_tool_call)
```

### 사용 가능한 이벤트

| 이벤트 | 설명 |
|---|---|
| `BeforeInvocationEvent` | 에이전트 호출 시작 전 |
| `AfterInvocationEvent` | 에이전트 호출 완료 후 |
| `BeforeModelCallEvent` | 모델 호출 전 |
| `AfterModelCallEvent` | 모델 호출 후 |
| `BeforeToolCallEvent` | 도구 실행 전 |
| `AfterToolCallEvent` | 도구 실행 후 |
| `MessageAddedEvent` | 메시지 추가 시 |

### Plugins (관련 훅 번들)

```python
from strands import Agent
from strands.plugins import Plugin, hook
from strands.hooks import BeforeToolCallEvent, AfterToolCallEvent

class LoggingPlugin(Plugin):
    name = "logging-plugin"

    @hook
    def log_before(self, event: BeforeToolCallEvent) -> None:
        print(f"호출: {event.tool_use['name']}")

    @hook
    def log_after(self, event: AfterToolCallEvent) -> None:
        print(f"완료: {event.tool_use['name']}")

agent = Agent(plugins=[LoggingPlugin()])
```

### 멀티 에이전트 훅 이벤트

| 이벤트 | 설명 |
|---|---|
| `MultiAgentInitializedEvent` | 오케스트레이터 초기화 |
| `BeforeMultiAgentInvocationEvent` | 멀티 에이전트 호출 전 |
| `AfterMultiAgentInvocationEvent` | 멀티 에이전트 호출 후 |
| `BeforeNodeCallEvent` | 노드 실행 전 |
| `AfterNodeCallEvent` | 노드 실행 후 |

---

## 12. 멀티 에이전트 시스템

### 12.1 Swarm (자율 협업)

여러 에이전트가 자율적으로 핸드오프하며 협업하는 패턴.

```python
from strands import Agent
from strands.multiagent import Swarm

researcher = Agent(name="researcher", system_prompt="연구 전문가...")
coder = Agent(name="coder", system_prompt="코딩 전문가...")
reviewer = Agent(name="reviewer", system_prompt="코드 리뷰 전문가...")

swarm = Swarm(
    [coder, researcher, reviewer],
    entry_point=researcher,
    max_handoffs=20,
    max_iterations=20,
    execution_timeout=900.0,
    node_timeout=300.0
)

result = swarm("TODO 앱의 REST API를 설계하고 구현해줘")
print(f"상태: {result.status}")
```

**Swarm 설정 옵션:**

| 파라미터 | 설명 | 기본값 |
|---|---|---|
| `entry_point` | 시작 에이전트 | 첫 번째 에이전트 |
| `max_handoffs` | 최대 핸드오프 횟수 | 20 |
| `max_iterations` | 전체 최대 반복 | 20 |
| `execution_timeout` | 전체 타임아웃(초) | 900 |
| `node_timeout` | 개별 에이전트 타임아웃(초) | 300 |

### 12.2 Graph (결정적 워크플로우)

의존성 기반의 결정적 실행 순서를 가진 그래프 패턴.

```python
from strands import Agent
from strands.multiagent import GraphBuilder

researcher = Agent(name="researcher", system_prompt="연구 전문가...")
analyst = Agent(name="analyst", system_prompt="분석 전문가...")
report_writer = Agent(name="report_writer", system_prompt="보고서 작성 전문가...")

builder = GraphBuilder()

# 노드 추가
builder.add_node(researcher, "research")
builder.add_node(analyst, "analysis")
builder.add_node(report_writer, "report")

# 엣지 추가 (의존성)
builder.add_edge("research", "analysis")
builder.add_edge("analysis", "report")

# 진입점 설정
builder.set_entry_point("research")
builder.set_execution_timeout(600)

graph = builder.build()
result = graph("AI가 헬스케어에 미치는 영향을 조사해줘")
```

#### 조건부 엣지

```python
def only_if_successful(state):
    research_result = state.results.get("research")
    if not research_result:
        return False
    return "successful" in str(research_result.result).lower()

builder.add_edge("research", "analysis", condition=only_if_successful)
```

#### 피드백 루프 (순환 그래프)

```python
def needs_revision(state):
    review_result = state.results.get("reviewer")
    return "revision needed" in str(review_result.result).lower()

def is_approved(state):
    review_result = state.results.get("reviewer")
    return "approved" in str(review_result.result).lower()

builder.add_edge("draft_writer", "reviewer")
builder.add_edge("reviewer", "draft_writer", condition=needs_revision)
builder.add_edge("reviewer", "publisher", condition=is_approved)
builder.set_max_node_executions(10)
```

#### 네스티드 패턴 (Graph 안에 Swarm)

```python
from strands.multiagent import GraphBuilder, Swarm

research_swarm = Swarm([agent1, agent2, agent3])
analyst = Agent(system_prompt="분석 전문가")

builder = GraphBuilder()
builder.add_node(research_swarm, "research_team")
builder.add_node(analyst, "analysis")
builder.add_edge("research_team", "analysis")
graph = builder.build()
```

### 12.3 Workflow (구조화된 워크플로우)

순차적/병렬 실행, 의존성 관리, 상태 관리를 포함하는 패턴.

```python
from strands import Agent
from strands_tools import workflow

agent = Agent(tools=[workflow])
agent.tool.workflow(
    action="create",
    workflow_id="data_analysis",
    tasks=[
        {
            "task_id": "extraction",
            "description": "데이터 추출",
            "system_prompt": "데이터 추출 전문가",
            "priority": 5
        },
        {
            "task_id": "analysis",
            "description": "트렌드 분석",
            "dependencies": ["extraction"],
            "system_prompt": "데이터 분석 전문가",
            "priority": 3
        },
        {
            "task_id": "report",
            "description": "보고서 생성",
            "dependencies": ["analysis"],
            "system_prompt": "보고서 작성 전문가",
            "priority": 2
        }
    ]
)

agent.tool.workflow(action="start", workflow_id="data_analysis")
status = agent.tool.workflow(action="status", workflow_id="data_analysis")
```

### 12.4 Agents as Tools

에이전트를 다른 에이전트의 도구로 사용:

```python
from strands_tools import swarm, graph

# Swarm을 도구로 사용
agent = Agent(tools=[swarm], system_prompt="에이전트 팀을 만들어 문제를 해결하세요.")
agent("양자 컴퓨팅 최신 동향을 연구, 분석, 요약해줘")

# Graph를 도구로 사용
agent = Agent(tools=[graph], system_prompt="그래프를 만들어 문제를 해결하세요.")
agent("TypeScript REST API를 설계하고 코드를 작성해줘")
```

### 12.5 스트리밍 이벤트 (멀티 에이전트)

```python
async for event in swarm.stream_async("REST API 설계 및 구현"):
    if event.get("type") == "multiagent_node_start":
        print(f"에이전트 {event['node_id']} 시작")
    elif event.get("type") == "multiagent_handoff":
        print(f"핸드오프: {event['from_node_ids']} → {event['to_node_ids']}")
    elif event.get("type") == "multiagent_result":
        print(f"완료: {event['result'].status}")
```

---

## 13. Observability

OpenTelemetry 기반의 관측 가능성 지원.

### 텔레메트리 요소

| 요소 | 설명 |
|---|---|
| **Traces** | 요청의 엔드투엔드 추적. 모델/도구 호출 스팬 포함 |
| **Metrics** | 호출 횟수, 실행 시간, 토큰 사용량, 에러율 |
| **Logs** | 특정 시점의 구조화/비구조화 텍스트 기록 |

### 모니터링 대상 메트릭

- **에이전트**: 호출 횟수, 실행 시간, 에러율
- **도구**: 호출 횟수, 실행 시간, 에러 유형
- **모델**: 토큰 사용량(입출력), 지연 시간, API 에러
- **시스템**: 메모리, CPU, 가용성

---

## 14. 배포

### 지원 배포 옵션

- **Amazon Bedrock AgentCore**: AWS 관리형 에이전트 서비스
- **AWS Lambda**: 서버리스 배포
- **AWS Fargate**: 컨테이너 기반 배포
- **AWS App Runner**: 웹 앱 배포
- **Amazon EKS**: Kubernetes 배포
- **Amazon EC2**: 가상 머신 배포
- **Docker**: 컨테이너화
- **Kubernetes**: 오케스트레이션
- **Terraform**: IaC 기반 배포

### 프로덕션 운영 권장사항

1. **Observability 우선**: 첫 날부터 관측 가능성을 핵심 컴포넌트로 구축
2. **세션 관리**: 분산 환경에서는 S3SessionManager 사용
3. **에러 핸들링**: 도구 실패 시 모델에 에러 정보를 전달하여 대안 시도
4. **컨텍스트 관리**: SummarizingConversationManager로 긴 대화 처리
5. **보안**: MCP 서버 노출 시 보안 고려, 세션 저장소 접근 제한

---

## 부록: 기능 비교 (Python vs TypeScript)

| 기능 | Python | TypeScript |
|---|---|---|
| Agent 생성/호출 | ✅ | ✅ |
| 스트리밍 | ✅ | ✅ |
| Structured Output | ✅ | ✅ |
| 커스텀 도구 | ✅ | ✅ |
| MCP 도구 | ✅ | ✅ |
| Swarm | ✅ | ✅ |
| Graph | ✅ | ✅ |
| Workflow | ✅ | ✅ |
| A2A (Agent-to-Agent) | ✅ | ✅ |
| Session Management | ✅ | ✅ |
| OpenTelemetry | ✅ | ✅ |
| Bidirectional Streaming | ✅ | ❌ |
| Agent Steering | ✅ | ❌ |
| 내장 도구 | 30+ (community) | 4 built-in |
| 모델 프로바이더 수 | 10+ | 5+ |
