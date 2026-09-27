
import streamlit as st
import json
import math
import random
import re
from datetime import datetime
from heapq import heappush, heappop

from langchain_groq import ChatGroq


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Multi-Agent Challenge Lab",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Multi-Agent Challenge Lab")
st.caption("Three simulated agentic systems: Wearable • AI Tutor • Smart City")


# ============================================================
# SIDEBAR / LLM CONFIG
# ============================================================

with st.sidebar:
    st.header("⚙️ Configuration")

    user_api_key = st.text_input(
        "Enter Groq API Key:",
        type="password"
    )

    model_name = st.text_input(
        "Groq Model:",
        value="openai/gpt-oss-20b"
    )

    st.info(
        "LLM features are optional. "
        "The app also contains deterministic fallback logic."
    )


# ============================================================
# LLM HELPER
# ============================================================

def get_llm():
    if not user_api_key:
        return None

    try:
        return ChatGroq(
            model=model_name,
            temperature=0.2,
            api_key=user_api_key
        )
    except Exception as e:
        st.error(f"LLM initialization failed: {e}")
        return None


def call_agent(system_prompt, user_prompt):
    llm = get_llm()

    if llm is None:
        return None

    try:
        response = llm.invoke([
            ("system", system_prompt),
            ("human", user_prompt)
        ])

        return response.content

    except Exception as e:
        st.error(f"Agent error: {e}")
        return None


# ============================================================
# COMMON JSON PARSER
# ============================================================

def extract_json(text):
    if not text:
        return None

    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"```json", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        return None

    try:
        return json.loads(match.group())
    except Exception:
        return None


# ============================================================
# SESSION STATE
# ============================================================

if "telemetry_stream" not in st.session_state:
    st.session_state.telemetry_stream = []

if "lesson_result" not in st.session_state:
    st.session_state.lesson_result = None

if "student_result" not in st.session_state:
    st.session_state.student_result = None

if "revised_lesson" not in st.session_state:
    st.session_state.revised_lesson = None

if "dispatch_events" not in st.session_state:
    st.session_state.dispatch_events = []


# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3 = st.tabs([
    "⌚ 1. IoT Wearable",
    "📚 2. AI Tutor",
    "🚑 3. Smart City Dispatch"
])


# ################################################################
# TAB 1
# ################################################################

