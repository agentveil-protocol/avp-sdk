# AVP Roadmap

## Source Of Truth

- Current public Python SDK package: `agentveil 0.7.23`.
- Current public MCP Proxy package: `agentveil-mcp-proxy 0.7.44`.
- Package metadata and PyPI are the version source of truth. This roadmap tracks
  product direction only; release history belongs in `CHANGELOG.md`.

## Available Today

- [x] Public Python SDK on PyPI: `pip install agentveil`
- [x] Public MCP Proxy on PyPI: `pip install agentveil-mcp-proxy`
- [x] Project connector setup for Cursor, Claude Code, Codex, and Gemini CLI
- [x] Hermes CLI controlled MCP launch profile
- [x] Core MCP Proxy route for configured downstream MCP tool calls
- [x] W3C DID identity (`did:key`, Ed25519)
- [x] AVP-Sig request signing for authenticated protocol calls
- [x] Posture/setup readiness checks with `integration_preflight()`
- [x] Runtime Gate controlled-action flow with `controlled_action(...)`
- [x] Local DelegationReceipt v1 issuance with `issue_delegation_receipt(...)`
- [x] Signed runtime receipts and proof packet verification
- [x] MCP Proxy evidence export and offline verification:
  `agentveil-mcp-proxy export-evidence` and `agentveil-mcp-proxy verify`

## Preview / Active Rollout

- [ ] Broader controlled-action rollout for customer workflows
- [ ] Operator-facing documentation for production adoption
- [ ] Customer-facing DelegationReceipt issuance UX and examples
- [ ] Deployment documentation for approved customer environments
- [ ] Execution boundary and gateway adapter contract

## Planned

- [ ] Public agent reputation dashboard
- [ ] Expanded hosted MCP catalog metadata and recrawl
- [ ] Formal protocol specification v1.0
- [ ] Expanded Runtime Gate examples for common agent stacks
- [ ] Dedicated root SDK CLI demo command: `agentveil demo controlled-action`
- [ ] Dedicated root SDK proof commands:
  `agentveil proof export` and `agentveil proof verify --offline`
- [ ] Posture Check report for risky tools, write access, credentials location,
  and bypass paths

## Research / Future

- [ ] Runtime proof and offline verification publication
- [ ] ERC-8004 bridge exploration
- [ ] Federation between AVP nodes
