# LinkedIn Post Schedule — one post per week (Aug 29 → Sep 18, 2026)

> **Cadence:** post 1 goes out today, Sat 29 Aug. Posts 2–4 go out on Fridays.
> `scripts/linkedin_post_reminder.py` runs from cron every Friday at 09:47 and
> prints the post that is due, so nothing needs remembering.

> Author voice: **Arslan Noor, CTO** (personal profile — better reach than the company page).
> To run from the ElectroCom company page instead, swap "I" → "our team" and drop the
> first-person opinion lines. Both versions of the tone work; personal pulls more.
>
> Rules applied: no em dashes, no hashtags, no semicolons, no links in the post body
> (links go in the first comment), 1–3 line paragraphs, and **every post ends on the
> solution, not a question** (Arslan, 2026-08-29 — the audience is too small for a
> closing question to get answered, and an unanswered one makes the post look dead).
>
> Three topics were given, the month has four Saturdays. Week 4 is a synthesis post that
> ties the other three together and points back at them.

| Week | Date | Topic | Status |
|---|---|---|---|
| 1 | 2026-08-29 | AWS Bedrock AgentCore | **posted** |
| 2 | 2026-09-04 | In-house CAD engineers for AI model evaluation | ready |
| 3 | 2026-09-11 | Oracle Integration Cloud | ready |
| 4 | 2026-09-18 | Synthesis: the three layers under every AI project | ready |

---

# PART 1 — SHORT POSTS (primary, post these)

Tweet-length. One idea, one hard specific, then the fix. No links in the body.

**Closing rule: end on the solution, never on a question.** The audience is still
small, so a question at the end goes unanswered and makes the post read as dead.
A post that ends with the fix pays the reader who never comments, and it is the
part that shows we know how to do the work. Long-form versions of the same four
are in Part 2 if a topic starts pulling and you want to go deeper on it later.

## Week 1 — 2026-08-29 — AWS Bedrock AgentCore (533 chars)

```
Your agent demo works. Shipping it is a different project.

Two users share a session. Nobody decided whose credentials the tool call uses. State lives in a dict that dies with the process.

None of that is a model problem.

What fixes it: give every session its own isolated runtime, move state into a managed memory store, put tool access behind one gateway, and attach a real identity to the agent.

AgentCore ships all four, so the work is configuration rather than construction.

Do that before you touch the prompts.

#AIAgents #AWS #Bedrock #AIEngineering
```

**Alt hook, same body:** `Nobody's agent fails because the model was not smart enough.`
**First comment:** `AWS's overview of the components, if you want the short read: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html`

---

## Week 2 — 2026-09-04 — CAD engineers in the eval loop (541 chars)

```
A model scoring 90 on your benchmark tells you nothing about whether the part is buildable.

Wall thickness under what the tooling holds. A fillet no cutter reaches. Tolerances stacked so the assembly never closes.

The metric reads that as a pass. A CAD engineer reads it as scrap.

So we put the engineer in the grading seat. They score output on manufacturability, tolerance realism and load path, and every rejection goes back into the eval set as a labelled failure.

Your real benchmark is the person who signs off in production.

#AIEvaluation #MachineLearning #CAD #Manufacturing
```

**Alt hook, same body:** `Your eval set is green because the reviewer was never allowed near it.`
**First comment:** `Same argument holds for clinical notes, structural calcs, contracts. If your reviewer only sees the output after launch, then launch is your first real eval.`

---

## Week 3 — 2026-09-11 — Oracle Integration Cloud (545 chars)

```
Oracle Integration Gen 2 died on 31 August 2025.

A year later plenty of teams are running Gen 2 integrations on Gen 3. Connectivity agents nobody retired. Process never split out. Five minute polling where an event already exists.

It never breaks loudly. It eats your integration team's week.

The second pass is the fix. Retire the agents you no longer need. Split Process out properly. Replace polling with events. Put observability on the flows that touch revenue.

Migration was the deadline. The rebuild is the part that pays.

#Oracle #OracleIntegrationCloud #EnterpriseIntegration #DigitalTransformation
```

**Alt hook, same body:** `Your OIC migration finished a year ago. Your integration debt did not move.`
**First comment:** `Oracle's own Gen 3 migration guidance, for anyone still working through it: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmic/oic-gen-3-migration.html`

