// ═══════════════════════════════════════════════════════════════════
// STEALTHAI BUDDY — CLIENT JAVASCRIPT ENGINE
// ═══════════════════════════════════════════════════════════════════

// ── Web Audio Synthesizer ───────────────────────────────────────
let audioCtx = null;
let isAudioMuted = localStorage.getItem('stealth_audio_muted') === 'true';

function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
}

function playSound(type = 'click') {
  if (isAudioMuted) return;
  try {
    initAudio();
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'click') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(400, now + 0.04);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.04);
      osc.start(now);
      osc.stop(now + 0.04);
    } else if (type === 'scan') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(350, now);
      osc.frequency.exponentialRampToValueAtTime(1200, now + 0.25);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.4);
      osc.start(now);
      osc.stop(now + 0.4);
    } else if (type === 'success') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.08);
      osc.frequency.setValueAtTime(783.99, now + 0.16);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.3);
      osc.start(now);
      osc.stop(now + 0.3);
    }
  } catch (e) {}
}

const audioToggleBtn = document.getElementById('audioToggleBtn');
const audioIcon = document.getElementById('audioIcon');
const audioText = document.getElementById('audioText');

function updateAudioUI() {
  if (isAudioMuted) {
    audioIcon.textContent = '🔇';
    audioText.textContent = 'Muted';
  } else {
    audioIcon.textContent = '🔊';
    audioText.textContent = 'Sound FX';
  }
}
updateAudioUI();

if (audioToggleBtn) {
  audioToggleBtn.addEventListener('click', () => {
    isAudioMuted = !isAudioMuted;
    localStorage.setItem('stealth_audio_muted', isAudioMuted);
    updateAudioUI();
    if (!isAudioMuted) playSound('click');
  });
}

