# TreeHacks 2026
Eashan Iyer, Samuel Lihn, Gordon Jin, Trevor Kwan

Project: 
We are building a generalized edge AI construction system for the Treehacks 2026 hackathon at Stanford. It demonstrates two robotic agents—one physical (in the real world) and one virtual (in NVIDIA Isaac Sim)—working together on a single shared task.

The premise is that you can prompt an LLM that runs locally on a DGX spark, which is used for planning and is the brains behind the operation. This can do a wide range of tasks. From there the LLM passes subtasks into the Jetson, which then uses VLA/VLM and a smaller LLM to turn this subtask into code that can run on the robotic arm.

To get a sense of capabitilies, we could build something like a tower of blocks. The prompt would be turned into subtasks and then run on the robotic arm. We would simulate actions on Isaac Sim and use that to prevent hallucination. We would also use it to simulate things like lateral forces as a simplified model of earthquakes. From there we could show that the current tower would break, then the AI would redesign the tower and then it would be rebuilt using this feedback loop to reinforce the structure. 

This system is built entirely on edge AI — the LLM runs locally on the DGX Spark, perception runs on the Jetson, and physics validation runs on a local GPU. No cloud. No internet required. That architectural choice unlocks the highest-stakes use case: disaster response. When an earthquake levels a building, cell towers go down and cloud APIs become unreachable, but the need for autonomous robots is at its peak. A system like this could direct robots to shore up unstable structures, clear debris from access routes, or assemble temporary shelters — all while simulating each action first to avoid making a collapse worse. The demo we show (building a block tower, earthquake-testing it in simulation, watching it fail, and having the AI redesign and rebuild a stronger version) is not a metaphor for disaster response — it is the core capability in miniature. The same plan-simulate-validate-execute loop that reinforces a block tower is what would prevent a rescue robot from pulling the wrong beam out of a rubble pile. Because the system is fully generalizable (prompt in natural language, execute with any manipulator), extending from blocks on a table to rubble in a disaster zone is a matter of scale, not a change in architecture. 

Here is the criteria that is being used to judge this project:
Creativity
We want hackers to create a project that makes you say “wow” and tell all your friends about it. We're looking for projects that think so far outside the box that you begin to wonder why there was a box at all in the first place.
Technical Complexity
In only 36 hours, hackers manage to build projects with remarkably complex infrastructures built on excitingly advanced frameworks. We hope to see projects that are really running some beautiful code or hardware under the hood.
Social Impact
We're looking for hacks that are the blueprints for change that will impact future generations in humanity's most pressing areas of concern in the coming years.

Hardware:
Nvidia DGX Spark
Nvidia Jetson Orin Nano Super
Hugging face SO-101 Robot arm (1 leader, 1 follower)
2 Mono Cameras
Logitech C920 Webcam

Compute:
RTX 3070 Mobile Laptop (can run NVIDIA Isaac Sim)
RTX 5090 can be accessed remotely for fine tuning models


Deep Dive: The MirrorVerse
Tagline: Bridging the Physical and Digital Worlds with Collaborative Multi-Agent Robotics

The Core Concept
The "MirrorVerse" is a Cross-Reality Construction System. It demonstrates two robotic agents—one physical (in the real world) and one virtual (in NVIDIA Isaac Sim)—working together on a single shared task.

Predictive Safety (The Crystal Ball):
Before the real robot moves a heavy or fragile object, the virtual robot runs 100 physics simulations in parallel to detect if the structure will collapse. Only the safest path is sent to the real world.
Business Value: Zero wasted materials, zero accidents.
Dynamic Blueprinting (The Architect):
The Virtual Agent isn't just playing; it's authoring the next steps. It builds a complex structure in sim, tests if it works there, and then "hands off" the feasible plan to the physical robot to execute.
Carryover Value: It turns the simulation into a live instruction manual that adapts to mistakes the physical robot makes.
Synthetic Training (The Dojo):
If the robot encounters a new object (e.g., a strange tool), the simulation can generate thousands of synthetic images of that tool in different lighting conditions instantly to train a vision model (Sim-to-Real), allowing the physical robot to identify it immediately.
Real-World Business Cases (The "Why")
This isn't just a toy; it solves expensive problems in:

