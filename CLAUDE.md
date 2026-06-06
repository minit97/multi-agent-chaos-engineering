# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-driven resilience testing platform using multi-agent chaos engineering. The system uses Strands Agents SDK with Amazon Bedrock to automate the full chaos engineering lifecycle on AWS EKS microservices: hypothesis generation, prioritization, FIS experiment design, execution, and learning/iteration.

The project is in early/prototype stage — documentation and a Jupyter notebook exist but no production source tree yet.

## Tech Stack

- **Language**: Python 3.13
- **Agent Framework**: Strands Agents SDK (`strands-agents` 1.41.0)
- **LLM**: Amazon Bedrock (Claude models)
- **Chaos Engineering**: AWS Fault Injection Service (FIS), AWS Systems Manager (SSM)
- **Target Workload**: Amazon EKS microservices (retail store sample app)
- **Interface**: Jupyter Notebook
- **Infrastructure**: AWS CDK (TypeScript)

## Environment Setup

```bash
# Activate the Python virtual environment
source .venv/bin/activate

# Install dependencies (Strands with Bedrock provider)
pip install 'strands-agents[bedrock]'
```

AWS credentials must be configured for Bedrock and FIS access.

## Architecture: 5-Agent Pipeline

The system follows a sequential multi-agent graph where each agent handles one phase of the chaos engineering lifecycle:

1. **Hypothesis Generator** — analyzes AWS workload inventory, generates failure hypotheses
2. **Prioritization Agent** — ranks hypotheses by impact and likelihood
3. **Experiment Design Agent** — creates FIS experiment templates and SSM documents
4. **Experiment Execution Agent** — validates guardrails, runs FIS experiments, collects metrics
5. **Learning & Iteration Agent** — analyzes results, identifies vulnerabilities, proposes improvements

Agents are composed using `strands.multiagent.GraphBuilder` with linear edges between phases. Each agent uses `use_aws` and `get_workload_tags` tools to interact with AWS resources.

## Key Conventions

- Agents must enforce 5 safety guardrails before experiment execution: target pre-validation, per-service safety thresholds (min 2 replicas), blocked action exclusion list, blast radius control (no cluster-wide selectors), and safe priority ordering.
- All documentation is in Korean. Keep new docs in Korean to match.
- The project references the [aws-samples/sample-strands-chaos-engineering-agents](https://github.com/aws-samples/sample-strands-chaos-engineering-agents) repo as a reference implementation.
