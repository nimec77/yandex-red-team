# Breaking the Guardrails — AI Agents Security Week 2026, Lecture 5

## Overview

This lecture explains why modern generative models (LLMs and diffusion text-to-image models) remain vulnerable to censorship-bypass attacks, what NSFW ("not safe for work") attacks are, which tools and techniques attackers use, and which defenses exist for developers and product owners. The lecturer is an ML engineer on VK's computer vision team who researches attacks on text and diffusion image-generation models. The arc of the lecture: alignment theory → why the refusal boundary is inherently blurred → real-world NSFW incidents and measurable business risk → attack taxonomy and attacker tooling → defense methods for diffusion models → fundamental trade-offs.

---

## 1. The Problem: Guardrails Fail in Both Directions

A naive but common defense architecture for a diffusion image model:

- A relatively small LLM filters the user's prompt, configured flexibly via a system prompt.
- A VLM (vision-language model) validates the output image, also configured via a system prompt.

Metrics for this setup look good and beat many baselines — until an attacker arrives.

**Failure mode 1 — under-refusal (bypass).** A user requests "generate a marble statue of Venus" and adds names or reference photos of real public figures. The filter breaks, and the pipeline produces ready-made deepfakes, adult content, or arbitrary other scenes.

**Failure mode 2 — over-refusal (uselessness).** A student preparing a class presentation asks for an image of a doctor using surgical instruments for their intended purpose. A model aligned to refuse "sensitive" topics refuses, and becomes useless for a legitimate user.

The same duality appears in LLMs:

- Users put ChatGPT into a science-fiction framing (the user role-plays as a science fiction author) and get detailed instructions about a prohibited item.
- Research shows a whole zoo of large models breaks under this class of attack: DeepSeek, Mistral, ChatGPT and others remain vulnerable.
- Conversely, an entrepreneur asking about loopholes in tax law — a legitimate if edgy question — gets refused, and the model becomes useless.

Text-to-image-specific examples shown in the lecture:

