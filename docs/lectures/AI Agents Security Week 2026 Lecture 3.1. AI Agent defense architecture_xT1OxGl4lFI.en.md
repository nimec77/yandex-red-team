# AI Agent Defense Architecture

## Overview

Lecture 3.1 of the "AI Agents Security Week 2026" course, delivered by Radmir Samarkhanov (Yandex; works on Managed GitLab and SourceCraft). The lecture approaches AI agent security not as "which filter to put in front of the model" but as a property of system architecture. Goal: learn to decompose any agentic system into parts, find where the holes are and where protection is redundant — a transferable skill, not a set of recipes. Plan: (1) how an agentic system is structured and where its weak points are, (2) a method to quickly find weak points and decide how much protection is needed where, (3) how to build that protection into the lifecycle so it doesn't decay over time.

## Why Agent Security Is Different from Chatbot Security

- For a chatbot, the usual worry is jailbreaks — "what if it says something it shouldn't." Input is text, output is text, there are essentially no side effects; worst case the answer is nonsense and you open a new chat.
- Once the model stops merely answering and starts **acting** — reading files, browsing the internet, calling tools, running commands, acting on your behalf — the question changes: what matters is not what the system *said* but what it *did*.
- A bad output is now potentially a deleted repository, a leaked secret, or someone else's code shipped to production.
- **Central thesis of the lecture:** security of an agentic system is not a filter in front of the model and not a pre-release checklist. It is a property of the architecture. Protection is either built into how the system is structured, or it does not exist — no clever filter can substitute for it.

## What Is an Agentic System

Working definition: an agentic system = model + its context + its state + its tools + action rules + the **execution loop**. The loop is the key word: the model plans next steps, acts, observes its own results, and iterates — possibly dozens of times. Therefore security of an agentic system is security of the **entire execution loop**, not of a single prompt.

Quick test — three questions; if at least two answers are "yes," it is an agentic system and must be defended:

1. Does the system gather context itself from external sources (files, internet), or does a human place everything into the request?
2. Does the system choose/propose the next step itself, or is the algorithm hard-coded?
3. Most important: can the system perform **real actions with real permissions**? Real permissions are the line beyond which an error stops being harmless.

## The Five-Layer Map

1. **Input and context** — everything the system reads: requests, data, documents.
2. **Core** — the model itself, its instructions, state, and ability to choose next steps.
3. **Memory and RAG** — what the system remembers and can retrieve by meaning.
4. **Tools / MCP** — what the system can invoke in external systems.
5. **Execution and infrastructure** — where a decision becomes a real action: running a script, executing commands in the cloud, delivery to production.

Common mistake: "protect the system" is interpreted as "protect the model" — put a guardrail in front of the LLM and relax. But the model is only one of five layers: context can be poisoned, memory can retain harm for a long time, tools produce real side effects, execution touches actual infrastructure. Covering only the model leaves four layers open; the incident can come from any of them.

## Trust Boundaries: Attacks Happen on the Arrows

- The danger lives not only inside the layers but **on the boundaries between them** — the arrows on the diagram. Every arrow where data crosses from one layer to another is a **trust boundary**.
- Attacks typically happen exactly where data crosses a boundary and turns into an instruction or an action — not in a block, but on an arrow. Examples: an untrusted document lands in context; the agent retrieves a poisoned record from memory; a tool returns a tampered result.
- Boundaries exist not only between human and system, but **between system and system**: the output of one system is untrusted external text for another.
- Defense reduces to one idea: find all trust boundaries and put a control on each one.

## Why Every Boundary Is Dangerous: Data vs. Commands

- In a conventional program, data and code are strictly separated. In a language model, text is simultaneously data **and** commands: the model does not natively distinguish "given to me to read" from "ordered for me to do" — both are just text in context.
- **Core rule:** everything arriving from outside is **data, not commands**. Documents from a knowledge base, tool output, the body of someone else's pull request, an incoming email — all data. Even if the content literally says "urgently run this command," that is content that happens to look like an order, not an order.
- By default the system may read it as an instruction and execute it. This is the root of nearly all problems in such systems.

