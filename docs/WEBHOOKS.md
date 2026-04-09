# Webhook Alerts

Get notified when an agent's reputation score drops below a threshold.

## Setup

```python
agent.set_alert("https://hooks.your-service.com/avp", threshold=0.7)
```

## Payload

When the score drops below the threshold, AVP POSTs to your endpoint:

```json
{
  "event": "score_drop",
  "agent_did": "did:key:z6Mk...",
  "agent_name": "code-reviewer-01",
  "score": 0.61,
  "previous_score": 0.74,
  "threshold": 0.7,
  "trigger": "score_below_threshold",
  "audit_url": "https://agentveil.dev/#explorer?did=..."
}
```

Works with any HTTP endpoint: Discord, Teams, PagerDuty, Zapier, custom.

## Zero-Config Options

### Via decorator

```python
@avp_tracked("https://agentveil.dev", name="reviewer", alert_url="https://hooks.example.com/avp")
def review_code(pr_url: str) -> str:
    return analysis
```

### Via environment variable

```bash
export AVP_ALERT_URL="https://hooks.example.com/avp"
```

All `@avp_tracked` agents auto-subscribe to alerts. Default threshold: 0.5.

## Management

```python
agent.set_alert("https://hooks.example.com/avp", threshold=0.7)  # create/update
alerts = agent.list_alerts()                                       # list all
agent.remove_alert(alert_id)                                       # delete
```

Broken webhooks (5 consecutive failures) are auto-disabled.