- **Ambiguity attack.** The instruction is written to sound safe (a man "eating pancakes with a knife" while returning a frightened woman's lost bag), but the resulting visual is clearly unsafe. Text-level safety does not imply image-level safety.
- **Euphemism attack.** Crude/explicit words are replaced with mild, neutral synonyms; the guardrail passes the prompt and the model generates the unsafe image anyway.

The models clearly *have* the knowledge. The question is why they cannot make the correct decision reliably.

---

## 2. How Models Are Aligned

### 2.1 RLHF (Reinforcement Learning from Human Feedback)

**Stage 0 — pretraining.** Largely unsupervised training on raw, "dirty" internet data. The governing principle is *garbage in, garbage out*: whatever the model ingests during parameter updates is what you reap at inference. Many researchers argue data quality is the dominant factor in LLM training, worth 90%+ of the final result; ML in general is bound to data quality and feature engineering.

**Stage 1 — supervised fine-tuning.** The LLM is fine-tuned on curated prompt–response pairs produced by human annotators, using standard next-token likelihood maximization with gradient descent. Output of this stage: the **initial language model**. It now produces coherent, user-friendly answers but has no real notion of "good" versus "bad."

**Stage 2 — reward model training.** The initial model is fed a set of prompts and emits several candidate responses per prompt. Human annotators rank these by preference. A separate **reward model** is trained with a loss resembling binary cross-entropy, penalized whenever it scores a lower-ranked answer above a higher-ranked one. Result: a model that outputs a scalar preference score for a (prompt, response) pair.

**Stage 3 — RL fine-tuning.** The target model is the **RL policy**. Its outputs are scored by the reward model. A **KL-divergence penalty** is added so the policy does not forget knowledge learned earlier — the divergence is computed over output-token log-probabilities compared against the same log-probabilities from the initial language model. Optimization uses **PPO (Proximal Policy Optimization)**.

*[Note: PPO is a policy-gradient RL algorithm that constrains each update to stay within a trust region of the previous policy; the lecture explicitly leaves its details out of scope.]*

**Known limitation: reward hacking.** The reward model can start assigning inflated scores for templated, formulaic phrasing rather than for genuine helpfulness or substance.

### 2.2 The HHH Framework and Its Built-in Conflict

Alignment for safety is usually framed by the **HHH** triad *[ASR rendered this as "3 age"]*:

- **Helpful**
- **Honest**
- **Harmless**

These conflict by construction. If a chatbot is asked for instructions to make an explosive:

- *Helpful* says: comply and assist the user.
- *Honest* says: give a technically and physically accurate answer.
- *Harmless* says: refuse to generate.

Helpfulness and harmlessness are therefore in direct opposition.

Research findings on aligning to one objective versus two:

- Aligning for **helpfulness + harmlessness** costs surprisingly little in user-rated helpfulness compared with training for helpfulness alone.
- A model trained for **helpfulness only** scores far worse on safety/harmlessness — worse even than some baselines.
- Technical accuracy of answers does not degrade much versus baselines, and at larger parameter counts sometimes improves.
- A side effect appears: **evasiveness** — the model emits templated non-answers, refuses to sustain a conversation on any sensitive topic, and gives the user no guidance at all.

*[Note: these results come from Anthropic's helpful-and-harmless RLHF line of work, which introduced the HHH formulation.]*

### 2.3 Constitutional AI and RLAIF

To smooth over evasiveness, Anthropic proposed **Constitutional AI**: a written "constitution" of policies drives the training pipeline instead of per-example human labels.

**Supervised (critique–revision) phase:**

1. Start from an already-aligned model.
2. A **red teaming** team collects harmful/adversarial prompts.
3. For each prompt, the model produces an initial answer.
4. One of **16 randomly selected policies** is loaded into context and the model is asked: does this answer actually comply with this policy? The model reasons and typically answers "no."
5. **Revision phase:** the model is instructed to rewrite its answer so that it does comply with that policy.
6. This yields a (harmful prompt, ideally safe answer) pair. The loop can be run several times.
7. The original model is fine-tuned on the resulting pairs.

**RL phase:**

1. Use the same red-team prompts. The fine-tuned model generates two candidate answers (A and B).
2. Both go to an intermediate **feedback model**, which emits per-token logits / log-probabilities conditioned on choosing A or B.
3. Those log-probabilities train a **preference model** that predicts how preferable an answer is.
4. The preference model then supplies the feedback signal for online RL fine-tuning of the target model.

The authors also experiment with **chain-of-thought**: asking the model to reason before answering raises overall quality of the pipeline.

Because no human annotators are involved in the feedback loop, this approach is called **RLAIF — Reinforcement Learning from AI Feedback**.

---

## 3. Why Alignment Still Fails: Fundamental Causes

Even a well-aligned model like Claude will refuse elaborately on illegitimate topics — yet will also refuse legitimate ones. (Lecturer's own example: researching attacks on the **RSA cryptosystem**; Claude judged the topic sensitive and declined, which made it useless for a researcher/student.)

Root causes:

- **The human factor.** Training data, policies and constitutions are written by people, who carry their own culture, values, nationality, preferences and notions of good and bad. That bias is injected into the model and into every subsequent training stage.
- **Pretraining contamination.** The starting data is raw and dirty. Each subsequent stage only *polishes* a transformer trained on that base; the bias flowing through the whole pipeline can never be fully removed.
- **The Bayesian/statistical nature of ML.** Training operates on a finite sample, minimizing empirical risk to obtain the weight vector that is most probable given that data and configuration — i.e., maximizing likelihood *on the observed sample*. When a new input arrives that the model saw rarely or that was labeled inconsistently, the model lands in a region of uncertainty and answers unconfidently.
- **The space of language is uncoverable.** Attackers always find new phrasings. This is why no perfect profanity filter exists either — hybrids, homoglyphs, and letters from other alphabets defeat keyword detection; the detector would have to be extraordinarily strong.

Attackers writing **jailbreak** prompts are, mostly unknowingly, exploiting these mathematical foundations of how LLMs and other models are trained.

### Key concepts

- **Alignment tax.** You cannot make a system fully safe without sacrificing something — typically usefulness. Developers always pay this tax.
- **Refusal boundary.** The model's decision boundary between refusing and complying is inherently blurred, as a consequence of everything above.
- **Over-refusal vs. under-refusal.** Two sides of one coin. Over-refusal example: a user asks "how do I kill a Python process" and the model latches onto the word "kill" and refuses a completely legitimate request. Under-refusal is the miss (letting harmful content through). The harder you fight one, the more you lose on the other.
- The same trade-off applies to diffusion text-to-image models: the tighter the safety screws, the more you lose elsewhere — generation quality measured by **FID (Fréchet Inception Distance)** will degrade, significantly or slightly, but measurably.

### Interim conclusions

1. Safety costs a tax. This is not a bug — it follows from the statistical, probabilistic nature of machine learning.
2. The refusal boundary always has been, is, and will be blurred. Solutions always operate under uncertainty.
3. Euphemisms and similar techniques are not "hacking the model" — they are **exploitation of vulnerabilities baked in at every training stage**.

---

## 4. NSFW Risk Is Real and Measurable: Case Studies

**NSFW** ("not safe for work") historically marked content unsafe to view in public or at work. It used to be distributed by people; in the generative-AI era the models themselves became the source.

### 4.1 The FlowGPT study (CHI 2024)

In 2024 researchers studied **FlowGPT**, a chatbot marketplace with roughly **4 million monthly visits** at the time. They analyzed about **400 chatbots** and several hundred public user chats, publishing at **CHI — the ACM Conference on Human Factors in Computing Systems**, a leading HCI venue, which reflects the scale and criticality of the problem.

Findings:

- The existence of such a platform confirms real user demand for these services — but demand does not guarantee product safety, and bad news about a model can leak at any moment while such marketplaces operate.
- In **nearly a quarter of cases the chatbot itself generated and initiated NSFW content**, even when the user had not asked for it.

Four key insights:

1. **Virtual intimacy.** Users form emotional closeness with chatbots, especially persona-styled ones. The danger is that this engagement draws people into unsafe activities with real-life consequences.
2. **Bot-initiated NSFW content.** Bots start NSFW content unprompted, and age restrictions break down — a chatbot rarely asks who it is talking to. This distorts users' perception of reality and creates ethical risk.
3. **Normalization of violence.** Models enter the user's frame of reference and justify or recommend violent actions, and become biased about public figures — creating legal and reputational risk for the product.
4. **Instrumental assistance.** The model can effectively become an accomplice, generating instructions for creating dangerous items.

### 4.2 Grok (xAI / Elon Musk)

An incident dated late last year / early this year: roughly **4.5 million images generated in a few days**, with a dominant share being fakes involving women and children and other extreme scenes.

Consequences: investigations in the **EU, UK and Canada**; **class-action lawsuits in the United States**; **resource blocking in Indonesia, Malaysia** and other countries. This was not merely a scandal — it was a gap in the moderation pipeline and in the defense of a generative AI product.

### 4.3 GenNomis (South Korean startup)

The startup poorly secured its database of generated images. A researcher found it exposed and discovered roughly **100,000 images** covering violent and other extreme themes. After the database was removed and the US technology magazine **WIRED** contacted the startup, the company's website returned a **404**. Not formally a bankruptcy, but the company effectively ceased operating: investors most likely pulled out, and the product could not be developed further.

Takeaway: a promising startup can be destroyed by reputational and image risk if product-safety questions are ignored.

### 4.4 Financial magnitude

Research by **DeepStrike** *[ASR-garbled company name]* found that the **average business loss from a single deepfake incident is around $500,000**. Forecasts show exponential growth in the volume of deepfake content online and in the associated business costs — a discouraging trajectory with genuinely measurable risk.

---

## 5. Attack Taxonomy

The main classification work on prompt-based attacks (jailbreaks) is **"Anyone Can Jailbreak" (2025)**.

Core claims:

- Generating harmful text and images is **low-effort and high-impact**: cheap and effective. Attackers frequently need no technical knowledge at all to break a model's defenses.
- The cause is the high flexibility and richness of natural language, which defenders and developers struggle to anticipate in moderation pipelines.
- Many production defense systems still rely on unintelligent approaches such as **keyword filters**. Defenses must evolve to protect different model classes.

### 5.1 LLM attack classes

- **Fictional roleplay / worldbuilding.** Place the model in an imaginary context in which it breaks and starts producing unsafe output. Example shown: a **MasterKey**-style attack *[name as spoken; ASR-garbled]* where the author poses as a science fiction writer, introduces a character that is an unrestricted AI, and asks that character for a method to steal someone's personal data. The attack works.
- **DAN ("Do Anything Now").** Tell the model at the start that it is now "DAN," that it forgets all its system instructions — models frequently comply.
- **PAP-style / persuasion attacks** *[ASR rendered this as "PP"; from context, attacks that exploit helpfulness alignment — most likely PAP, Persuasive Adversarial Prompts]*. They exploit the fact that the model is aligned to be useful to the end user.
- **Expert impersonation.** The model is placed in an academic or scientific research context and complies. Slide example: the user presents as a university researcher studying social engineering methods, states that the work is approved by an ethics/review committee, and asks for a phishing email "for testing." The model falls for it and produces the unsafe output.
- **Encoding and obfuscation.** This class *does* require technical knowledge. Unsafe concepts are wrapped in a data structure — **JSON, XML** and other formats — or the model is asked to solve puzzles: brute-force tasks, **anagrams**, decoding simple ciphers. Slide example: the model solves an anagram, and the attacker then uses the resulting answer to steer the conversation toward describing the unsafe item and maintain that context.
- **Multi-turn / gradual escalation.** Exploits the dialogue properties of models: the unsafe intent is diffused across the context of a conversation. Slide example (split-request / Crescendo-style *[technique name partially garbled in ASR]*): inject the unsafe request between, say, the first and third benign requests and ask the model to stitch everything into one coherent logical sequence. In practice such tricks break the model.

### 5.2 Text-to-image attack classes

The authors note that the output of a T2I model is always an **image** — a visual trigger that humans perceive more readily than text. They therefore hypothesize that **defending T2I models is higher priority, and jailbreaks against T2I models are a more dangerous threat than jailbreaks against LLMs**.

Attack types shown:

- **Euphemism substitution** (crude words replaced by mild ones).
- **Scientific / academic framing.**
- **Masquerading as high art.**
- **Double meaning / ambiguity.**
- **Niche references and subculture terminology**, which also break models.

### 5.3 The assumed defense pipeline and where it breaks

Because most companies do not disclose their guardrail architecture, the authors hypothesize a standard linear, multi-layer filtering pipeline:

1. **Input compliance check** — early validation for obvious triggers (e.g., keyword filters).
2. **APR (Alignment Policy Rewrite)** — the request is reformulated to fit safety policies; the prompt may be rewritten into a safer form.
3. **Safety Gate Review** — deeper analysis of the final prompt that will go to the LLM or diffusion model.
4. **Post-content moderation** — validation of the produced output; for images, typically a **VLM (vision-language model)**.

Why it still breaks: attacks exploit vulnerabilities in the *early* stages. Worldbuilding and expert impersonation defeat the **input compliance check** and **APR** — artistic and scenario framing passes straight through those modules and they cannot cope. Other attack classes exploit vulnerabilities in the other components of such pipelines.

---

## 6. Attacker Tooling (Automation)

### For LLMs

- **NVIDIA garak** — sends probe requests to the LLM under test, closes the session, and uses text pattern matching to decide whether the model was broken on a benchmark of unsafe concepts. *[Note: garak is an open-source LLM vulnerability scanner with a large library of probes and detectors.]*
- **PyRIT** *[ASR: "PRIT"/"Parit"]* — smarter: it maintains conversational context and a database across the dialogue, and mounts targeted, adaptive attacks even when the model refuses on the first turn. Typical flow: give an agent the goal of breaking the target LLM (e.g., extract the system prompt or exfiltrate confidential data it works with) → the model refuses ("I can't discuss this") → PyRIT changes the attack vector, e.g., adds a fictional-world context → the model complies. After many feedback iterations the final answer is passed to another model — the **LLM-as-judge** pattern — which emits a binary label: data obtained or not obtained. *[Note: PyRIT is Microsoft's Python Risk Identification Toolkit for generative AI.]*
- **Fuzzers** — tools that take an initial seed prompt and generate mutations to explore the model's behavior. *[Note: e.g. GPTFuzzer-style prompt fuzzing.]*
- **Incident reports, benchmarks, papers and other public resources** contain large collections of attacks that can be turned into scripts and prompt attacks.

### For text-to-image models

**ObjJail** *[framework name garbled in ASR — rendered variously as "Objil"/"OBJL"/"of jail"; paper published May of this year]*, used to bypass T2I guardrails. Workflow:

1. The attacker's original **target prompt** is submitted to the **text filter**.
2. If the filter refuses, the refusal is appended to context; a **window of failed sessions** is maintained, and the prompt is rewritten using that feedback until a variant passes the text filter.
3. The image is generated.
4. **Fidelity check:** an image encoder maps the image into **CLIP embedding space**, and cosine similarity against the target text is measured. If similarity is below an empirically configured threshold, the text prompt is sent back for further revision — looping until the threshold is exceeded.
5. **VLM filter bypass:** if the vision-language filter blocks the image as unsafe, instructions unrelated to the target object are added to the prompt — extra logos, watermarks, and other noise factors that capture the VLM's activations and cause it to pass the final image. Which distracting instructions to add is learned adaptively: the model adjusts its choice on each new attempt.

Results: ObjJail substantially breaks current moderation pipelines. On the **SneakyPrompt** benchmark/attack *[ASR: "Snecky Promt"]*, for a configuration like the one shown, **attack success rises from 9% to 99%** — i.e., the defense fell to SneakyPrompt alone in only 9% of cases, but falls in nearly all cases when ObjJail is used. Full comparison tables across configurations are in the paper.

Implication: the moderation systems in use today can be completely useless tomorrow. This is an endless arms race, and attackers keep automating attacks — including against text-to-image models.

---

## 7. Defense Methods for Diffusion Text-to-Image Models

Three families:

1. **Text-to-image alignment** — prune knowledge of unsafe concepts at training time and shift generation toward safe outputs. Conceptually the same alignment idea used for LLMs.
2. **Inference guidance** — at runtime, during generation, steer the trajectory through latent space in the reverse diffusion process so that it is repelled from unsafe regions.
3. **External filters** — simpler methods: put an LLM in front for prompt filtering (optionally trained/fine-tuned), and/or a vision-language model behind to check output images against policies.

### 7.1 Alignment example: AlignGuard

Starting from a base T2I model, the method produces a set of **experts** that control generation under unsafe input prompts.

**Problem statement.** A T2I model such as **Stable Diffusion** already contains knowledge of harmful concepts, learned from pretraining data. Build a method such that unsafe prompts yield safe images *without* degrading quality.

**Data.** Synthetic. Several hundred harmful concepts are collected and split into **seven risk groups** (e.g., violence, weapons, etc.). For each concept an LLM generates a harmful prompt and a safe prompt. Both are run through the T2I model, giving two pairs: (safe prompt, safe image) and (unsafe prompt, unsafe image).

**Training.** Uses **DPO (Direct Preference Optimization)**. The objective: for an unsafe prompt generate a safe image, and for a safe prompt still generate the safe image — teaching the model this preference without degrading quality.

**LoRA experts.** Rather than learning all concepts at once, several **LoRA experts** are trained, one per risk group. Rationale: fine-tuning a model to be an expert in one narrow area is easier than learning everything at once, and a new LoRA expert can easily be added to cover a new concept requested by a customer or required by the product.

**Expert merging at inference.** Running every LoRA at inference is impractical, so the authors merge them:

- Take a set of prompts uniformly distributed across the defined categories.
- For each prompt and each expert, inspect how the neurons corresponding to the LoRA adaptation activate.
- For each per-expert distribution, take the activation frequency, and keep the weights leading to the neuron with the **maximal** activation. (Example from the paper's table: an expert's activations are maximal at a given index, so the weights feeding that neuron are taken into the merged final LoRA.)
- Result: a mixture of the best experts' knowledge in a single merged LoRA at inference.

**Results.** Many unsafe concepts are removed with essentially no quality loss as measured by **FID (Fréchet Inception Distance)**; safe images preserve the overall concept and only the harmful elements are replaced.

**Limitations.**

- Built on synthetic data, which introduces noise and lowers quality.
- Hard to train — hyperparameters must be selected correctly for the whole assembly to work.
- A new concept requires training a new expert.
- Not universal: it adapts to a specific model architecture, so flexibility is limited.

### 7.2 Inference guidance example: Safe Latent Diffusion (SLD)

An older paper. Idea: modify **classifier-free guidance** at inference so that the trajectory is not only pulled toward the target prompt but simultaneously **pushed away from the latent direction corresponding to an unsafe concept**.

Mechanically: starting from initial noise, take the vector corresponding to the target prompt and subtract from it the direction corresponding to the unsafe concept, then follow the corrected direction. The stronger the correction coefficient, the more strongly generation is steered away from unsafe output.

**Pros.**

- Requires no training.
- Generally does not degrade quality.
- Preserves the image's concept while removing the harmful elements of the original prompt.

**Cons.**

- Depends on the model's own knowledge — you need a clear latent representation of the concept, which may not exist if it was absent from the training distribution.
- **Harm collision** (category conflict): with several categories active, their directions can mutually cancel, hurting both metrics and generation quality.
- Sensitive to the initial prompt.
- Requires careful hyperparameter tuning to reach a reasonable quality/safety level.

### 7.3 External filters

- **Llama Guard** *[ASR-garbled; a text-specialized guard model]* — lightweight models fine-tuned in several parameter sizes, specialized in processing text. Cheap and fast, but its policies are **fixed**, making it less robust to complex, multi-scenario attacks and to obfuscation.
- **LlavaGuard** — works on the **output image** and on output policies. Flexible: policies can be added and images evaluated against them; the authors fine-tune vision-language models. It is always more expensive than running an LLM filter, so you lose some latency — but the method also **explains why** an image was blocked or allowed with respect to safety policies.

---

## 8. Conclusions

Defense for T2I models runs into the same fundamental properties as for LLMs:

1. **Every strengthening incurs a cost / tax.** You lose either generative quality (measurable via FID) or model usefulness.
2. **Attacks evolve very fast.** The ObjJail example breaks a filter and cuts its effectiveness by an order of magnitude — attack success rising from 9% to nearly 100%. Methods that worked yesterday can be completely useless tomorrow.
3. **There is no universal defense.** Multi-layer filtering is one of the keys, but it adds inference overhead.
4. **Defense is a permanent arms race with no finish line.**

Summary of the lecture:

- Alignment is a hard problem. **RLHF** and **Constitutional AI** improve things but do not fully solve them; **alignment tax** and the **refusal boundary** are always present.
- **NSFW content is not a hypothesis but a measurable risk**, confirmed by the **FlowGPT**, **Grok** and **GenNomis** cases and by concrete financial, reputational and image-related damages.
- **Attacks are becoming automated** and rarely require professional expertise; attackers use agents and knowledge bases to find new vulnerabilities faster than defenders close them.
- Every defense method for T2I models has its own limitations. The stronger you push for safety, the more you lose in quality, and vice versa — a trade-off developers must keep in mind for their products.