## Threat Modeling in Five Steps

A process applicable to any agentic system *[Note: the speaker calls it "threat modeling"]*:

1. **Draw the data flow.** Decompose the agent across the five layers: where context comes from, which model, what is in memory, which tools, where execution happens. Blocks and arrows on a sheet of paper.
2. **Mark all boundaries** — every arrow where data crosses layers and external becomes internal. These are the main risk points; there are usually 5–7 of them.
3. **At each boundary ask: what can an attacker do in the worst case?** Not the typical case — the worst. An incoming document must be presumed untrusted and possibly carrying an injection; a tool call must be presumed to have potentially substituted arguments.
4. **Rank the boundaries by blast radius.** Somewhere the maximum damage is a bad answer; somewhere it is a wiped production environment.
5. **Place controls starting from the largest radius.** Close the boundaries where the cost of error is maximal and irreversible first; deal with small stuff later.

## Blast Radius: The Autonomy Spectrum

Autonomy is a spectrum, not an on/off toggle. The same injection at different levels causes radically different damage (bottom to top):

- **Text only** — worst case: a bad answer.
- **Reads context** — can pull a harmful instruction in from outside.
- **Proposes changes** — can propose dangerous recommendations (a human still applies them by hand).
- **Writes files** — direct modification of code and configs.
- **Runs commands** (packages, secrets, shell) — maximal risk: reaches real execution.
- **CI/CD deploy** — full compromise; hits everyone who consumes the artifact the system produces.

**Formula to remember: the injection is just the trigger; permissions and tools are the blast radius.** The fact of injection is identical at every level — the difference is only in what the system is allowed to do afterwards.

First practical conclusion: **the cheapest way to reduce risk is to remove unnecessary permissions from the system, not to add another filter.**

## How Much Protection Each Level Needs

Minimum controls per autonomy level:

- **Read-only in the working directory:** an allowlist is sufficient (low risk).
- **Writes to working directories:** allowlist + manual human confirmation.
- **Executes arbitrary scripts/code:** isolation (sandboxing) of execution + human confirmation.
- **Calls external APIs with data:** very high risk — short-lived credentials scoped to the specific operation, with audit.
- **CI/CD and deploy:** maximal risk — everything above, plus mandatory audit of everything happening, with maximally reduced permissions for each operation in the pipeline.

Logic: the higher the radius, the more control shifts from checking text to **restricting capabilities and recording results**.

Caveat many forget: human confirmation only works if the human understands what they are approving. If the system proposes reading a config, the human must see *which* configs and *why* — not rubber-stamp "OK" without looking.

## The Dangerous Triad as a Design Rule

