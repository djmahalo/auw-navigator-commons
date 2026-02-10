const API = "http://127.0.0.1:8000";

async function createIntake() {
  const body = {
    caller_id: document.getElementById("caller").value,
    channel: "phone",
    domain_module: document.getElementById("domain").value,
    priority: document.getElementById("priority").value,
    crisis: document.getElementById("crisis").checked,
    narrative: document.getElementById("narrative").value,
    attributes: {}
  };

  const res = await fetch(API + "/intakes", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)
  });

  const data = await res.json();
  document.getElementById("result").innerText =
    JSON.stringify(data, null, 2);

  loadQueues();
  loadIntakes();
}

async function loadQueues() {
  const res = await fetch(API + "/queues");
  const data = await res.json();
  document.getElementById("queues").innerText =
    JSON.stringify(data, null, 2);
}

async function loadIntakes() {
  const res = await fetch(API + "/intakes");
  const data = await res.json();
  document.getElementById("intakes").innerText =
    JSON.stringify(data, null, 2);
}

loadQueues();
loadIntakes();
