const sampleCode = `import os
import pickle
import random
import hashlib
import subprocess
from flask import request

DEBUG = True
API_SECRET = "super-secret-admin-token"

def find_user(db, user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)

def run_ping(host):
    subprocess.run("ping -c 1 " + host, shell=True)

def load_profile():
    return pickle.loads(request.data)

def reset_token():
    return str(random.randint(100000, 999999))

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def render_name(element, name):
    element.innerHTML = name
`;

const state = {
  editor: null,
  lenis: null,
  velocity: 0,
  smoothVelocity: 0,
  mouse: { x: 0, y: 0 },
  cameraTarget: { x: 0, y: 0 },
  frameCount: 0,
  fps: 0,
  lastFpsTime: performance.now(),
  scanState: "idle",
  issueCount: 0,
};

const dom = {
  canvas: document.getElementById("hyper-scene"),
  scanBtn: document.getElementById("scanBtn"),
  sampleBtn: document.getElementById("sampleBtn"),
  results: document.getElementById("results"),
  statusText: document.getElementById("statusText"),
  riskScore: document.getElementById("riskScore"),
  issueCount: document.getElementById("issueCount"),
  highCount: document.getElementById("highCount"),
  scanTime: document.getElementById("scanTime"),
  hudFps: document.getElementById("hudFps"),
  hudVelocity: document.getElementById("hudVelocity"),
  hudCamera: document.getElementById("hudCamera"),
  hudIssues: document.getElementById("hudIssues"),
};

let scene;
let camera;
let renderer;
let panels = [];
let particles;
let core;

const FRONT_Z = 28;
const BACK_Z = -420;
const DEPTH_RANGE = FRONT_Z - BACK_Z;

function boot() {
  if (window.lucide) {
    window.lucide.createIcons();
  }

  setupLenis();
  setupThree();
  setupMouse();
  setupEditor();
  bindActions();
  requestAnimationFrame(animate);
}

function setupLenis() {
  state.lenis = new Lenis({
    duration: 1.1,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smoothWheel: true,
    wheelMultiplier: 1.15,
    touchMultiplier: 1.8,
  });

  state.lenis.on("scroll", ({ velocity }) => {
    state.velocity = velocity;
  });
}

function setupThree() {
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x030303, 0.014);

  camera = new THREE.PerspectiveCamera(62, window.innerWidth / window.innerHeight, 0.1, 900);
  camera.position.set(0, 0, 34);

  renderer = new THREE.WebGLRenderer({
    canvas: dom.canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));
  renderer.setSize(window.innerWidth, window.innerHeight);

  createLightField();
  createFloatingPanels();
  createScannerCore();

  window.addEventListener("resize", handleResize);
}

function createLightField() {
  const count = 1400;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  for (let i = 0; i < count; i += 1) {
    const i3 = i * 3;
    positions[i3] = randomBetween(-90, 90);
    positions[i3 + 1] = randomBetween(-55, 55);
    positions[i3 + 2] = randomBetween(BACK_Z, FRONT_Z);

    const cyanBias = Math.random();
    colors[i3] = cyanBias > 0.82 ? 1 : 0;
    colors[i3 + 1] = cyanBias > 0.82 ? 0.05 : 0.85;
    colors[i3 + 2] = cyanBias > 0.82 ? 0.2 : 1;
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.18,
    transparent: true,
    opacity: 0.8,
    vertexColors: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });

  particles = new THREE.Points(geometry, material);
  scene.add(particles);
}

function createFloatingPanels() {
  const panelMaterialOptions = {
    transparent: true,
    opacity: 0.28,
    side: THREE.DoubleSide,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  };

  const palette = [0x00f3ff, 0xff003c, 0x39ff88, 0xffcc3d, 0xb86bff];

  for (let i = 0; i < 58; i += 1) {
    const width = randomBetween(4, 14);
    const height = randomBetween(1.4, 5.6);
    const geometry = new THREE.PlaneGeometry(width, height, 4, 2);
    const material = new THREE.MeshBasicMaterial({
      ...panelMaterialOptions,
      color: palette[i % palette.length],
      wireframe: i % 3 === 0,
    });
    const mesh = new THREE.Mesh(geometry, material);
    const baseZ = randomBetween(BACK_Z, FRONT_Z);

    mesh.position.set(randomBetween(-52, 52), randomBetween(-31, 31), baseZ);
    mesh.rotation.set(
      randomBetween(-0.32, 0.32),
      randomBetween(-0.6, 0.6),
      randomBetween(-0.18, 0.18)
    );

    mesh.userData = {
      baseX: mesh.position.x,
      baseY: mesh.position.y,
      baseZ,
      drift: randomBetween(0.25, 1.35),
      phase: randomBetween(0, Math.PI * 2),
      rotSpeed: randomBetween(-0.006, 0.006),
    };

    panels.push(mesh);
    scene.add(mesh);
  }
}

