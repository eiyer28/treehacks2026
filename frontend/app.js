// ---- CONFIG ----
const SPARK_IP = "100.123.79.38";
const BRIDGE_URL = `http://${SPARK_IP}:9090`;

// ---- DOM ----
const messagesEl = document.getElementById("messages");
const promptEl = document.getElementById("prompt");
const sendBtn = document.getElementById("send");
const statusEl = document.getElementById("status");
const planView = document.getElementById("plan-view");
const subtaskLabel = document.getElementById("subtask-label");
const logPanel = document.getElementById("log-panel");
const logToggle = document.getElementById("log-toggle");

// ---- LOG PANEL ----
logToggle.addEventListener("click", () => {
    logPanel.classList.toggle("open");
    logToggle.textContent = logPanel.classList.contains("open") ? "Hide Logs" : "Logs";
});

function log(message, level = "info") {
    const ts = new Date().toLocaleTimeString("en-US", {
        hour12: false, hour: "2-digit", minute: "2-digit",
        second: "2-digit", fractionalSecondDigits: 3
    });
    const entry = document.createElement("div");
    entry.className = `log-entry log-${level}`;
    entry.innerHTML = `<span class="log-ts">${ts}</span><span class="log-msg">${message}</span>`;
    logPanel.appendChild(entry);
    logPanel.scrollTop = logPanel.scrollHeight;
}

// ---- STATE ----
let planSteps = [];
let currentSubtask = "";
let evtSource = null;

// ---- HELPERS ----
function addMessage(text, role) {
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setStatus(connected) {
    statusEl.textContent = connected ? "connected" : "disconnected";
    statusEl.className = connected ? "connected" : "";
    sendBtn.disabled = !connected;
}

function renderPlan() {
    if (planSteps.length === 0) {
        planView.innerHTML = '<div style="color:#555;">No plan yet. Send a prompt to begin.</div>';
        return;
    }
    planView.innerHTML = "";
    planSteps.forEach((step, i) => {
        const div = document.createElement("div");
        div.className = "plan-step";

        if (step.status === "done") {
            div.classList.add("done");
        } else if (step.status === "active") {
            div.classList.add("active");
        }

        div.textContent = `${i + 1}. ${step.label}`;
        planView.appendChild(div);
    });
}

// ---- SSE CONNECTION ----
let connectAttempt = 0;

function connectSSE() {
    connectAttempt++;
    log(`SSE connection attempt #${connectAttempt} to ${BRIDGE_URL}/events`, "info");

    evtSource = new EventSource(`${BRIDGE_URL}/events`);

    evtSource.onopen = () => {
        connectAttempt = 0;
        setStatus(true);
        addMessage("Connected to DGX Spark.", "system");
        log(`SSE connected to ${BRIDGE_URL}/events`, "ok");
    };

    evtSource.addEventListener("plan", (e) => {
        log(`plan received: ${e.data.substring(0, 200)}`, "info");
        try {
            const plan = JSON.parse(e.data);
            planSteps = (Array.isArray(plan) ? plan : [plan]).map((s) => {
                if (typeof s === "string") return { label: s, status: "pending" };
                return { label: s.label || s.task || JSON.stringify(s), status: s.status || "pending" };
            });
            renderPlan();
            addMessage("Plan received:\n" + planSteps.map((s, i) => `  ${i + 1}. ${s.label}`).join("\n"), "assistant");
        } catch (err) {
            log(`plan parse error: ${err.message}`, "warn");
            addMessage(e.data, "assistant");
        }
    });

    evtSource.addEventListener("subtask", (e) => {
        log(`subtask: ${e.data}`, "info");
        currentSubtask = e.data;
        subtaskLabel.textContent = currentSubtask;

        let foundCurrent = false;
        planSteps.forEach((step) => {
            if (foundCurrent) {
                step.status = "pending";
            } else if (step.label === currentSubtask || currentSubtask.includes(step.label)) {
                step.status = "active";
                foundCurrent = true;
            } else {
                step.status = "done";
            }
        });
        renderPlan();
    });

    evtSource.onerror = () => {
        setStatus(false);
        log(`SSE connection lost. Retrying in 3s (attempt #${connectAttempt})`, "warn");
        evtSource.close();
        setTimeout(connectSSE, 3000);
    };
}

// ---- SEND ----
function send() {
    const text = promptEl.value.trim();
    if (!text) return;

    addMessage(text, "user");
    log(`Sending goal: "${text}"`, "ok");

    planSteps = [];
    renderPlan();
    subtaskLabel.textContent = "Planning...";

    fetch(`${BRIDGE_URL}/goal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
    })
        .then((res) => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            log(`Goal accepted by server`, "ok");
        })
        .catch((err) => {
            log(`Failed to send goal: ${err.message}`, "error");
            addMessage(`Error sending goal: ${err.message}`, "system");
        });

    promptEl.value = "";
}

sendBtn.addEventListener("click", send);
promptEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send();
});

document.getElementById("hostname").textContent = `${location.hostname || "file"} \u2192 ${BRIDGE_URL}`;

log(`Page loaded. Target: ${BRIDGE_URL}`, "info");
connectSSE();