with tab1:

    st.header("⌚ IoT Wearable Context Engine")

    st.write(
        "Telemetry → Profiler Agent → Context → Action Agent"
    )

    st.warning(
        "Simulation only. Emergency decisions here are demonstrations "
        "of agent logic and are not intended for real medical or safety use."
    )

    # ------------------------------------------------------------
    # Generate mock telemetry
    # ------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        heart_rate = st.slider(
            "Heart Rate",
            40,
            180,
            75
        )

    with col2:
        motion = st.slider(
            "Motion Level",
            0.0,
            10.0,
            1.0,
            0.1
        )

    with col3:
        battery = st.slider(
            "Battery %",
            1,
            100,
            50
        )

    gps_mode = st.selectbox(
        "Location Context",
        [
            "Home",
            "Familiar City",
            "Unfamiliar City"
        ]
    )

    active_app = st.selectbox(
        "Active App",
        [
            "None",
            "Navigation",
            "Beads Counter",
            "Music",
            "Workout"
        ]
    )

    if st.button("📡 Generate Telemetry Event"):

        telemetry = {
            "timestamp": datetime.now().isoformat(),
            "heart_rate": heart_rate,
            "motion": motion,
            "gps": gps_mode,
            "active_app": active_app,
            "battery": battery
        }

        st.session_state.telemetry_stream.append(telemetry)

        # Keep rolling window
        if len(st.session_state.telemetry_stream) > 10:
            st.session_state.telemetry_stream.pop(0)

    # ------------------------------------------------------------
    # Show latest telemetry
    # ------------------------------------------------------------

    if st.session_state.telemetry_stream:

        latest = st.session_state.telemetry_stream[-1]

        st.subheader("📡 Latest Telemetry")

        st.json(latest)

        # --------------------------------------------------------
        # PROFILER AGENT
        # --------------------------------------------------------

        st.subheader("🧠 Profiler Agent")

        hr = latest["heart_rate"]
        motion_value = latest["motion"]
        gps = latest["gps"]
        app = latest["active_app"]

        if motion_value < 0.3 and hr < 65:
            user_state = "User is likely sleeping or resting."

        elif motion_value < 0.3 and hr >= 120:
            user_state = "User has an elevated heart rate while stationary."

        elif app == "Navigation" and gps == "Unfamiliar City":
            user_state = "User is navigating in an unfamiliar city."

        elif motion_value > 5:
            user_state = "User is highly active."

        elif app == "Beads Counter":
            user_state = "User is interacting with the beads-counting application."

        else:
            user_state = "User is in a normal active state."

        st.info(user_state)

        # Optional LLM profiler
        profiler_prompt = f"""
You are the Profiler Agent of a smartwatch.

Telemetry:
{json.dumps(latest, indent=2)}

Create a one-sentence description of the user's current context.
Focus on activity, stress indicators, location and device state.
"""

        llm_profile = call_agent(
            "You analyze wearable telemetry and infer context.",
            profiler_prompt
        )

        if llm_profile:
            st.write("**LLM Profiler:**", llm_profile)

        # --------------------------------------------------------
        # ACTION AGENT
        # --------------------------------------------------------

        st.subheader("⚡ Action Agent")

        action = "NO ACTION"
        reason = "No urgent condition detected."

        # Emergency condition
        if hr >= 120 and motion_value < 0.3:

            action = "🚨 EMERGENCY PROTOCOL"
            reason = (
                "Heart rate is unusually high while the user "
                "appears completely stationary."
            )

        # Battery + navigation exception
        elif battery <= 5 and app == "Navigation" and gps == "Unfamiliar City":

            action = "🔕 STAY QUIET"
            reason = (
                "Battery is critically low, but navigation in an "
                "unfamiliar city is currently active."
            )

        elif battery <= 5:

            action = "🔋 LOW BATTERY ALERT"
            reason = "Battery is critically low."

        else:

            action = "✅ NO INTERRUPTION"
            reason = "User context does not justify an interruption."

        st.success(f"Decision: {action}")
        st.write(reason)

        # --------------------------------------------------------
        # Rolling Window
        # --------------------------------------------------------

        st.subheader("📊 Rolling Context Window")

        st.dataframe(
            st.session_state.telemetry_stream,
            use_container_width=True
        )


# ################################################################
# TAB 2
# ################################################################