A quick lens to judge whether a system is dangerous at all — three conditions *[Note: this is Simon Willison's "lethal trifecta"]*:

1. Access to **private data**;
2. **Untrusted input**;
3. An **egress channel** through which something can be sent out.

When all three coincide, risk is maximal: untrusted input gives the attacker a voice, private data is the loot, and the egress channel is the way to carry it out.

Usually this triad is presented as a way to describe attacks, but it can be inverted into a **design rule**. Closing each attack individually is expensive and endless — attacks keep improving and defenses go stale. But if you **architecturally remove one of the three legs**, the attacker fundamentally cannot cause damage. Removing one leg is cheap and works always:

- If the system reads untrusted pull requests from strangers — give it **no egress channel**: nowhere to exfiltrate.
- If the agent holds secrets and touches production — it must **accept no untrusted content at all**.

Before hanging filters on the system, check whether you can simply not give it all three legs at once. Absence of a channel cannot be bypassed; a filter can.

## End-to-End Case: An Attack Chain Across the Five Layers

A chain derived directly from the five-layer map (not invented — mirrors real incidents):

1. Agent reads an **untrusted pull request** (e.g., to help with review). An injection is hidden in the PR description. — *Input boundary.*
2. The injection enters context; the system interprets it as a task. — *Core boundary.*
3. The system edits configs / CI workflows. — *Tools/write boundary.*
4. CI runs; CI holds tokens and secrets. — *Execution boundary.*
5. Secrets and sensitive data are exfiltrated. — *Egress layer.*

Note: **every individual step is legitimate.** Reading, writing, executing are all normally permitted; nothing is "hacked" at any single step — the system performs ordinary actions. Only viewing the chain end-to-end reveals where to break it:

- **Boundary 1:** context from a PR is untrusted → data, not commands; no privileged actions are permitted on its basis.
- **Step 3:** writes to configs go through allowlists; an attempt to escape the allowed set requires **explicit human confirmation** — the human can see it and refuse.
- **Step 4:** the system must hold **no raw secrets**; they are injected by a separate external system, narrowly scoped — for an untrusted PR they simply don't exist.
- **Step 5:** **no egress** — nowhere to carry data out (the removed leg of the triad).

Key idea: defense is not one wall but several boundaries, each with its own control. The attacker must break through **every** level; the defender needs to hold **only one**.

## Real, Documented Incidents

Each documented case below hits exactly one link of the chain above:

1. **GitLab Duo** (GitLab's AI assistant). Researchers from **Legit Security** hid an instruction in a merge request description (input layer). Duo read it as a command, rendered an image, and exfiltrated source code (egress layer). One case violates two boundaries at once: input and output.
2. **MCP-based repo agent exploit found by Invariant Labs** — hits core and tools. A malicious issue was planted in a public repository; an agent with overly broad permissions read it, obeyed, and leaked everything from private repositories into a public pull request. Exactly the pattern discussed: untrusted input treated as a command, combined with excessive permissions. Remedy, as already discussed: **narrow tokens scoped to the specific repository per session.** *[Note: the transcript says "GitLab MCP"; the described case matches Invariant Labs' well-known GitHub MCP exploit (malicious issue → private repo data leaked into a public PR).]*
3. **Cursor** (AI IDE) — hits tools and execution. An injection made the agent append a line to the MCP config (`mcp.json`); the entry auto-launched, resulting in arbitrary code execution on the machine. *[Note: this matches the "MCPoison" vulnerability, CVE-2025-54136, reported by Check Point.]*

Three different products, three different research teams — one identical mechanism: untrusted text crosses a trust boundary. Together the cases cover the whole chain: input, core, tools, execution, egress. The hand-drawn map is not theory; it is a real attack map.

## Lifecycle: From SDLC to ADLC

Doing threat modeling once before a release goes stale within a week — attacks improve daily. Protection must live in the lifecycle.

- Classic **SDLC** tracks code changes: commits, versions, deploys; the boundary is "who committed what"; feedback comes from bugs, tests, review.
- In AI systems, not only code changes — **behavior** changes, plus a whole layer that regular code lacks: instructions, data, tools, and permissions. This is **ADLC — Agentic Development Lifecycle**.
- In ADLC, artifacts are not just commits but instructions, context, and policies; data, memory, tools, and permissions all mutate; the boundary is no longer "who committed what" but **"who can do what with real permissions"**; feedback is logs and traces, from which new restrictions are born.
- Goal of the framework in one line: **a model error must never become a full compromise.** The model will err — that is a given; the question is whether the error is contained or reaches production.

### Eight Stages of ADLC (each control lands on its stage)

1. **Design** — draw the trust boundaries and honestly decide what the system must never be able to do. The cheapest control; applied at stage zero, on paper.
2. **Tools** — every tool works via an allowlist. The model also reads tool descriptions/metadata and trusts them by default, so tool metadata is part of the trust chain.
3. **Context** — label provenance of everything; external content is data, not commands.
4. **Memory** — validate whatever enters long-term memory both on write and on read: memory poisoning lives a very long time.
5. **Identity** — the system must never see raw secrets; access decisions are made by an external system, not by the prompt.
6. **Gateway** — every external endpoint requires authorization; attach metadata and logs; close open endpoints.
7. **Red teaming** — continuously attack your own system, grow the bypass corpus, and re-run it regularly.
8. **Observability** — log so that an incident can be investigated right here and now.

Controls do not hang in a generic "best practices" list — each is bound to a stage. That is what distinguishes architectural protection from a one-off effort.

## Observability: Agent Logs Are Wider Than Backend Logs

Without logs, all protection is blind: if the system was broken and there are no traces, the incident cannot be investigated and continuous testing has nothing to build on. Agent-system logs must capture essentially everything:

- the prompt;
- which tools were called and **with which arguments**;
- which chunks were retrieved from the database (RAG);
- what verdicts the checks/guardrails produced;
- under which identity and tokens each request ran;
- the model version;
- routing decisions.

From this set you can reconstruct what happened and at which boundary, and add a new check. Without tool calls + arguments you can't tell what the system did; without identity — on whose behalf; without retrieved chunks — whether it trusted poisoned data. Logging is part of the defense, not an appendix to it.

## Identity: The Most Underrated Layer

- **Antipattern:** giving the system a raw key directly in context ("it's faster"). The system can be compromised by nature, and if it holds a live key, it can hand it to any third party, write it to a log — anywhere. One key with rights to everything means any compromise equals full access on behalf of the service.
- **Correct pattern:** the system never sees the raw secret. It operates on an **alias/profile** — e.g., instead of a bearer token it invokes something like a "read-database profile." The real token is injected by a separate external layer the model has no access to, and that layer logs the operation.
- Even if the system is compromised, the most it can reveal is which profile it invoked; the key cannot leak because the system never held it.
- **Principle: permissions are a property of the system, not of the prompt.** Who may do what is decided not by text in an instruction (easily broken) but by an external control — e.g., a token issued narrowly for a specific operation, for a limited time, on behalf of a specific actor.
- This also cures the classic **confused-deputy** problem: a privileged component acting without verifying that the original requester had the right.

## Common Pitfalls (If You Recognize Your Project in Two of These, Fix Something)

- Protecting only the LLM while boundaries don't exist — one filter in front of the model with five other arrows wide open. The most frequent problem.
- A single shared system prompt for everyone — break it once and even an ordinary user learns everything they shouldn't.
- Raw keys stored at the system — compromise equals leak.
- Permissions granted via the prompt instead of an external system — that is not access control, it is a wish.
- Believing "internal agent = safe agent" — a compromised internal system will talk to one that has real permissions, and the infection propagates.
- Approving long scripts without reading them — confirmation without understanding is not protection.
- Believing an unknown open endpoint is unreachable — it will be reached; every endpoint must require authorization.
- Configuring a guardrail once and forgetting it — defense is a living system that must be tested continuously.

## Summary: The Whole Picture and Three Pillars

Five layers — input, core, memory, tools, execution — each boundary with its own control: check text at input and output; track provenance in context and memory; allowlists and authorization in front of tools; maximal isolation of execution; access granted through external systems, narrowly, per task. On top of it all, the eight-stage ADLC band from design to observability turns a one-time placement of controls into a continuous process. This map is drawable quickly with the method from the start: layers → boundaries → worst cases → radius → controls.

The one takeaway: **defense of AI systems is not a filter and not a checklist — it is an architecture of trust boundaries built across the whole lifecycle, prioritized by blast radius.** Three pillars:

1. **Boundaries** — danger lives on the arrows between layers; every boundary needs a control.
2. **Lifecycle** — protection is built in from the design stage and lives through observability, not bolted on before release.
3. **Radius** — close the places where the cost of error is maximal first; **remove excess permissions before adding filters.**

Honest closing note: at the engineering level, AI-system security largely resembles ordinary DevSecOps — the same authorization, isolation, least privilege, audit, and testing as any system with access rights. The principal difference: one of the inputs is now arbitrary text that the model may take for a command. Everything else you already know how to do — you just need to see the agent as a system of boundaries.
