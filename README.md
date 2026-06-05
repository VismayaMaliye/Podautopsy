# PodAutopsy 🔬

Automated Kubernetes incident post-mortem generator.

When a pod crashes, engineers normally spend 30-60 minutes manually running
kubectl commands to piece together what happened. PodAutopsy collects all
of that data in 3 seconds and presents it as a structured, shareable report.

## Install

```bash
git clone https://github.com/YOUR_USERNAME/podautopsy
cd podautopsy
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Analyze a specific pod
podautopsy analyze --namespace prod --pod payment-service-7d9f

# With AI root cause analysis
podautopsy analyze --namespace prod --pod payment-service-7d9f --ai

# Save as markdown
podautopsy analyze --namespace prod --pod payment-service-7d9f --output markdown

# Save as HTML
podautopsy analyze --namespace prod --pod payment-service-7d9f --output html

# Scan all failed pods in a namespace
podautopsy scan --namespace prod
```

## Requirements

- Python 3.10+
- kubectl configured and pointing at a cluster
- For AI analysis: Anthropic API key (`export ANTHROPIC_API_KEY=sk-ant-...`)

## What It Detects

| Failure Type | Signal |
|---|---|
| OOMKilled | exit code 137, reason=OOMKilled |
| CrashLoopBackOff | container stuck in restart loop |
| ImagePullBackOff | cannot pull container image |
| Evicted | node resource pressure |
| Pending | cannot be scheduled |