with tab2:

    st.header("📚 Algorithmic Instructional Designer")

    st.write(
        "Documentation → Architect Agent → Content Agent → "
        "Simulated Student → Review → Rewrite"
    )

    default_docs = """
LangChain is a framework for developing applications powered by
language models. It provides abstractions for prompts, models,
output parsers, tools, retrievers and agents.

A chain connects multiple steps together.
An agent can decide which tools to use.
Retrieval-Augmented Generation allows an application to retrieve
relevant documents before generating an answer.
"""

    documentation = st.text_area(
        "📄 Technical Documentation",
        value=default_docs,
        height=250
    )

    if st.button("🏗️ Generate Curriculum"):

        # --------------------------------------------------------
        # ARCHITECT AGENT
        # --------------------------------------------------------

        architect_system = """
You are the Architect Agent.

Your job is to convert technical documentation into a structured
teaching blueprint.

Use these principles:
1. Learning objective
2. Prior knowledge
3. Concept introduction
4. Demonstration
5. Guided practice
6. Independent practice
7. Assessment
8. Feedback
"""

        architect_prompt = f"""
Technical documentation:

{documentation}

Create a structured lesson blueprint.
Keep it practical and beginner friendly.
"""

        blueprint = call_agent(
            architect_system,
            architect_prompt
        )

        if blueprint is None:

            blueprint = f"""
# Lesson Blueprint

## Learning Objective
Understand the main concepts in the documentation.

## Lesson Flow
1. Introduction
2. Core concepts
3. Example
4. Guided exercise
5. Independent exercise
6. Assessment

## Assessment
Explain the core concept in your own words.
"""

        # --------------------------------------------------------
        # CONTENT AGENT
        # --------------------------------------------------------

        content_system = """
You are the Content Agent.

Using the lesson blueprint, create:
- Explanation
- Example
- Practical exercise
- Assessment questions

Avoid unnecessary long theory.
"""

        content_prompt = f"""
Documentation:

{documentation}

Blueprint:

{blueprint}

Generate the complete lesson.
"""

        lesson = call_agent(
            content_system,
            content_prompt
        )

        if lesson is None:

            lesson = f"""
# AI Generated Lesson

## 1. Concept
The documentation describes a collection of tools and
abstractions used to build LLM applications.

## 2. Example
A simple application can connect a prompt to an LLM.

## 3. Exercise
Create a chain that sends a user question to an LLM.

## 4. Assessment
What is the difference between a chain and an agent?
"""

        st.session_state.lesson_result = {
            "blueprint": blueprint,
            "lesson": lesson
        }

        st.session_state.student_result = None
        st.session_state.revised_lesson = None

    # ------------------------------------------------------------
    # DISPLAY GENERATED LESSON
    # ------------------------------------------------------------

    if st.session_state.lesson_result:

        st.subheader("🏗️ Architect Agent Output")

        st.markdown(
            st.session_state.lesson_result["blueprint"]
        )

        st.divider()

        st.subheader("✍️ Content Agent Output")

        st.markdown(
            st.session_state.lesson_result["lesson"]
        )

        # --------------------------------------------------------
        # SIMULATED STUDENT
        # --------------------------------------------------------

        st.divider()

        st.subheader("🎓 Simulated Student Agent")

        if st.button("🧪 Run Student Simulation"):

            student_system = """
You are a simulated student.

You must attempt the assessment using ONLY the lesson provided.

Return:
RESULT: PASS or FAIL
ANSWER: your answer
CONFUSION: what was difficult
"""

            student_prompt = f"""
Lesson:

{st.session_state.lesson_result["lesson"]}

Attempt the assessment as a beginner student.
Do not pretend to know information that is not in the lesson.
"""

            student_output = call_agent(
                student_system,
                student_prompt
            )

            if student_output is None:

                student_output = """
RESULT: FAIL

ANSWER:
I understand that chains connect multiple steps, but I am not
fully sure how an agent decides which tool to use.

CONFUSION:
The difference between a chain and an agent was not explained
with enough examples.
"""

            st.session_state.student_result = student_output

        # --------------------------------------------------------
        # SHOW STUDENT RESULT
        # --------------------------------------------------------

        if st.session_state.student_result:

            st.markdown(
                st.session_state.student_result
            )

            # Determine whether the student failed
            failed = (
                "FAIL" in
                st.session_state.student_result.upper()
            )

            # ----------------------------------------------------
            # REVIEW / REWRITE AGENTS
            # ----------------------------------------------------

            if failed:

                st.warning(
                    "❌ Student failed. Triggering lesson revision..."
                )

                if st.button("🔄 Rewrite Confusing Section"):

                    repair_system = """
You are the Review Agent.

The student failed the assessment.

Identify the confusing concept and rewrite the relevant part
of the lesson.

Make the explanation simpler.
Add an example.
Add one small practice question.
"""

                    repair_prompt = f"""
Original lesson:

{st.session_state.lesson_result["lesson"]}

Student attempt:

{st.session_state.student_result}

Rewrite only the confusing sections.
"""

                    repaired = call_agent(
                        repair_system,
                        repair_prompt
                    )

                    if repaired is None:

                        repaired = """
# 🔄 Revised Lesson Section

## Chain vs Agent

A chain follows a predefined sequence.

Example:

User Question
      ↓
Prompt
      ↓
LLM
      ↓
Answer

An agent is different because it can decide what action or tool
to use.

Example:

User Question
      ↓
Agent
   ↙     ↓      ↘
Search  Calculator  Database

### Practice

When the steps are fixed, use a chain.
When the system must decide which tool to use, use an agent.
"""

                    st.session_state.revised_lesson = repaired

            # ----------------------------------------------------
            # SHOW REVISED LESSON
            # ----------------------------------------------------

            if st.session_state.revised_lesson:

                st.subheader("🔄 Dynamically Revised Lesson")

                st.markdown(
                    st.session_state.revised_lesson
                )