---

## Week 4 — 2026-09-18 — The three layers (556 chars)

```
Most AI projects stall for the same three reasons. None of them is the model.

No runtime. The agent holds state in memory and shares one API key across every user.

No real evaluation. Every score is green and the expert who signs off has never seen the eval set.

No foundation. The AI sits on integrations that already need weekly babysitting.

Fix them in that order. Isolated runtime and managed state first. Then your domain expert grading real output. Then the data layer underneath.

The model is the part that already works.

#AI #AIEngineering #MLOps #TechLeadership
```

**Alt hook, same body:** `Every team wants to start with the model. It is the wrong end to start.`
**First comment:** `Wrote each of these up on its own over the last month. AgentCore, evaluation, integration. All on this profile if you want the long version of any one.`

---

# PART 2 — LONG-FORM VERSIONS (fallback, only if a topic pulls)

---

## Week 1 — 2026-08-29 — AWS Bedrock AgentCore

**Audience:** CTOs and heads of engineering at Seed–Series B companies with a working agent demo and no path to production.
**Goal:** Read ElectroCom as the team that takes agents from demo to production. Reply or DM.
**Core insight:** The prototype-to-production gap for agents is infrastructure, not intelligence.
**Proof:** AgentCore's own component list (Runtime, Memory, Gateway, Identity, Observability) reads as a list of the failures teams hit. Firecracker microVM per session, terminated and sanitised after. Gateway converts existing APIs and Lambdas into MCP tools. Framework-agnostic.
**Format:** Contrarian Opinion — the common assumption is that better models fix agent reliability.
**Hook used:** #1 Contrarian.

### Hook variants

1. **Contrarian (48 chars):** `Your agent demo works. Shipping it is a different project.`
2. **Mistake/Lesson (74 chars):** `The agent broke in production for a reason nobody wrote a prompt to fix.`
3. **Provocative, boldest (66 chars):** `Nobody's agent fails because the model was not smart enough.`

### POST (1,247 chars)

```
Your agent demo works. Shipping it is a different project.

Watch what breaks first.

Two users share a session and one of them sees the other's context. The agent needs to call an internal API and nobody has decided whose credentials it uses. Conversation state lives in a dict that dies with the process. A run takes nine minutes and there is no trace to explain where it went.

None of that is a model problem. All of it is infrastructure.

That is the shape of why AWS built Bedrock AgentCore the way they did. Read the component list as a list of the walls teams hit on the way to production. Runtime. Memory. Gateway. Identity. Observability.

Runtime gives every session its own Firecracker microVM, keeps it alive across invocations, then terminates it and sanitises the memory. Cross-session leakage stops being something you defend against in your own code.

Gateway turns the APIs and Lambda functions you already run into MCP tools. Your agent reaches existing systems instead of a new integration layer somebody has to own.

It stays framework agnostic. LangGraph, CrewAI, Strands. The agent logic survives the move.

The teams shipping agents this year are not the ones with the best prompts. They are the ones who treated the runtime as a real engineering problem.

Isolate the session, manage the state, gateway the tools, name the identity. Then go back to the prompts.
```

### Spicier variant

Changed: the opening is blunter and the closing line names the mistake instead of implying it. Sharper, same length.

```
Nobody's agent fails because the model was not smart enough.

Watch what breaks first.

Two users share a session and one of them sees the other's context. The agent needs to call an internal API and nobody has decided whose credentials it uses. Conversation state lives in a dict that dies with the process. A run takes nine minutes and there is no trace to explain where it went.

None of that is a model problem. All of it is infrastructure.

That is the shape of why AWS built Bedrock AgentCore the way they did. Read the component list as a list of the walls teams hit on the way to production. Runtime. Memory. Gateway. Identity. Observability.

Runtime gives every session its own Firecracker microVM, keeps it alive across invocations, then terminates it and sanitises the memory. Cross-session leakage stops being something you defend against in your own code.

Gateway turns the APIs and Lambda functions you already run into MCP tools. Your agent reaches existing systems instead of a new integration layer somebody has to own.

Six months of prompt tuning will not fix any of this. It is a platform problem and it always was.

The teams shipping agents this year are not the ones with the best prompts. They are the ones who stopped pretending the runtime was somebody else's job.

Isolate the session, manage the state, gateway the tools, name the identity. Then go back to the prompts.
```

