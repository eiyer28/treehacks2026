# MirrorVerse — Presentation Deck
# TreeHacks 2026

---

## SLIDE 1: Title

**MirrorVerse**
*Sim-Validated Edge AI Robotics for Disaster Response*

Eashan Iyer, Samuel Lihn, Gordon Jin, Trevor Kwan
TreeHacks 2026

---

## SLIDE 2: The Problem

**When disasters strike, robots can't think for themselves — and humans can't reach them.**

- 2023 Turkey-Syria earthquake: 59,000+ dead, 10,000+ buildings collapsed
  - Secondary aftershock collapses killed additional victims and endangered 53,000+ deployed rescue workers
  - Source: UNDP, Center for Disaster Philanthropy

- March 2025 Myanmar earthquake: 3,600+ dead, 10,000+ buildings collapsed or severely damaged
  - A 6.4 aftershock hit while rescue operations were active
  - Source: WHO, AHA Centre

- In these environments, cell towers are down. Cloud APIs are unreachable. But the need for autonomous robots is at its peak.

**The question: How do you make a robot that can build, reinforce, and clear — safely — with zero internet?**

---

## SLIDE 3: The Insight

**The most dangerous thing an autonomous robot can do is act without checking its work.**

An LLM can plan a construction task. But LLMs hallucinate — they can propose structures that are physically impossible or unstable.

Current approaches:
- Cloud-based VLAs (like Gemini Robotics 1.5) require massive models and internet connectivity
- Standard digital twins mirror reality but don't plan ahead
- Text-to-robot systems are one-shot — no validation before execution

**What's missing: a physics sanity-check that runs locally, before the robot commits.**

---

## SLIDE 4: Our Solution

**MirrorVerse: Plan. Simulate. Validate. Build.**

An AI system that runs entirely on edge hardware:

1. **You prompt it** — "Build a reinforced shelter" (natural language)
2. **It plans** — Local LLM on DGX Spark decomposes the task into subtasks
3. **It simulates** — Isaac Sim tests each action: will this block fall? Will this structure survive lateral forces?
4. **It validates** — Only actions that pass physics checks are sent to the real robot
5. **It builds** — SO-101 arm executes the validated plan
6. **It adapts** — If the real world doesn't match the sim (block slipped, misaligned), the system re-plans

No cloud. No internet. Fully autonomous.

---

## SLIDE 5: The Demo — Earthquake Test

[This slide should show a diagram or live demo of the following sequence]

**Step 1: Prompt** — "Build a tower"
- DGX Spark LLM breaks this into pick-and-place subtasks

**Step 2: Build** — Physical arm stacks blocks
- Isaac Sim mirrors every move in real time (split screen)

**Step 3: Stress Test** — Simulate an earthquake
- Isaac Sim applies lateral forces to the digital twin
- The tower collapses in simulation (the real tower is untouched)

**Step 4: Redesign** — AI sees the failure
- LLM analyzes the collapse, redesigns with a wider base and interlocking pattern

**Step 5: Rebuild** — Arm deconstructs and rebuilds the reinforced version
- Isaac Sim confirms the new design survives the same earthquake

**The punchline: The AI broke it in simulation so it wouldn't break in reality.**

---

## SLIDE 6: Architecture

**Three devices. Four agents. Zero cloud dependency.**

```
[Voice/Text Prompt]
        |
        v
  +-----------------+
  |   DGX Spark     |  Agent C: "The Overlord"
  |   Local LLM     |  Plans tasks, decomposes prompts,
  |                 |  orchestrates all agents
  +-----------------+
        |
   subtasks
        |
   v              v
+-----------+  +-----------------+
| Jetson    |  | RTX 3070 Laptop |
| Orin Nano |  | Isaac Sim       |
|           |  |                 |
| Agent A:  |  | Agent B:        |
| "Builder" |  | "Architect"     |
| VLM +     |  | Physics sim,    |
| Motor     |  | stress testing, |
| control   |  | validation      |
+-----------+  +-----------------+
     |                |
     v                v
  [SO-101 Arm]   [Digital Twin]
     |                |
     +--- feedback ---+

Agent D: "The Operator" — Human override via Leader Arm
(safety-critical fallback when autonomy fails)
```

---

## SLIDE 7: Why Edge Matters

**This is not a cloud project that happens to use hardware.**
**This is a hardware-native system designed for environments where cloud doesn't exist.**

| | Cloud Robotics | MirrorVerse |
|---|---|---|
| Internet required | Yes | No |
| Latency | 100-500ms round trip | <10ms local |
| Works in disaster zone | No | Yes |
| Works on Mars (20-min delay) | No | Yes |
| Physics validation | None | Every action |