# ################################################################
# TAB 3
# ################################################################

with tab3:

    st.header("🚑 Smart City Dynamic Dispatch Grid")

    st.write(
        "911 Transcript → Triage Agent → Incident → "
        "Resource Manager → Dispatch Agent"
    )

    st.warning(
        "Simulation only. Do not use this prototype for real emergency "
        "dispatch or operational decisions."
    )

    # ------------------------------------------------------------
    # MOCK RESOURCE DATABASE
    # ------------------------------------------------------------

    default_resources = {
        "Ambulance-1": {
            "type": "ambulance",
            "location": "Central"
        },
        "Ambulance-2": {
            "type": "ambulance",
            "location": "North"
        },
        "FireTruck-1": {
            "type": "fire",
            "location": "East"
        },
        "FireTruck-2": {
            "type": "fire",
            "location": "West"
        },
        "Police-1": {
            "type": "police",
            "location": "Central"
        }
    }

    if "resources" not in st.session_state:
        st.session_state.resources = default_resources.copy()

    # ------------------------------------------------------------
    # MOCK 911 TRANSCRIPT
    # ------------------------------------------------------------

    default_transcript = """
There has been a serious accident near Central Hospital.
Two people may be injured and there is smoke coming from a vehicle.
Please send an ambulance and fire truck.
"""

    transcript = st.text_area(
        "📞 Incoming 911 Transcript",
        value=default_transcript,
        height=180
    )

    # ------------------------------------------------------------
    # TRIAGE AGENT
    # ------------------------------------------------------------

    if st.button("🧠 Run Triage Agent"):

        triage_system = """
You are the Triage Agent in a simulated smart-city emergency system.

Extract:
- location
- severity
- required resources
- incident type
- short summary

Return JSON only:

{
  "location": "...",
  "severity": "LOW|MEDIUM|HIGH|CRITICAL",
  "resources": ["ambulance", "fire", "police"],
  "incident_type": "...",
  "summary": "..."
}
"""

        triage_prompt = f"""
911 transcript:

{transcript}

Extract the structured incident information.
"""

        triage_output = call_agent(
            triage_system,
            triage_prompt
        )

        triage_data = extract_json(triage_output)

        # --------------------------------------------------------
        # FALLBACK TRIAGE
        # --------------------------------------------------------

        if triage_data is None:

            lower = transcript.lower()

            if any(word in lower for word in [
                "death",
                "multiple injured",
                "explosion",
                "fire",
                "critical"
            ]):
                severity = "CRITICAL"

            elif any(word in lower for word in [
                "serious",
                "injured",
                "accident"
            ]):
                severity = "HIGH"

            else:
                severity = "MEDIUM"

            resources = []

            if any(word in lower for word in [
                "injured",
                "medical",
                "ambulance"
            ]):
                resources.append("ambulance")

            if any(word in lower for word in [
                "fire",
                "smoke"
            ]):
                resources.append("fire")

            if any(word in lower for word in [
                "police",
                "crime"
            ]):
                resources.append("police")

            if not resources:
                resources.append("police")

            triage_data = {
                "location": "Central",
                "severity": severity,
                "resources": resources,
                "incident_type": "Unknown",
                "summary": transcript.strip()
            }

        st.session_state.dispatch_events.append(
            triage_data
        )

    # ------------------------------------------------------------
    # SHOW INCIDENT
    # ------------------------------------------------------------

    if st.session_state.dispatch_events:

        incident = st.session_state.dispatch_events[-1]

        st.subheader("🧠 Triage Agent Result")

        st.json(incident)

        # --------------------------------------------------------
        # DUPLICATE DETECTION
        # --------------------------------------------------------

        normalized = incident["summary"].lower()

        duplicate = False

        for old_event in st.session_state.dispatch_events[:-1]:

            old_summary = old_event["summary"].lower()

            # Very simple simulated duplicate detector
            common_words = set(normalized.split()) & set(
                old_summary.split()
            )

            if len(common_words) >= 5:
                duplicate = True
                break

        if duplicate:

            st.info(
                "🔁 Possible duplicate incident detected. "
                "No additional dispatch recommended."
            )

        else:

            # ----------------------------------------------------
            # MOCK CITY GRAPH
            # ----------------------------------------------------

            graph = {
                "Central": [
                    ("North", 5),
                    ("East", 4),
                    ("West", 6)
                ],
                "North": [
                    ("Central", 5),
                    ("East", 7)
                ],
                "East": [
                    ("Central", 4),
                    ("North", 7),
                    ("West", 5)
                ],
                "West": [
                    ("Central", 6),
                    ("East", 5)
                ]
            }

            def shortest_distance(start, target):

                queue = [(0, start)]
                visited = set()

                while queue:

                    distance, node = heappop(queue)

                    if node in visited:
                        continue

                    visited.add(node)

                    if node == target:
                        return distance

                    for neighbor, weight in graph.get(node, []):

                        if neighbor not in visited:
                            heappush(
                                queue,
                                (
                                    distance + weight,
                                    neighbor
                                )
                            )

                return float("inf")

            # ----------------------------------------------------
            # DISPATCH AGENT
            # ----------------------------------------------------

            st.subheader("🚑 Dispatch Agent")

            requested_types = incident["resources"]

            if incident["severity"] == "CRITICAL":

                priority_score = 100

            elif incident["severity"] == "HIGH":

                priority_score = 80

            elif incident["severity"] == "MEDIUM":

                priority_score = 50

            else:

                priority_score = 20

            assignments = []

            used_resources = set()

            for resource_type in requested_types:

                candidates = []

                for name, details in st.session_state.resources.items():

                    if name in used_resources:
                        continue

                    if details["type"] == resource_type:

                        distance = shortest_distance(
                            details["location"],
                            incident["location"]
                        )

                        candidates.append(
                            (
                                distance,
                                name,
                                details
                            )
                        )

                if candidates:

                    candidates.sort(
                        key=lambda x: x[0]
                    )

                    distance, name, details = candidates[0]

                    used_resources.add(name)

                    assignments.append({
                        "resource": name,
                        "type": details["type"],
                        "from": details["location"],
                        "to": incident["location"],
                        "travel_time": distance,
                        "priority": priority_score
                    })

            if assignments:

                st.success("✅ Dispatch plan generated")

                for assignment in assignments:

                    st.write(
                        f"**{assignment['resource']}** → "
                        f"{assignment['to']} | "
                        f"ETA: {assignment['travel_time']} min | "
                        f"Priority: {assignment['priority']}"
                    )

            else:

                st.error(
                    "❌ No matching resources are available."
                )

    # ------------------------------------------------------------
    # RESOURCE DATABASE
    # ------------------------------------------------------------

    st.divider()

    st.subheader("🚓 Resource Database")

    resource_rows = []

    for name, details in st.session_state.resources.items():

        resource_rows.append({
            "Resource": name,
            "Type": details["type"],
            "Location": details["location"]
        })

    st.dataframe(
        resource_rows,
        use_container_width=True
    )

    if st.button("♻️ Reset Resources"):

        st.session_state.resources = default_resources.copy()

        st.session_state.dispatch_events = []

        st.rerun()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Multi-agent prototype • Mock data • Educational use"
)