// ── Particle Background Canvas ──────────────────────────────────
const canvas = document.getElementById('bgCanvas');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let particles = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  class Particle {
    constructor() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.vx = (Math.random() - 0.5) * 0.3;
      this.vy = (Math.random() - 0.5) * 0.3;
      this.r = Math.random() * 1.5 + 0.8;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
      if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(99, 102, 241, 0.4)';
      ctx.fill();
    }
  }

  for (let i = 0; i < 40; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(99, 102, 241, ${0.12 * (1 - dist / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(animate);
  }
  animate();
}

// ── Sandbox Scenarios Data ──────────────────────────────────────
const scenarios = {
  dp: {
    title: 'LeetCode 72: Edit Distance (Dynamic Programming)',
    code: `<span style="color:#5a6e8c;">// Compute min operations to convert word1 -> word2</span><br>
<span style="color:#f43f5e;">def</span> <span style="color:#38bdf8;">minDistance</span>(word1: str, word2: str) -&gt; int:<br>
&nbsp;&nbsp;&nbsp;&nbsp;m, n = len(word1), len(word2)<br>
&nbsp;&nbsp;&nbsp;&nbsp;dp = [[0] * (n + 1) <span style="color:#f43f5e;">for</span> _ <span style="color:#f43f5e;">in</span> range(m + 1)]<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#f43f5e;">for</span> i <span style="color:#f43f5e;">in</span> range(m + 1): dp[i][0] = i<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#f43f5e;">for</span> j <span style="color:#f43f5e;">in</span> range(n + 1): dp[0][j] = j<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#5a6e8c;">// Optimal recurrence relation:</span>`,
    solution: {
      title: 'Optimal Recurrence: O(M×N) Time, O(N) Space',
      items: [
        'If <code>word1[i-1] == word2[j-1]</code>: <code>dp[i][j] = dp[i-1][j-1]</code>',
        'Else: <code>dp[i][j] = 1 + min(insert, delete, replace)</code>',
        'Can be space-optimized with rolling 2 rows: <code>O(N)</code> space',
        'Passes all LeetCode test cases in 0ms'
      ],
      model: 'Gemini 2.0 Flash',
      ocr: '11ms',
      ai: '648ms'
    }
  },
  ml: {
    title: 'ML: Ridge Regression L2 Regularization',
    code: `<span style="color:#5a6e8c;">// Ridge Regression Closed-Form Normal Equation</span><br>
<span style="color:#f43f5e;">import</span> numpy <span style="color:#f43f5e;">as</span> np<br>
<span style="color:#f43f5e;">def</span> <span style="color:#38bdf8;">ridge_regression</span>(X, y, alpha=1.0):<br>
&nbsp;&nbsp;&nbsp;&nbsp;d = X.shape[1]<br>
&nbsp;&nbsp;&nbsp;&nbsp;I = np.identity(d)<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#f43f5e;">return</span> np.linalg.inv(X.T @ X + alpha * I) @ X.T @ y`,
    solution: {
      title: 'Proof & Complexity: Analytical Solution',
      items: [
        'Objective: <code>min_w ||Xw - y||² + λ||w||²</code>',
        'Gradient: <code>∇_w = 2Xᵀ(Xw - y) + 2λw = 0</code>',
        'Closed-form: <code>w = (XᵀX + λI)⁻¹Xᵀy</code>',
        'Guaranteed invertible for all <code>λ &gt; 0</code>'
      ],
      model: 'Gemini 2.0 Flash',
      ocr: '14ms',
      ai: '782ms'
    }
  },
  rate: {
    title: 'System Design: Distributed Token Bucket Rate Limiter',
    code: `<span style="color:#5a6e8c;">// High-throughput Redis Token Bucket Implementation</span><br>
<span style="color:#f43f5e;">async def</span> <span style="color:#38bdf8;">allow_request</span>(user_id: str, capacity: int = 100, refill_rate: float = 10.0):<br>
&nbsp;&nbsp;&nbsp;&nbsp;key = f"bucket:{user_id}"<br>
&nbsp;&nbsp;&nbsp;&nbsp;now = time.time()<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#5a6e8c;">// Atomic evaluation using Lua script:</span>`,
    solution: {
      title: 'Atomic Redis Lua Script Solution',
      items: [
        'Tokens: <code>min(cap, tokens + delta * rate)</code>',
        'If <code>tokens &gt;= 1</code>: decrement & allow; else 429 rate limit',
        'Single round-trip atomic script execution',
        'P99 latency &lt; 1.2ms under 500k RPS'
      ],
      model: 'Claude 3.5 Sonnet',
      ocr: '9ms',
      ai: '795ms'
    }
  },
  thread: {
    title: 'Concurrency: Dining Philosophers Deadlock Fix',
    code: `<span style="color:#5a6e8c;">// Fix circular wait condition in mutex acquisition</span><br>
<span style="color:#f43f5e;">class</span> <span style="color:#38bdf8;">Philosopher</span>(threading.Thread):<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#f43f5e;">def</span> <span style="color:#38bdf8;">__init__</span>(self, left_fork, right_fork):<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;self.left = left_fork<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;self.right = right_fork<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span style="color:#5a6e8c;">// How to prevent circular wait deadlock?</span>`,
    solution: {
      title: 'Resource Hierarchy Solution (Dijkstra Proof)',
      items: [
        'Enforce global lock ordering: acquire lower ID fork first',
        'Break circular wait: <code>first = min(left, right); second = max(left, right)</code>',
        'Deadlock-free proof without mutex timeouts',
        'Zero starvation probability with fair queueing'
      ],
      model: 'GPT-4o Mini',
      ocr: '12ms',
      ai: '710ms'
    }
  }
};

let currentScenario = 'dp';
const codeDisplay = document.getElementById('sandboxCodeDisplay');
const hudBody = document.getElementById('sandboxHudBody');
const hudStatus = document.getElementById('sandboxHudStatus');
const latencyDisplay = document.getElementById('sandboxLatency');
const modelBadge = document.getElementById('sandboxModelBadge');
const scanBtn = document.getElementById('sandboxScanBtn');
const laserBeam = document.getElementById('laserBeam');
const tabs = document.querySelectorAll('.sandbox-tab');

function setScenario(key) {
  currentScenario = key;
  const s = scenarios[key];
  if (codeDisplay) codeDisplay.innerHTML = s.code;
  if (hudStatus) hudStatus.textContent = 'STEALTH AI · READY';
  if (modelBadge) modelBadge.textContent = s.solution.model;
  if (latencyDisplay) latencyDisplay.textContent = `OCR ${s.solution.ocr} · AI ${s.solution.ai} · Ready`;

  if (hudBody) {
    hudBody.innerHTML = `
      <div class="hud-title">⚡ ${s.title}</div>
      <ul class="hud-bullets">
        <li>Press <b>[F9]</b> or click Scan Screen</li>
        <li>Instant reasoning powered by ${s.solution.model}</li>
      </ul>
    `;
  }
}
setScenario('dp');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    setScenario(tab.dataset.scenario);
    playSound('click');
  });
});

