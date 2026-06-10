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

## Examples
<img width="1440" height="789" alt="Screenshot 2026-06-05 at 5 07 35 PM" src="https://github.com/user-attachments/assets/c6209107-cfc5-4156-ae32-e6a3957afe32" />
<img width="1440" height="853" alt="Screenshot 2026-06-05 at 5 09 03 PM" src="https://github.com/user-attachments/assets/9581d7da-a2eb-47a3-87d0-7260760c9347" />
<img width="1440" height="887" alt="Screenshot 2026-06-05 at 5 06 46 PM" src="https://github.com/user-attachments/assets/4ed4f8fe-817b-442f-ae7e-3794d4e45989" />


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