### First comment (pick one, post immediately after publishing)

- **C1 — source + context:** `AWS's own overview of the AgentCore components is the clearest short read on this: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html`
- **C2 — discussion driver:** `The part I am still working out: how much of Memory to hand to AgentCore versus keeping in your own store. Where have you drawn that line?`
- **C3 — deeper context:** `Session isolation detail for anyone who wants it, including what happens to the microVM after a session ends: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html`

---

## Week 2 — 2026-09-04 — In-house CAD engineers for AI model evaluation

> **Check before posting:** this post states publicly that ElectroCom has CAD engineers
> in the evaluation loop. Confirm that is accurate and currently true.

**Audience:** Founders and ML leads building models that produce engineering, design or other expert-reviewed output.
**Goal:** Read ElectroCom as a team that does evaluation seriously, not just model plumbing. Reply or DM.
**Core insight:** A benchmark score tells you nothing about whether the output is buildable. Only the expert who signs off in production knows that.
**Proof:** Named, concrete CAD failure modes that a similarity metric scores as a pass.
**Format:** Contrarian Opinion — the common assumption is that eval means a metric.
**Hook used:** #1 Contrarian.

### Hook variants

1. **Contrarian (94 chars):** `A model scoring 90 on your benchmark tells you nothing about whether the part is buildable.`
2. **Framework Reveal (67 chars):** `Three things a CAD engineer catches that no eval metric will.`
3. **Provocative, boldest (72 chars):** `Your eval set is green because the reviewer was never allowed near it.`

### POST (1,286 chars)

```
A model scoring 90 on your benchmark tells you nothing about whether the part is buildable.

That gap is why we keep CAD engineers in the evaluation loop, not only metrics.

The pattern repeats. A team fine tunes a model on engineering drawings or 3D geometry. The eval suite reports geometric similarity, token overlap, a preference score from a second model. Every number moves the right way.

Then somebody tries to make the part.

Wall thickness under what the tooling holds. A fillet no cutter reaches. A bracket whose load path runs through its thinnest section. Tolerances stacked so the assembly never closes.

A similarity metric reads all of that as a pass, because the output looks correct.

An engineer who has run a part through production reads it as scrap.

So the grading seat belongs to a person. Our engineers score output on manufacturability, tolerance realism and load path, and every rejection goes back into the eval set as a labelled failure. The model gets measured against the thing the customer receives.

This holds anywhere a domain expert signs off on model output. Drawings. Clinical notes. Structural calculations. Contracts.

If the person who reviews that output in real life is not in your evaluation loop, you are measuring a proxy and calling it quality.

Put your reviewer in the loop, score on what production cares about, and feed every rejection back as a labelled failure. Your real benchmark is the person who signs off.
```

### Spicier variant

Changed: the second line accuses rather than explains, and the closing swaps a soft question for a direct one. Same length.

```
Your eval set is green because the reviewer was never allowed near it.

Benchmarks measure whether output looks right. Experts measure whether it works.

The pattern repeats. A team fine tunes a model on engineering drawings or 3D geometry. The eval suite reports geometric similarity, token overlap, a preference score from a second model. Every number moves the right way.

Then somebody tries to make the part.

Wall thickness under what the tooling holds. A fillet no cutter reaches. A bracket whose load path runs through its thinnest section. Tolerances stacked so the assembly never closes.

A similarity metric reads all of that as a pass. An engineer who has run a part through production reads it as scrap.

Which is why we put CAD engineers in the grading seat. They score output on manufacturability, tolerance realism and load path, and every rejection goes back into the eval set as a labelled failure.

Hiring domain experts to grade a model is slower and more expensive than a metric. It is also the only version that survives contact with a customer.

This holds anywhere an expert signs off. Drawings. Clinical notes. Structural calculations. Contracts.

Name the person who reviews your model's output in production. Put them in the eval loop, score on what they actually reject for, and label every failure. That is the whole method.
```

### First comment

- **C1 — context, no link needed:** `To be specific about the failure that started this: geometrically the output matched the reference almost exactly. It was still unmanufacturable in three separate places.`
- **C2 — discussion driver:** `The part I am still working out: how many expert-graded samples you need before the labelled failures start generalising. Where has that landed for your team?`
- **C3 — expand reach beyond CAD:** `Same argument applies to clinical, legal and structural output. If your reviewer only sees the model after launch, launch is your first real eval.`