let isScanning = false;
function runScan() {
  if (isScanning) return;
  isScanning = true;

  playSound('scan');
  if (laserBeam) {
    laserBeam.classList.remove('scanning');
    void laserBeam.offsetWidth;
    laserBeam.classList.add('scanning');
  }

  if (hudStatus) hudStatus.textContent = 'STEALTH AI · CAPTURING...';
  if (scanBtn) { scanBtn.textContent = '⏳ Scanning...'; scanBtn.disabled = true; }
  if (latencyDisplay) latencyDisplay.textContent = 'Snapping silent screen buffer...';

  setTimeout(() => {
    if (hudStatus) hudStatus.textContent = 'STEALTH AI · REASONING...';
    if (latencyDisplay) latencyDisplay.textContent = 'OCR 11ms · Reasoning with Gemini 2.0...';

    setTimeout(() => {
      const s = scenarios[currentScenario];
      if (hudStatus) hudStatus.textContent = 'STEALTH AI · ANSWER READY';
      if (modelBadge) modelBadge.textContent = s.solution.model;
      if (latencyDisplay) latencyDisplay.textContent = `OCR ${s.solution.ocr} · AI ${s.solution.ai} · Total < 1s`;

      if (hudBody) {
        hudBody.innerHTML = `
          <div class="hud-title">⚡ ${s.solution.title}</div>
          <ul class="hud-bullets">
            ${s.solution.items.map(it => `<li>${it}</li>`).join('')}
          </ul>
        `;
      }

      playSound('success');
      if (scanBtn) { scanBtn.textContent = '⚡ Scan Screen (F9)'; scanBtn.disabled = false; }
      isScanning = false;
      showToast('Scan complete! Solution rendered on HUD.', '⚡');
    }, 750);
  }, 350);
}

if (scanBtn) scanBtn.addEventListener('click', runScan);

// ── Virtual Keyboard Event Listener ────────────────────────────
const lastKeyEl = document.getElementById('lastKeyPressed');
const lastVkEl = document.getElementById('lastVkCode');
const kbKeys = document.querySelectorAll('.kb-key');

window.addEventListener('keydown', (e) => {
  if (lastKeyEl) lastKeyEl.textContent = e.key.toUpperCase();
  if (lastVkEl) lastVkEl.textContent = `0x${(e.keyCode || 0).toString(16).toUpperCase()}`;

  const match = document.querySelector(`.kb-key[data-key="${e.code}"]`) ||
                document.querySelector(`.kb-key[data-key="${e.key}"]`) ||
                document.querySelector(`.kb-key[data-key="${e.key.toUpperCase()}"]`);
  if (match) {
    match.classList.add('active');
    playSound('click');
  }

  if (e.key === 'F9') {
    e.preventDefault();
    runScan();
  }
});

window.addEventListener('keyup', (e) => {
  const match = document.querySelector(`.kb-key[data-key="${e.code}"]`) ||
                document.querySelector(`.kb-key[data-key="${e.key}"]`) ||
                document.querySelector(`.kb-key[data-key="${e.key.toUpperCase()}"]`);
  if (match) match.classList.remove('active');
});

kbKeys.forEach(key => {
  key.addEventListener('mousedown', () => {
    const k = key.dataset.key || key.textContent;
    if (lastKeyEl) lastKeyEl.textContent = k.toUpperCase();
    key.classList.add('active');
    playSound('click');
    if (k === 'F9') runScan();
  });
  key.addEventListener('mouseup', () => key.classList.remove('active'));
});

// ── Toast Notification Queue ────────────────────────────────────
function showToast(message, icon = '✓') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
    if (container.children.length === 0) container.remove();
  }, 2800);
}

const copyBtn = document.getElementById('hudCopyBtn');
if (copyBtn) {
  copyBtn.addEventListener('click', () => {
    showToast('Solution copied to clipboard!', '📋');
    playSound('click');
  });
}
