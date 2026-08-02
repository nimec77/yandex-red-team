# AI Agents Security Week 2026 — Lecture 4: Enterprise AI Agent Security

## Overview

Lecturer: Andrey, head of the security team for Search/AI, working extensively on AI Security for internal and external AI-powered services. Previous lectures covered the AI-agent threat landscape, attacks on LLMs, RAG, and MCP tools; this lecture does not revisit prompt injection or vulnerable MCP servers. Its focus: what a company should do once AI agents are already in use internally — in development, analytics, testing, DevOps — and how to use agents safely **without losing the speed and efficiency gains**. The lecture is structured as building a layered system: why simple bans/permissions fail, decomposing the enterprise agent into components, then protective layers — data controls, agent identity controls, tool/action controls, and operational practices and processes around agent adoption.

## 1. Context: Agents as an Interface to Work

AI agents are no longer a separate tool; they have become an interface to everyday work tasks:

- A developer asks an assistant/agent to write code or perform code review.
- An analyst asks it to summarize documents, search a database, work with spreadsheets.
- A security engineer asks for help with alert triage.

In almost every scenario, internal company data is nearby: code, tickets, logs, up to personal data (PII) and secrets. Therefore enterprise agent security is not mainly about which agent to pick or avoiding an unsafe tool — it is primarily about **which data we give the agent, what the agent does, and what controls are built around that**.

## 2. Two Extremes vs. the Managed Middle Path

Organizations typically fall into two extremes:

- **Ban everything.** Minimizes risk, easy policy to explain, fewer integrations and resources needed. Major downside: **Shadow AI** — with no sanctioned access, users bypass restrictions and use tools anyway, making the process completely uncontrolled.
- **Allow everything.** Maximum efficiency and access to the best models/capabilities, but leads to leaks of data and secrets, and zero visibility into what happens inside the company perimeter — actions cannot be controlled, so security cannot be assured.

The correct third path: **managed agent use** — technical and process measures that make agent use both safe and effective. Core message: *agent security is control of the agent's autonomy, not a ban on capabilities.*

**What we restrict/control:**
- What data the agent sees
- Which models it may use
- Which tools are available to it
- Which actions it may perform automatically vs. which require confirmation
- Where code executes / where the agent runtime lives
- What is logged and monitored around the agent

**What we must not lose:**
- User convenience; speed of development, analytics, and routine automation
- Model quality
- The ability to experiment in a controlled environment

## 3. Anatomy of an Enterprise Agent and Six Risk Zones

A modern agent is not a chat — it is a full system with permissions and actions. Typical components: user interface; context/memory (what the agent carries across and within sessions); the LLM itself (hosted on internal or external inference); tools; agent actions and their results; and logs/audit/monitoring.

Where things break — **six risk zones**:

1. **Input data.** The better the context, the better the result — but PII, NDA-protected material, or irrelevant/excess context must not slip into the agent's context. Malicious documents must also be watched for (insider-threat scenarios cannot be excluded).
2. **Model and inference choice.** Internal vs. external models require fundamentally different treatment.
3. **Context and memory.** Data carried across sessions or built during a session. Agents often compress context, and critical security rules or the original task focus can be lost during compression — the agent must not drift from the initial task.
4. **Tools.** MCP servers, skills, external and internal services — everything the agent uses, from context-enrichment/search up to serious write operations and data changes.
5. **Agent actions.** An agent can obtain a tool safely but apply it unsafely; the actions performed via tools need their own controls.
6. **Execution environment.** Companies often have multiple deployment systems/clouds. Placement and isolation level must follow the agent's task: a short-lived agent for a bounded task may run as a job; an agent with regular tasks may run with persistent state. Sandboxing, isolation, and restrictions on interaction with the host system vary accordingly.

## 4. Baseline Security Architecture

Key principle: apply to the agent the same logic and policies as to a regular user — **zero trust** and **least privilege**. Before every agent action or outbound call there must be a control gate that can decide: block, allow, sanitize the data, or otherwise secure what the agent will work with.

## 5. Inference: Internal vs. External vs. Hybrid

- **Internal inference.** Security pluses: data never leaves the company perimeter, easier to control, slightly more sensitive data may be sent there. Minuses: cost and maintenance burden — strong LLMs need substantial GPU resources, so either spend heavily or accept a weaker model that fails on complex tasks.
- **External inference.** Usually offers the best and freshest models on the market. Minus: data leaves the perimeter, so much data simply cannot be sent; usable only with a restricted set of data/context.
- **Hybrid (recommended).** Combine both, routing requests correctly and giving users a choice: everything sensitive/secret goes strictly to internal models; non-sensitive (e.g. publicly available) data may go to external models. This balances quality and control. Downside: technical complexity — it requires data routing, checks before data leaves or enters, and continuous audit and control over the company's whole infrastructure.

