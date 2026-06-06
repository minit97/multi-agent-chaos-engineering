# V1 실행 가이드: AWS 환경 세팅 (처음부터)

> EKS 클러스터 생성 → Sample App 배포 → FIS 권한 세팅 → 실험 실행

---

## 사전 준비물

로컬에 설치 필요:

```bash
# 확인 명령어
aws --version        # AWS CLI v2
eksctl version       # eksctl (EKS 클러스터 생성)
kubectl version      # kubectl (K8s 관리)
helm version         # helm (선택, 패키지 설치)
```

설치 안 되어있으면:

```bash
# macOS 기준
brew install awscli
brew install eksctl
brew install kubectl
brew install helm
```

---

## Step 1: AWS CLI 프로필 확인

```bash
# 현재 인증 상태 확인
aws sts get-caller-identity
```

정상이면 아래처럼 나옴:
```json
{
    "UserId": "AIDAXXXXXXXXXXXX",
    "Account": "<ACCOUNT_ID>",
    "Arn": "arn:aws:iam::<ACCOUNT_ID>:user/your-username"
}
```

> ⚠️ Bearer Token은 Bedrock 전용. EKS/FIS는 일반 AWS 자격 증명(Access Key 또는 SSO)이 필요합니다.

---

## Step 2: EKS 클러스터 생성

```bash
# 클러스터 생성 (약 15~20분 소요)
eksctl create cluster \
  --name retail-store-cluster \
  --region us-east-1 \
  --version 1.30 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 4 \
  --managed
```

완료 확인:
```bash
kubectl get nodes
# NAME                            STATUS   ROLES    AGE   VERSION
# ip-192-168-xx-xx.ec2.internal   Ready    <none>   5m    v1.30.x
```

---

## Step 3: Retail Store Sample App 배포

```bash
# 네임스페이스 생성
kubectl create namespace retail-store

# Sample App 배포 (빠른 배포)
kubectl apply -n retail-store \
  -f https://raw.githubusercontent.com/aws-containers/retail-store-sample-app/main/dist/kubernetes/deploy.yaml

# 배포 상태 확인 (모두 Running이 될 때까지 대기)
kubectl get pods -n retail-store -w
```

정상 배포 확인:
```bash
kubectl get pods -n retail-store
# NAME                        READY   STATUS    RESTARTS   AGE
# ui-xxx                      1/1     Running   0          2m
# catalog-xxx                 1/1     Running   0          2m
# catalog-mysql-xxx           1/1     Running   0          2m
# cart-xxx                    1/1     Running   0          2m
# checkout-xxx                1/1     Running   0          2m
# orders-xxx                  1/1     Running   0          2m
# ...
```

(선택) 웹 UI 접근:
```bash
kubectl get svc -n retail-store ui
# EXTERNAL-IP 확인 후 브라우저에서 접속
```

---

## Step 4: FIS IAM Role 생성

```bash
# 1. FIS 실행용 Role 생성
aws iam create-role \
  --role-name ChaosAgentFISRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "fis.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 2. EKS 장애 주입 권한 연결
aws iam attach-role-policy \
  --role-name ChaosAgentFISRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorEKSAccess

# 3. 네트워크 장애 주입 권한 연결
aws iam attach-role-policy \
  --role-name ChaosAgentFISRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorNetworkAccess

# 4. SSM 자동화 권한 연결
aws iam attach-role-policy \
  --role-name ChaosAgentFISRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSFaultInjectionSimulatorSSMAccess

# 5. CloudWatch Logs 권한 (실험 로그용)
aws iam attach-role-policy \
  --role-name ChaosAgentFISRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

확인:
```bash
aws iam get-role --role-name ChaosAgentFISRole --query 'Role.Arn'
# "arn:aws:iam::<ACCOUNT_ID>:role/ChaosAgentFISRole"
```

---

## Step 5: EKS FIS Pod Action Addon 설치

```bash
# FIS가 EKS Pod에 장애를 주입하기 위한 addon
aws eks create-addon \
  --cluster-name retail-store-cluster \
  --addon-name aws-fis-pod-action \
  --region us-east-1

# 설치 확인
aws eks describe-addon \
  --cluster-name retail-store-cluster \
  --addon-name aws-fis-pod-action \
  --query 'addon.status'
# "ACTIVE"
```

---

## Step 6: 내 IAM 사용자에 FIS 권한 추가

에이전트가 FIS API를 호출하려면 내 계정에도 권한이 필요:

```bash
# 인라인 정책 추가 (또는 IAM 콘솔에서 수동 추가)
aws iam put-user-policy \
  --user-name <YOUR_USERNAME> \
  --policy-name ChaosAgentPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "fis:CreateExperimentTemplate",
          "fis:DeleteExperimentTemplate",
          "fis:GetExperimentTemplate",
          "fis:ListExperimentTemplates",
          "fis:StartExperiment",
          "fis:StopExperiment",
          "fis:GetExperiment",
          "fis:ListExperiments",
          "fis:ListActions",
          "fis:ListTargetResourceTypes"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": "arn:aws:iam::*:role/ChaosAgentFISRole"
      },
      {
        "Effect": "Allow",
        "Action": [
          "eks:DescribeCluster",
          "eks:ListClusters",
          "eks:ListNodegroups",
          "eks:DescribeNodegroup"
        ],
        "Resource": "*"
      }
    ]
  }'
```

---

## Step 7: 검증 (전체 세팅 확인)

```bash
echo "=== 1. EKS 클러스터 ==="
kubectl get nodes

echo "=== 2. Sample App Pods ==="
kubectl get pods -n retail-store

echo "=== 3. FIS Role ==="
aws iam get-role --role-name ChaosAgentFISRole --query 'Role.Arn' --output text

echo "=== 4. FIS Addon ==="
aws eks describe-addon --cluster-name retail-store-cluster --addon-name aws-fis-pod-action --query 'addon.status' --output text

echo "=== 5. FIS Actions 조회 ==="
aws fis list-actions --query 'actions[?contains(id, `eks`)].id' --output table
```

모두 정상이면 `test.ipynb`에서 mock 도구를 실제 boto3 도구로 교체하고 실험 실행 가능.

---

## 예상 비용

| 리소스 | 예상 비용 (시간당) | 비고 |
|---|---|---|
| EKS Control Plane | $0.10/hr | 고정 |
| t3.medium x 3 노드 | ~$0.125/hr | 3대 합계 |
| FIS 실험 | $0.00 | 실험 자체는 무료 |
| Bedrock (Claude) | 토큰당 과금 | 이미 사용 중 |
| **합계** | **~$0.225/hr** | 테스트 시에만 켜두기 |

> 💡 테스트 끝나면 클러스터 삭제: `eksctl delete cluster --name retail-store-cluster --region us-east-1`

---

## 세팅 완료 후 다음 단계

1. `test.ipynb` Cell 0~7 실행하여 mock 파이프라인 동작 확인
2. Mock 도구 → boto3 실제 도구로 전환 (v2)
3. `dry_run=False`로 실제 FIS 실험 실행