The same architecture that validates a block tower on a table validates a structural reinforcement in a collapsed building.

---

## SLIDE 8: The Market

**This sits at the intersection of two rapidly growing markets.**

Disaster Response Robotics:
- $2.5B in 2024, projected $6.2B by 2033 (10.5% CAGR)
- Search & rescue robots: $35.3B in 2025, projected $70.3B by 2030 (14.8% CAGR)
- Sources: Verified Market Reports, Mordor Intelligence

Digital Twin Technology:
- $35.8B in 2025, projected $328.5B by 2034 (31.1% CAGR)
- NVIDIA Omniverse already deployed by TSMC, BMW, Siemens for factory digital twins
- Source: GM Insights, Grand View Research

Edge AI for Robotics:
- NVIDIA investing heavily: Jetson platform, Isaac Sim, DGX Spark all launched for exactly this use case
- $1.2 trillion in 2025 US manufacturing investment driving robotics adoption
- Source: NVIDIA Newsroom

**No one has combined all three for autonomous disaster response.**

---

## SLIDE 9: What Makes This Novel

**We didn't invent the components. We composed them in a way no one has.**

| Existing Approach | What They Do | What We Add |
|---|---|---|
| Digital Twins (Siemens, BMW) | Mirror reality for monitoring | Active planning + validation before execution |
| Sim-to-Real (OpenAI, DeepMind) | Train in sim, deploy to real | Run both simultaneously as coordinating agents |
| Text-to-Robot (VoxPoser, RoboGPT) | One-shot: prompt to action | Iterative: prompt to sim to validate to action |
| Cloud VLAs (Gemini Robotics 1.5) | Think before acting (cloud) | Think before acting (fully local, edge hardware) |

**The bidirectional feedback loop is the key innovation:**
Sim proposes a design. Robot tries to build it. Robot reports failures. Sim adapts the design. This is multi-agent collaboration, not one-way mirroring.

---

## SLIDE 10: Beyond Disaster Response

**The system is fully generalizable. The demo is blocks. The architecture is universal.**

Same plan-simulate-validate-execute loop applies to:

- **Hazmat decommissioning** — Test a cutting procedure in sim before committing a robot in a radioactive environment
- **Remote space construction** — Build a habitat in simulation on Earth, execute the validated plan on Mars where 20-minute signal delay makes teleoperation impossible
- **Precision manufacturing** — Simulate micro-assembly before a robot places a component worth thousands of dollars
- **Infrastructure inspection** — Simulate load redistribution before a robot removes a damaged bridge section

The prompt changes. The manipulator changes. The physics engine stays the same.
**If you can simulate it, you can validate it. If you can validate it, you can trust a robot to do it.**

---

## SLIDE 11: Hardware on the Table

[Photo of actual setup]

| Device | Role | Why |
|---|---|---|
| NVIDIA DGX Spark | Local LLM (planning + orchestration) | Powerful enough to run a capable LLM with zero internet |
| NVIDIA Jetson Orin Nano Super | Perception + motor control | Edge AI inference for VLM, drives the arm in real time |
| RTX 3070 Laptop | Isaac Sim (physics validation) | Runs full physics simulation for stress testing |
| SO-101 Follower Arm | Physical manipulation | Executes validated construction plans |
| SO-101 Leader Arm | Human override | Operator takes control when autonomy hits an edge case |
| 2x Mono Cameras | Stereo perception | Tracks block positions, feeds digital twin |

---

## SLIDE 12: Live Demo

[LIVE DEMO HERE]

"Build a tower. Break it in simulation. Redesign it. Rebuild it stronger."

---

## SLIDE 13: Closing

**MirrorVerse**

An AI system that plans a construction task, simulates it to check for structural failure, and only then tells the robot to build. If the simulation says it'll collapse in an earthquake, the AI redesigns it and the robot rebuilds.

Fully local. Fully autonomous. Physics-validated safety.

Built for the places where cloud doesn't reach and mistakes cost lives.

---

## APPENDIX: Prize Track Alignment

| Prize | Why We Fit |
|---|---|
| **NVIDIA Edge AI Track** | DGX Spark + Jetson + Isaac Sim — the full NVIDIA edge stack |
| **NVIDIA Open Models Challenge** | Multi-agent system built on NVIDIA open models and hardware |
| **Best Hardware Hack** | 3 NVIDIA devices + 2 robot arms + stereo cameras |
| **Most Technically Complex** | Local LLM + VLA + physics sim + multi-agent orchestration across 3 devices |
| **Greylock Best Multi-Turn Agent** | 4 agents reasoning about feedback to complete multi-step construction |
| **Grand Prize** | Innovation + complexity + social impact in one demo |