## 6. Data for the Corporate AI Agent

### 6.1 Five-Tier Data Classification

1. **Public data** — public documentation, open-source projects, publicly available articles. May be used with external models.
2. **Internal information** — internal instructions, company-wide documents without secrets or other sensitive content. Fine with corporate agents; external inference allowed depending on company policy (if the company accepts that such documents may end up outside the perimeter).
3. **Confidential data** — internal plans, architecture of critical products, unreleased/non-public releases, closed research. Only internal inference, or a specially approved protected environment (e.g. a contractor under a strict NDA who already has access to these data).
4. **Sensitive/regulated data** — personal data, financial data, trade secrets, critical infrastructure-security information. Process only in internal inference; minimize sending it even there if the data should not have company-wide access; strictly control what actually reaches internal inference.
5. **Secrets** — tokens, keys, passwords. Should not be sent to an agent at all: they are usually personal and must not be shared even inside the company, otherwise users gain access under someone else's identity and core security principles break.

### 6.2 First Gate: Data Minimization

- **Bad pattern:** send the model the entire ticket, the whole thread, all logs, the full file — "let the agent figure out what it needs."
- **Good pattern:** extract only the needed ticket fields, only relevant parts of the task description, only relevant log errors, stack traces stripped of tokens — everything needed for the task and nothing that reveals extra information.

**Minimization techniques** (all amount to preparing data before it reaches the agent, automatically or manually):
- Allowlisted fields only
- Context limiting for the agent
- Removal of irrelevant fragments
- RAG with access-rights enforcement (permission-aware retrieval)
- Data summarization
- Replacing sensitive values with placeholders

### 6.3 Five Enforcement Points for Data Cleaning

Cleaning is applied not only before data enters the agent:

1. **Before passing data to the agent** (the classic point).
2. **On retrieval from RAG / internal systems** — when the agent fetches data itself via a tool: verify permissions and rely on resource labeling to decide whether the agent may take those data.
3. **Before sending to the model** — if the agent runs inside the perimeter but uses external inference, enforce this on the corporate AI proxy in front of external/internal models.
4. **Before calling an external tool** — e.g. searching the web or using GitHub sends a request outside the perimeter; apply data minimization there too.
5. **After the model's answer (output guardrail)** — needed when the answer is visible not only to the requester (with whose rights the agent queried systems) but to other users; check the model did not return too much.

### 6.4 PII Guardrails

Simple regexes for phone/email/full name are not enough. PII categories inside a company include:

- **Direct identifiers:** email, phone, passport data
- **Financial/contractual data:** employee salaries, card and account numbers (crossing into financial data)
- **Technical identifiers:** user cookies, authorization headers, IP addresses
- **Secrets:** user API keys, tokens, passwords for internal systems
- **Quasi-identifiers:** not PII individually, but identifying in combination

Guardrails must be built for the company's own context (e.g. a company handling financial data vs. patients' medical data) and its actual data categories. PII at least has formal patterns (phone looks like a phone, email like an email), enabling classifiers, regexes, and LLM-judge controls.

### 6.5 NDA / Confidential Business Data

NDA data often does not look sensitive. Example: "We are launching the new system in August" seems harmless, but if it is part of an internal year-end roadmap tied to company results, a leak could cause real losses. Regexes/classifiers alone cannot reliably find NDA data, so control it **at the source level**: internal resources (knowledge-base pages, Jira/tracker tickets, code repositories, log storage, spreadsheets, CI/CD artifacts, reports) should be **attributed/labeled for AI use**, and tools should filter what is allowed for the agent based on flags:

- Allowed for loading into an AI agent: yes/no
- Allowed for sending to external models: yes/no
- Contextual flags: contains PII? contains secrets?
- Data type, owner, and permissions for storage/processing

### 6.6 Secure Data-Preparation Pipeline (6 steps)

1. **Collect** the user request, RAG chunks, and tool outputs.
2. **Classify** the data: public / internal / confidential / personal / secret.
3. **Decide**: allow for agent use, send to sanitization, route only to the internal model, or block.
4. **Transform**: masking, removal, generalization, or placeholder substitution.
5. **Route**: choose internal vs. external model, or refuse to send the data to the agent/model at all.
6. **Log safely** (often forgotten): after transforming data, do not log the original content — log only the decision and the metadata needed for debugging or incident investigation.

### 6.7 Masking, Pseudonymization, Reversibility