---

## Week 3 — 2026-09-11 — Oracle Integration Cloud

**Audience:** IT directors, integration leads and enterprise architects who moved to OIC Gen 3 under the deadline.
**Goal:** Read ElectroCom as the team that does the second pass, and connect OIC work to AI readiness. Reply or DM.
**Core insight:** The Gen 2 deadline forced a lift and shift. A year later the migration is done and the modernisation never happened, which is also what blocks AI on top.
**Proof:** Gen 2 stopped accepting new instances on 20 March 2025 and retired on 31 August 2025. Gen 3 separated Integrations and Process into their own components.
**Format:** Contrarian Opinion — the common assumption is that the migration is finished.
**Hook used:** #1 Contrarian.

### Hook variants

1. **Contrarian (98 chars):** `Oracle Integration Gen 2 died on 31 August 2025. Plenty of teams are still running Gen 2 on Gen 3.`
2. **Specific Result (61 chars):** `A migration deadline is not a modernisation plan.`
3. **Provocative, boldest (80 chars):** `Your OIC migration finished a year ago. Your integration debt did not move.`

### POST (1,299 chars)

```
Oracle Integration Gen 2 died on 31 August 2025. Plenty of teams are still running Gen 2 integrations on Gen 3.

The deadline forced a lift and shift. Under that time pressure it was the right call. It also left the job half done.

What tends to still be sitting there.

Connectivity agents kept for integrations that no longer need one. Process flows never separated out after Gen 3 split Integrations and Process into their own components. Scheduled jobs polling on a five minute timer where an event already exists. Error handling that writes to a log nobody opens. Credentials living in mappings instead of connections.

None of it breaks loudly. It shows up as an integration team spending its week on reruns and reconciliations instead of new work.

The second pass is where the value sits. Retire the agents you no longer need. Split Process out properly. Replace polling with events. Put real observability on the flows that touch revenue.

Then the interesting part becomes available. Once your integrations are clean and event driven, an agent has somewhere to stand. Order exceptions triaged before anyone opens a ticket. Invoice mismatches explained rather than queued.

That never works on top of integrations your own team does not trust.

Migration was the deadline. The rebuild is the project.

Retire the agents. Split Process out. Replace polling with events. Instrument the flows that touch revenue. That is the second pass, and it is the one that pays.
```

### Spicier variant

Changed: the opening names the uncomfortable truth directly, and the AI section stops hedging. Same length.

```
Your OIC migration finished a year ago. Your integration debt did not move.

Gen 2 retired on 31 August 2025 and the deadline forced a lift and shift. That was the right call at the time. Calling it modernisation is where teams went wrong.

Look at what is still sitting there.

Connectivity agents kept for integrations that no longer need one. Process flows never separated out after Gen 3 split Integrations and Process into their own components. Scheduled jobs polling on a five minute timer where an event already exists. Error handling that writes to a log nobody opens. Credentials living in mappings instead of connections.

None of it breaks loudly. It shows up as an integration team spending its week on reruns and reconciliations instead of new work.

Now here is the expensive part. Every one of those teams also has an AI mandate this year. Order exception triage. Invoice matching. Automated reconciliation.

An agent sitting on integrations your own team does not trust will make bad data move faster. That is the whole result.

The second pass is not optional and it is not cosmetic. Retire the agents. Split Process out. Replace polling with events. Instrument the flows that touch revenue.

Migration was the deadline. The rebuild is the project, and it is the one that pays.

Retire the agents. Split Process out. Replace polling with events. Instrument the flows that touch revenue. That is the second pass, and it is the one that pays.
```

### First comment

- **C1 — source + context:** `Oracle's own Gen 3 migration guidance, for anyone still working through it: https://docs.oracle.com/en/cloud/saas/transportation/26a/otmic/oic-gen-3-migration.html`
- **C2 — discussion driver:** `The one I keep seeing argued: whether to split Process out during the move or leave it for a later pass. Which way did you go, and would you repeat it?`
- **C3 — sharpen the AI link:** `The cleanest AI wins we have seen on OIC were not new models. They were event driven flows that finally made the data reliable enough to act on.`

---