Space Construction (The "Mars Base"):
Problem: 20-minute light delay makes joystick control impossible.
Solution: Astronauts on Earth build the habitat in the "MirrorVerse" simulation. The physical robot on Mars executes the validated plan autonomously. If it gets stuck, it pauses for a "Macro-Correction" from the Leader Arm.
Nuclear/Hazmat Decommissioning:
Problem: Environments are too radioactive for humans and too unstructured for standard automation.
Solution: The "Digital Twin" allows operators to test a dangerous cutting procedure in safety before committed the robot to do it for real.
Micro-Manufacturing (The "Scale" Shift):
Problem: Assembling micro-electronics is hard for human hands.
Solution: The Leader Arm is large (human-scale). The Follower Arm is microscopic (or geared down). The human moves 10cm, the robot moves 1mm. The simulation ensures the 1mm move doesn't crush the chip.
Why This Wins (Tracks & Promos)
Demonstrates Multi-Agent Systems: Explicitly uses distinct agents with different capabilities (Physics vs. Simulation) coordinating.
Edge AI (NVIDIA): Showcases Jetson Orin for real-time perception and Isaac Sim for digital twinning.
Visual "Wow" Factor: Seeing a physical robot place a block, and instantly seeing it appear in 3D simulation to be picked up by a virtual robot is magical.
Technical Architecture
1. The Hardware Setup
Physical Domain (Real World)
Robot: SO-101 "Follower" Arm.
Compute: Jetson Orin Nano Super.
Sensors: 2x Mono Cameras (Stereo Setup) looking at the workspace.
Digital Domain (Simulation)
Simulation: NVIDIA Isaac Sim running on the RTX 3070 Laptop.
Robot: Digital Twin of the SO-101.
2. The Agentic Workflow (Multi-Agent)
Agent A: "The Builder" (Physical)
Role: Manipulate real objects.
Stack: Runs on Jetson Orin.
Loop:
Receives high-level command: "Place Red Block at (x,y,z)".
Uses VLM (Vision Language Model) to find the block.
Plans path (collision avoidance).
Executes move.
Agent B: "The Architect" (Virtual/Simulated)
Role: Physics simulation, stability testing, and virtual extension.
Stack: Runs on RTX 3070 (Isaac Sim).
Loop:
Continually mirrors the real world state (updates digital twin based on camera feed).
Simulation: "If we place the next block here, will it fall?" (Run 100 physics checks).
Handoff: When the physical tower is done, Agent B conceptually "takes over" and adds virtual procedural extensions that would be impossible purely physically (e.g., zero-gravity extensions).
Agent C: "The Overlord" (Orchestrator)
Role: The Brain.
Stack: Hosted LLM (OpenAI/Anthropic APIs via Promos).
Function:
Takes user voice prompt ("Build a bridge").
Decomposes task into sub-tasks.
Assigns sub-tasks: "Agent A, build the pillars. Agent B, verify structural integrity of the span."
Agent D: "The Teacher" (Human + Leader Arm)
Role: Exception handling and Imitation Learning.
Hardware: SO-101 Leader Arm (Handheld).
Workflow:
If Agent A (Builder) tells Agent C (Overlord) "I cannot grab this object, it's too slippery," the system pauses.
Human Intervention: You grab the Leader Arm. The Follower Arm mirrors you directly. You perform the grab and place the block manually.
The "Magic": The system records your joint angles and velocity. Agent B (Virtual) analyzes this "expert demo" to update its policy ("Ah, approach from 45 degrees, not 90").
Resume: The system goes back to autonomous mode, now smarter.
The Demo Flow (What Judges See)
Setup: On the table is the SO-101 Arm and a pile of colored blocks. A large monitor shows the Isaac Sim view (the "Mirror World").
Prompt: You say, "Let's build a gateway."
Action - Physical: The Physical Arm wakes up. It identifies two blocks and stacks them as pillars.
Cool Tech: As it moves, the Virtual Arm on screens mirrors it perfectly in real-time (Digital Twin).
Action - Handoff: The Physical Arm places a "capstone" block. The system detects this completes the physical phase.
Action - Virtual: The Virtual Arm in the simulation "picks up" a virtual block (that doesn't exist in reality) and places it on top of the real tower's digital twin.
Action - Simulation: The Virtual Agent spawns 50 more blocks to create a massive impossible archway in the simulation that responds to the physics of the real base. If you accept the design, the Physical Arm could try to match it (or just leave it as an AR extension).

What Exists (The "Shoulders of Giants")
Digital Twins (Industry Standard):
Companies like Siemens and BMW (using NVIDIA Omniverse) use Digital Twins to monitor factories. The virtual robot mirrors the real robot 1:1 to check for faults.
Difference: They use it for monitoring, you are using it for creative extension.
Sim-to-Real Transfer:
Research papers (and Isaac Sim demos) often train a robot in simulation and then deploy the policy to the real world.
Difference: Your project runs both simultaneously as separate agents working largely independently but coordinating, rather than just training one to be the other.
Mixed Reality Assembly:
Microsoft HoloLens demos often show humans seeing virtual instructions overlaid on real parts.
Difference: You are removing the human from the loop and having a Virtual Robot communicate with a Physical Robot.
Text-to-Robot Construction (The Edge):
Systems like VoxPoser and RoboGPT use LLMs to write code for robot arms to assemble simple objects (chairs, blocks).
Difference: These are usually "One-Shot" (Text → Move). Your system is "Iterative" (Text → Sim → Fail/Success → Refine → Real Move). You are adding a "Physics Sanity Check" loop that prevents the LLM from hallucinating physically impossible structures.
Context: The "DeepMind Gap" (Gemini Robotics 1.5)
You mentioned the Gemini Robotics 1.5 paper. That model represents the "Holy Grail": a massive Cloud VLA that "thinks" before it acts.

The Constraint: We cannot run a 100B+ parameter VLA on a Jetson Orin (Edge AI).
The Hack: The MirrorVerse approximates this "System 2 Thinking" by splitting the brain:
Reasoning (Cloud): We use the Gemini API (via Vercel credits) for the "Thinking" (High-level planning).
Physics (Sem-Cloud): We use Isaac Sim (RTX Laptop) to validate the "Action".
Reflex (Edge): We use the Jetson for the "Muscle Memory" (VLA/Policy execution).
Result: We show that you don't need a massive single model to achieve "Thoughtful Robotics"—you just need a Multi-Agent System (one of the track criteria!).
Your "Hackathon Novelty" (The "Cool" Factor)
The innovations that make this specific "MirrorVerse" idea unique for a hackathon:

The "Handoff": Most digital twins just copy the real world. Your virtual agent takes over where reality ends.
Bidirectional Feedback (The Real Innovation): The Virtual Agent proposes a "perfect" design. The Physical Agent tries to build it and reports failures (e.g., "block slipped"). The Virtual Agent updates the blueprint to compensate for real-world physics (e.g., "make the base wider"). This is true Multi-Agent Collaboration.
Multi-Agent Protocol: Defining a communication language between a "Nvidia Isaac Sim Agent" and a "Jetson Real-World Agent" is a strong technical implementation of the "Multi-Agent Systems" criterion.