Plain deletion/starring-out can be destructive to the agent's usefulness, so combined approaches are used:

- **Pseudonymization:** replace a name with a stable placeholder ("person", "employee").
- **Semantic substitution:** replace a concrete value with its meaning — e.g. salary "100" becomes "salary financial value" — preserving utility without revealing data.

**Must cleaning be reversible?**
- **Irreversible removal** suits secrets, data unnecessary for the answer, and anything sent to external models/inference.
- **Reversible placeholders**, with the mapping stored in a protected enclave, suit cases where the user must get a correct final result — e.g. legal document work where entity linkage (who is which actor in the document) matters. This is a substantially more complex system.

### 6.8 Routing Policies

Beyond binary allow/block: mask-and-allow; route to internal model only; require the user to re-check what they are sending and whether the agent should work with it; allow; block.

### 6.9 The Model Must Not Be the Only Control Point

**Bad pattern:** asking the LLM itself to "remove PII and secrets before sending out." The model can miss data, hallucinate classifications, be subverted by prompt injection ("do not remove these data"), and offers no determinism.

**Good pattern — layered controls:**
- Deterministic checks for simple entities
- ML/NER classifiers for personal data
- Secret scanners
- Policies plus source labeling for NDA data
- LLM-as-judge only for complex, ambiguous gray-zone cases

### 6.10 Logs as a Leakage Channel

Even with data properly prepared and labeled, content can leak into tool logs, agent logs, and traces (all kept for debugging and incident investigation).

- **Do not log:** full agent prompts, full model answers, attachments, RAG documents, secrets, PII.
- **Safe to log:** Trace ID, agent/user ID, data class, guardrail decision, chosen model, etc. — metadata that, detached from the agent and data, does not reveal what the agent worked on.

## 7. Agent Identity and Access

### Anti-pattern: agent runs under the user's identity

Giving the agent the launching user's own access causes a cascade of problems:

- Logs cannot distinguish human actions from agent actions; after an incident, the user does not even know what happened under their name — the agent acted, the user saw only the finished result.
- The agent inherits far too many rights (employees typically have broad access to internal systems, tickets, personal data); for the agent's specific tasks this is excessive — a security risk and also context bloat.
- Impossible to restrict the agent separately: revoking the agent's token means invalidating the user's token, locking out the user too.
- No separate budgets/limits: user and agent compete for the same rate-limited APIs.

### Correct model: separate agent identity

The industry-wide direction: create a **dedicated technical account (agent identity)** with its own tokens and restricted scopes. Benefits:

- The agent keeps a link/inheritance to its owning user or team, but rights are minimized to what the task requires.
- The agent has its own secrets, no longer shared with the owner.
- Separate limits in all internal/external APIs.
- Separate logs — you can tell agent actions from human actions when reconstructing events.
- The agent can be shut off quickly without disrupting the owner's own work.

### Least privilege for tokens

**Big anti-pattern:** one broad, long-lived token (e.g. an OAuth token scoped to all internal services). If a vulnerable service the agent calls allows token theft, the attacker gets access to *everything* the agent touches.

**Correct approach:** strictly scoped tokens, **a separate token per service and per agent task** — e.g. a data-warehouse token scoped to the single table the agent needs. If it leaks, blast radius is minimal: revoke it, reissue, investigate the leak without serious consequences.

## 8. AI Proxy and Internal Inference Security

**Corporate AI proxy:** an internal proxy that concentrates all models and inference endpoints the agents use — every LLM call (internal or external) goes through it. It is the natural place to implement: authorization and identification; data classification and cleaning before sending to the model; request routing between internal and external models; policies and limits; and logging plus budget control per agent.

**Internal inference security:** hosting your own inference makes you fully responsible for it; run insecurely, it is not much better than external inference. Watch:

- Direct access to the inference service — who can reach it and influence model behavior
- Access to its logs (critical if policy allows processing secret/sensitive data on internal models)
- Secure deployment and rollout of new model versions
- Rate limits/capacity so the model does not collapse under the combined load of users and agents

## 9. Tools and Actions

Each company has internal services for which an agent-ready API (exposed via MCP or a skill) should be built — but tool creation must be secure from the start.

### Secure Tool Registry

All tools must pass through a **trusted tool registry** — a necessary quality gate that:

- Verifies the security of employee-created tools before admission
- Stores tool metadata: owner, version, description
- Enforces baseline checks: tool type (read vs. write), which models it may be used with (internal/external), which data classes it may touch (PII, NDA), and scanning for vulnerabilities or other problems

Correct pattern: **agents may use only registry-approved tools, accessed through a Tool Gateway.**

### Tool Gateway