## Week 4 — 2026-09-18 — Synthesis: the three layers under every AI project

**Audience:** Founders and CTOs with an AI project that has not reached customers.
**Goal:** Position ElectroCom across all three capabilities in one post, and pull replies naming which layer is stuck. DM.
**Core insight:** AI projects stall on the runtime, the evaluation loop, or the integration layer. Never on the model.
**Proof:** Each of the three references the concrete argument from the earlier posts in this month.
**Format:** Framework Post — three named failure modes.
**Hook used:** #4 Framework Reveal.

### Hook variants

1. **Framework Reveal (79 chars):** `Most AI projects stall for the same three reasons. None of them is the model.`
2. **Contrarian (66 chars):** `The model is the part of your AI project that already works.`
3. **Provocative, boldest (72 chars):** `Every team wants to start with the model. It is the wrong end to start.`

### POST (1,214 chars)

```
Most AI projects stall for the same three reasons. None of them is the model.

Enough of these have crossed my desk to name the pattern.

One. No runtime. The agent runs on a laptop, holds state in memory, and shares one API key across every user. Somebody asks about session isolation and the room goes quiet. This is exactly the problem Bedrock AgentCore was built for, and the fix is infrastructure work, not prompt work.

Two. No real evaluation. Every score is green and the expert who reviews the output in production has never seen the eval set. For engineering output we put a CAD engineer in the grading seat, because a similarity metric reads an unmanufacturable part as a pass. Your domain will have its own version of that person. Put them in the loop.

Three. No foundation. The AI layer sits on integrations that already need weekly babysitting. An agent that reads bad data faster is not an improvement, it is a louder failure.

Every team wants to start with the model. The model is the part that already works.

The three unglamorous layers underneath are what separate a demo from something your customers depend on.

Fix them in that order. Runtime and state first. Then your domain expert grading real output. Then the data layer underneath.
```

### Spicier variant

Changed: the diagnosis lines are blunter and the close names the cost of getting the order wrong. Same length.

```
Every team wants to start with the model. It is the wrong end to start.

Enough stalled AI projects have crossed my desk to name the pattern, and the model was never the reason.

One. No runtime. The agent runs on a laptop, holds state in memory, and shares one API key across every user. Ask about session isolation and the room goes quiet. Bedrock AgentCore exists because this is a platform problem, and no amount of prompt tuning touches it.

Two. No real evaluation. Every score is green and the expert who reviews the output in production has never seen the eval set. We put a CAD engineer in the grading seat for engineering output, because a similarity metric reads an unmanufacturable part as a pass. Your domain has its own version of that person. You skipped them.

Three. No foundation. The AI layer sits on integrations that already need weekly babysitting. An agent reading bad data faster is not an improvement, it is a louder failure.

Six months of model work will not save a project missing any one of these. That is why the demo impressed everyone and nothing shipped.

Fix them in that order. Runtime and state first. Then your domain expert grading real output. Then the data layer underneath.
```

### First comment

- **C1 — thread the month together:** `Wrote these up one at a time over the last month. The AgentCore, evaluation and integration posts are all on this profile if you want the long version of any of the three.`
- **C2 — discussion driver:** `My guess is number three is the most common and the least talked about. Which one would you say costs teams the most?`
- **C3 — soft CTA:** `If you are stuck on one of the three, say which. Happy to give a straight read on it in the comments.`

---

## Results log (fill in ~48h after each post)

Fill this in and the next month's topics pick themselves. Without it we are guessing.

| Week | Topic | Posted | Impressions | Reactions | Comments | Profile views / connects | Notes |
|---|---|---|---|---|---|---|---|
| 1 | AgentCore | 2026-08-29 | | | | | first post of the run, no baseline yet |
| 2 | CAD eval | | | | | | |
| 3 | Oracle OIC | | | | | | |
| 4 | Three layers | | | | | | |

---

## Posting checklist (run before each post)

- [ ] Post body has no links. Links live in the first comment.
- [ ] First comment is ready to paste within a minute of publishing.
- [ ] No em dashes, no hashtags, no semicolons in the body.
- [ ] Every factual claim traces to source. Dates and product names verified.
- [ ] Reply to every comment inside the first two hours.
- [ ] Log the post in `reports/YYYY-MM-DD.md` under `Assets`.