function createScannerCore() {
  const group = new THREE.Group();

  const ringA = new THREE.Mesh(
    new THREE.TorusGeometry(8.5, 0.035, 8, 96),
    new THREE.MeshBasicMaterial({ color: 0x00f3ff, transparent: true, opacity: 0.42 })
  );
  const ringB = new THREE.Mesh(
    new THREE.TorusGeometry(5.2, 0.03, 8, 96),
    new THREE.MeshBasicMaterial({ color: 0xff003c, transparent: true, opacity: 0.36 })
  );
  const plane = new THREE.Mesh(
    new THREE.PlaneGeometry(18, 18, 16, 16),
    new THREE.MeshBasicMaterial({
      color: 0x00f3ff,
      transparent: true,
      opacity: 0.035,
      wireframe: true,
      side: THREE.DoubleSide,
    })
  );

  ringA.rotation.x = Math.PI / 2;
  ringB.rotation.y = Math.PI / 2;
  plane.rotation.z = Math.PI / 4;

  group.add(ringA, ringB, plane);
  group.position.set(0, 0, -76);
  group.userData = { ringA, ringB, plane };
  core = group;
  scene.add(group);
}

function setupMouse() {
  window.addEventListener("pointermove", (event) => {
    state.mouse.x = (event.clientX / window.innerWidth - 0.5) * 2;
    state.mouse.y = (event.clientY / window.innerHeight - 0.5) * 2;
    state.cameraTarget.y = state.mouse.x * 0.14;
    state.cameraTarget.x = state.mouse.y * -0.1;
  });
}

function setupEditor() {
  require.config({
    paths: {
      vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.45.0/min/vs",
    },
  });

  require(["vs/editor/editor.main"], () => {
    monaco.editor.defineTheme("autosecai-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment", foreground: "6a858c" },
        { token: "keyword", foreground: "00f3ff" },
        { token: "string", foreground: "ffcc3d" },
        { token: "number", foreground: "39ff88" },
      ],
      colors: {
        "editor.background": "#05070a",
        "editor.foreground": "#effcff",
        "editorLineNumber.foreground": "#40636b",
        "editorCursor.foreground": "#00f3ff",
        "editor.selectionBackground": "#ff003c44",
        "editor.lineHighlightBackground": "#00f3ff10",
        "editorGutter.background": "#05070a",
      },
    });

    state.editor = monaco.editor.create(document.getElementById("editor"), {
      value: sampleCode,
      language: "python",
      theme: "autosecai-dark",
      automaticLayout: true,
      minimap: { enabled: true },
      fontSize: 14,
      fontLigatures: true,
      smoothScrolling: true,
      cursorSmoothCaretAnimation: "on",
      padding: { top: 16, bottom: 16 },
      scrollbar: {
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10,
      },
    });

    setStatus("Editor online");
  });
}

function bindActions() {
  dom.scanBtn.addEventListener("click", runScan);
  dom.sampleBtn.addEventListener("click", () => {
    if (state.editor) {
      state.editor.setValue(sampleCode);
      setStatus("Sample reloaded");
    }
  });
}

async function runScan() {
  if (!state.editor) {
    setStatus("Editor loading");
    return;
  }

  const code = state.editor.getValue();
  state.scanState = "scanning";
  dom.scanBtn.disabled = true;
  setStatus("Scanning code");
  renderLoading();

  try {
    const response = await fetch("/api/scan/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        code,
        language: "python",
        learning_mode: true,
      }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Scan failed");
    }

    renderResults(payload);
    state.issueCount = payload.summary.issue_count;
    state.scanState = "complete";
    setStatus(payload.summary.issue_count ? "Threats mapped" : "No issues found");
  } catch (error) {
    state.scanState = "error";
    renderError(error.message);
    setStatus("Backend offline");
  } finally {
    dom.scanBtn.disabled = false;
  }
}

function renderLoading() {
  dom.results.replaceChildren(node("div", { className: "empty-state" }, [
    node("span", { className: "empty-glyph", text: "SCAN" }),
    node("p", { text: "Neural rules are traversing the source graph." }),
  ]));
}

function renderError(message) {
  dom.results.replaceChildren(node("div", { className: "empty-state" }, [
    node("span", { className: "empty-glyph", text: "ERR" }),
    node("p", { text: message }),
  ]));
}

function renderResults(payload) {
  const { issues, summary } = payload;
  dom.riskScore.textContent = String(summary.risk_score).padStart(2, "0");
  dom.issueCount.textContent = summary.issue_count;
  dom.highCount.textContent =
    (summary.severity_counts.Critical || 0) + (summary.severity_counts.High || 0);
  dom.scanTime.textContent = `${summary.scan_time_ms}ms`;
  dom.hudIssues.textContent = String(summary.issue_count).padStart(2, "0");

  if (!issues.length) {
    dom.results.replaceChildren(node("div", { className: "empty-state" }, [
      node("span", { className: "empty-glyph", text: "OK" }),
      node("p", { text: "No known prototype rules fired. Keep scanning before ship." }),
    ]));
    return;
  }

  const fragment = document.createDocumentFragment();
  issues.forEach((issue) => fragment.appendChild(renderIssue(issue)));
  dom.results.replaceChildren(fragment);
}