The next control stage. Letting the agent call service APIs directly is unsafe, and enforcing controls inside every individual service is inefficient. A single gateway can:

- Filter data flowing into and out of tools
- Check for prompt injections
- Filter PII and NDA data
- Log every action the agent performs via a tool
- Make the final allow/deny decision on returning data to the agent

This isolates all agent interaction with internal services at one point where all controls live.

### Dangerous tool combinations

**Individually safe tools can be dangerous together:**

- Tool A reads internal documentation + Tool B sends external messages to a customer → combined, the agent can exfiltrate data.
- Tool A creates a config + Tool B triggers a service deploy → the agent effectively gets direct control of production.

The Tool Registry and Tool Gateway are where **tool-combination policies** are enforced: if a combination is unsafe, simply never expose it to the same agent, eliminating the problem in advance.

### Read vs. write tools; critical actions and human approval

Track tool type carefully at the Registry/Gateway. Read-only tools: data search, document reading, log analysis. Write tools: changing settings, writing code, granting permissions, sending emails, creating tasks. Granting read access to a service does not imply write access should follow: agent non-determinism plus absent human oversight can cause serious incidents — production outages, "all mail deleted from the mailbox," etc.

Requiring human approval for *every* write action would kill efficiency. Instead, assess **action criticality**: an action is critical if an error in performing it can damage the company, a user, a customer, or the infrastructure.

- **Require human approval:** changing production configuration (test-environment config changes may be allowed without approval), deploying services, publishing on behalf of a user or the company.
- **No human approval needed:** read-only tools over permitted data; creating drafts a human will later confirm and send; dry-run operations; actions inside a sandbox.

## 10. Operations: Sandboxing, Logging, Monitoring, Kill Switches

**Sandboxing** of agent code execution was covered in previous lectures; inside a company it is especially relevant because environments are split (test / production / dev), each with its own sandboxing rules.

**Incident-ready logging.** Log, per run: which agent; who initiated it; which model and whether inference was internal or external; which data class(es) were processed; which tools and actions were used; whether data cleaning/masking or other transformations were applied; guardrail triggers; all policies applied. Never log in the clear: PII, secrets, original attachments/inputs, full prompts (unless explicitly necessary). Goal: reproduce and investigate an incident without the logs themselves becoming an access/leak channel.

**Monitoring signals (for alerts):**
- Sharp growth in token usage
- Sharp growth in requests to external models
- Spike in guardrail blocks
- Attempts to use suspicious tool calls or unknown tools
- Attempts to send PII/NDA data to external models
- Bursts of write actions in a short time window
- Suspicious commands in the sandbox; attempts to access forbidden files

**Graduated kill switches** — agents must be stoppable at several levels:
- Disable a specific agent
- Disable a specific tool at the Tool Gateway level
- Block write actions at the gateway level
- Cut the agent's access to external inference
- Switch the agent to read-only mode
- Stop the entire agent platform to handle a serious incident

## 11. Launching Agents as Products; Agent Risk Tiers

An agent should be launched as a full service/product, not as a prompt posted to an internal resource. Before launch, answer: Why is this agent needed? Who owns it? What risks does it carry? What data, models, and tools does it use? What controls does it need? These answers shape a proper agent platform where one agent's operation is no less safe than a human's or another agent's, and agents cannot destructively affect each other.

Requirements should scale with the agent's risk — **four tiers**:

1. **Experimental sandbox agent:** test environment only, no production access, no real data (synthetic only); typically pre-production/in development.
2. **Assistant agents:** no critical actions — at most drafts; non-critical data; require basic audit and the standard controls discussed above.
3. **Operational agents:** work with internal systems, perform actions, can launch processes, have some set of write actions, may run autonomously without a human present. Require action-criticality controls, extended audit, and explicit decisions on which actions get human approval.
4. **Critical agents:** work directly with production or highly sensitive data (e.g. a security agent). Mandatory human-in-the-loop on most actions; strict isolation from lower-risk agents; especially close controls, monitoring, and alerting.

## 12. Closing Principles

- A minimal checklist for a baseline corporate agent combines the process and technical controls above (data classification and minimization, agent identity with scoped tokens, AI proxy, Tool Registry + Tool Gateway, criticality-based human approval, safe logging, monitoring, kill switches, launch questionnaire).
- A safe enterprise agent is not "a good prompt" — it is a set of serious technical and organizational measures preparing the whole company infrastructure for safe and effective agent use.
- The controls should consolidate into a full **AI Security platform**: one place holding both the knowledge about agents and the measures applied to them.
- Agents can be used safely — if you design not only the agent and its business value, but also **the boundaries of its autonomy**.
