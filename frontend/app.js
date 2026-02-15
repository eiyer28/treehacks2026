// ---- CONFIG ----
// Change this to your DGX Spark's IP address
const SPARK_IP = "10.19.183.204";
const ROS_URL = `ws://${SPARK_IP}:9090`;

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
let ros = null;
let goalTopic = null;
let planSteps = [];
let currentSubtask = "";

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

// ---- ROS CONNECTION ----
let connectAttempt = 0;

function connect() {
    connectAttempt++;
    log(`Connection attempt #${connectAttempt} to ${ROS_URL}`, "info");

    try {
        ros = new ROSLIB.Ros({ url: ROS_URL });
    } catch (e) {
        log(`Failed to create ROSLIB.Ros: ${e.message}`, "error");
        setTimeout(connect, 3000);
        return;
    }

    ros.on("connection", () => {
        connectAttempt = 0;
        setStatus(true);
        addMessage("Connected to DGX Spark.", "system");
        log(`Connected to ${ROS_URL}`, "ok");

        goalTopic = new ROSLIB.Topic({
            ros: ros,
            name: "/mission/goal",
            messageType: "std_msgs/String"
        });

        const planTopic = new ROSLIB.Topic({
            ros: ros,
            name: "/plan/full",
            messageType: "std_msgs/String"
        });
        log("Subscribed to /plan/full", "info");
        planTopic.subscribe((msg) => {
            log(`/plan/full received: ${msg.data.substring(0, 200)}`, "info");
            try {
                const plan = JSON.parse(msg.data);
                planSteps = (Array.isArray(plan) ? plan : [plan]).map((s) => {
                    if (typeof s === "string") return { label: s, status: "pending" };
                    return { label: s.label || s.task || JSON.stringify(s), status: s.status || "pending" };
                });
                renderPlan();
                addMessage("Plan received:\n" + planSteps.map((s, i) => `  ${i + 1}. ${s.label}`).join("\n"), "assistant");
            } catch (e) {
                log(`/plan/full parse error: ${e.message}`, "warn");
                addMessage(msg.data, "assistant");
            }
        });

        const subtaskTopic = new ROSLIB.Topic({
            ros: ros,
            name: "/subtask/current",
            messageType: "std_msgs/String"
        });
        log("Subscribed to /subtask/current", "info");
        subtaskTopic.subscribe((msg) => {
            log(`/subtask/current: ${msg.data}`, "info");
            currentSubtask = msg.data;
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
    });

    ros.on("error", (err) => {
        const detail = err ? (err.message || err.type || JSON.stringify(err)) : "unknown";
        log(`ROS error: ${detail}`, "error");
        log(`Possible causes: rosbridge_server not running, wrong IP/port, firewall, or CORS`, "warn");
        addMessage("Connection error.", "system");
    });

    ros.on("close", () => {
        setStatus(false);
        log(`Connection closed. Will retry in 3s (attempt #${connectAttempt})`, "warn");
        addMessage("Disconnected. Retrying in 3s...", "system");
        setTimeout(connect, 3000);
    });
}

// ---- SEND ----
function send() {
    const text = promptEl.value.trim();
    if (!text || !goalTopic) return;

    addMessage(text, "user");
    log(`Publishing to /mission/goal: "${text}"`, "ok");
    goalTopic.publish(new ROSLIB.Message({ data: text }));

    planSteps = [];
    renderPlan();
    subtaskLabel.textContent = "Planning...";

    promptEl.value = "";
}

sendBtn.addEventListener("click", send);
promptEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter") send();
});

document.getElementById("hostname").textContent = `${location.hostname || "file"} \u2192 ${ROS_URL}`;

log(`Page loaded. Target: ${ROS_URL}`, "info");
log(`ROSLIB version: ${ROSLIB.REVISION || "unknown"}`, "info");
connect();