function renderIssue(issue) {
  const card = node("article", { className: "issue-card" });

  const title = node("h3");
  title.append(
    node("span", { text: issue.type }),
    node("span", { className: `severity ${issue.severity}`, text: issue.severity })
  );

  const meta = node("div", { className: "issue-meta" }, [
    node("span", { text: `Line ${issue.line}` }),
    node("span", { text: issue.cwe }),
    node("span", { text: issue.owasp }),
    node("span", { text: issue.id }),
  ]);

  card.append(
    title,
    meta,
    node("p", { text: issue.explanation }),
    node("p", { text: `Fix: ${issue.fix}` }),
    node("pre", { text: issue.secure_example })
  );

  if (issue.learning) {
    card.appendChild(node("p", { text: `Learning mode: ${issue.learning}` }));
  }

  return card;
}

function animate(time) {
  state.lenis.raf(time);
  state.smoothVelocity = lerp(state.smoothVelocity, state.velocity, 0.09);
  const intensity = Math.min(1, Math.abs(state.smoothVelocity) / 42);
  const scrollDepth = (state.lenis.scroll || 0) * 0.08;

  updateCamera(intensity);
  updatePanels(time, scrollDepth, intensity);
  updateParticles(scrollDepth, intensity);
  updateCore(time, intensity);
  updateGlitch(intensity);
  updateHud(time);

  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function updateCamera(intensity) {
  camera.rotation.x = lerp(camera.rotation.x, state.cameraTarget.x, 0.045);
  camera.rotation.y = lerp(camera.rotation.y, state.cameraTarget.y, 0.045);
  camera.position.x = lerp(camera.position.x, state.mouse.x * 2.8, 0.035);
  camera.position.y = lerp(camera.position.y, state.mouse.y * -1.8, 0.035);
  camera.position.z = lerp(camera.position.z, 34 - intensity * 5.5, 0.06);
}

function updatePanels(time, scrollDepth, intensity) {
  panels.forEach((panel, index) => {
    const data = panel.userData;
    const wrappedZ = wrap(data.baseZ + scrollDepth, BACK_Z, FRONT_Z);
    const wave = Math.sin(time * 0.0012 * data.drift + data.phase);

    panel.position.z = wrappedZ;
    panel.position.x = data.baseX + wave * (0.8 + intensity * 1.8);
    panel.position.y = data.baseY + Math.cos(time * 0.001 + data.phase) * 0.6;
    panel.rotation.z += data.rotSpeed * (1 + intensity * 7);
    panel.rotation.x += Math.sin(time * 0.0006 + index) * 0.0008;
    panel.material.opacity = 0.17 + intensity * 0.22 + (wrappedZ > -40 ? 0.1 : 0);
  });
}

function updateParticles(scrollDepth, intensity) {
  if (!particles) return;
  particles.rotation.z += 0.00035 + intensity * 0.0014;
  particles.rotation.y = Math.sin(scrollDepth * 0.002) * 0.08;
  particles.material.size = 0.16 + intensity * 0.22;
}

function updateCore(time, intensity) {
  if (!core) return;
  core.rotation.z += 0.0025 + intensity * 0.02;
  core.rotation.x = Math.sin(time * 0.0007) * 0.18;
  core.userData.ringA.rotation.z += 0.004 + intensity * 0.028;
  core.userData.ringB.rotation.x -= 0.005 + intensity * 0.024;
  core.userData.plane.material.opacity = 0.035 + intensity * 0.1;
}

function updateGlitch(intensity) {
  const shift = Math.round(intensity * 10);
  const blur = intensity > 0.42 ? Math.min(1.8, intensity * 1.25) : 0;
  document.documentElement.style.setProperty("--rgb-shift", `${shift}px`);
  document.documentElement.style.setProperty("--motion-blur", `${blur}px`);
  document.body.classList.toggle("glitch-active", intensity > 0.18 || state.scanState === "scanning");
}

function updateHud(time) {
  state.frameCount += 1;
  if (time - state.lastFpsTime >= 500) {
    state.fps = Math.round((state.frameCount * 1000) / (time - state.lastFpsTime));
    state.frameCount = 0;
    state.lastFpsTime = time;
  }

  dom.hudFps.textContent = String(state.fps).padStart(3, "0");
  dom.hudVelocity.textContent = state.smoothVelocity.toFixed(2);
  dom.hudCamera.textContent = `${camera.position.x.toFixed(1)},${camera.position.y.toFixed(1)},${camera.position.z.toFixed(1)}`;
  dom.hudIssues.textContent = String(state.issueCount).padStart(2, "0");
}

function handleResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.8));
}

function setStatus(text) {
  dom.statusText.textContent = text;
}

function node(tag, options = {}, children = []) {
  const element = document.createElement(tag);
  if (options.className) element.className = options.className;
  if (options.text !== undefined) element.textContent = options.text;
  children.forEach((child) => element.appendChild(child));
  return element;
}

function randomBetween(min, max) {
  return min + Math.random() * (max - min);
}

function lerp(current, target, amount) {
  return current + (target - current) * amount;
}

function wrap(value, min, max) {
  const range = max - min;
  return ((((value - min) % range) + range) % range) + min;
}

boot();

