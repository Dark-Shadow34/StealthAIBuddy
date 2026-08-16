// ═══════════════════════════════════════════════════════════════════
// STEALTHAI BUDDY — INTERACTIVE JAVASCRIPT CLIENT ENGINE
// ═══════════════════════════════════════════════════════════════════

// ── Web Audio API Sound FX Synthesizer ──────────────────────────
let audioCtx = null;
let isAudioMuted = localStorage.getItem('stealth_audio_muted') === 'true';

function initAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
}

function playSound(type = 'click') {
  if (isAudioMuted) return;
  try {
    initAudioContext();
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'click') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(400, now + 0.05);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.05);
      osc.start(now);
      osc.stop(now + 0.05);
    } else if (type === 'scan') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(300, now);
      osc.frequency.exponentialRampToValueAtTime(1400, now + 0.3);
      osc.frequency.exponentialRampToValueAtTime(600, now + 0.6);
      gain.gain.setValueAtTime(0.12, now);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.6);
      osc.start(now);
      osc.stop(now + 0.6);
    } else if (type === 'success') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(523.25, now); // C5
      osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
      osc.frequency.setValueAtTime(783.99, now + 0.16); // G5
      gain.gain.setValueAtTime(0.1, now);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.35);
      osc.start(now);
      osc.stop(now + 0.35);
    }
  } catch (e) {
    // Silent fail if browser audio policy blocks
  }
}

// Audio Toggle Button
const audioToggleBtn = document.getElementById('audioToggleBtn');
const audioIcon = document.getElementById('audioIcon');
const audioText = document.getElementById('audioText');

function updateAudioButton() {
  if (isAudioMuted) {
    audioIcon.textContent = '🔇';
    audioText.textContent = 'Muted';
    audioToggleBtn.classList.remove('active');
  } else {
    audioIcon.textContent = '🔊';
    audioText.textContent = 'Sound FX';
    audioToggleBtn.classList.add('active');
  }
}
updateAudioButton();

audioToggleBtn.addEventListener('click', () => {
  isAudioMuted = !isAudioMuted;
  localStorage.setItem('stealth_audio_muted', isAudioMuted);
  updateAudioButton();
  if (!isAudioMuted) playSound('click');
});

// ── Interactive Particle Background Canvas ───────────────────────
const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');

let particles = [];
const particleCount = 52;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

class Particle {
  constructor() {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.vx = (Math.random() - 0.5) * 0.35;
    this.vy = (Math.random() - 0.5) * 0.35;
    this.radius = Math.random() * 1.8 + 0.8;
    this.color = Math.random() > 0.5 ? 'rgba(99, 102, 241, 0.45)' : 'rgba(56, 189, 248, 0.35)';
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
    if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
  }

  draw() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fillStyle = this.color;
    ctx.fill();
  }
}

for (let i = 0; i < particleCount; i++) {
  particles.push(new Particle());
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Draw connecting lines
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 140) {
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(99, 102, 241, ${0.14 * (1 - dist / 140)})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }
    }
  }

  particles.forEach(p => {
    p.update();
    p.draw();
  });

  requestAnimationFrame(animateParticles);
}
animateParticles();

// ── Dynamic Hero Typewriter Cycler ──────────────────────────────
const usecases = [
  'Live Coding Interviews',
  'LeetCode Hard Challenges',
  'Machine Learning Proofs',
  'Distributed System Design',
  'Complex Technical Screenings'
];

let usecaseIdx = 0;
const dynamicUsecaseEl = document.getElementById('dynamicUsecase');

function cycleUsecase() {
  usecaseIdx = (usecaseIdx + 1) % usecases.length;
  dynamicUsecaseEl.style.opacity = '0';
  setTimeout(() => {
    dynamicUsecaseEl.textContent = usecases[usecaseIdx];
    dynamicUsecaseEl.style.opacity = '1';
  }, 300);
}
setInterval(cycleUsecase, 3200);

// ── Invisibility Split Slider Drag Mechanics ────────────────────
const splitSlider = document.getElementById('splitSlider');
const splitOverlay = document.getElementById('splitOverlay');
const splitHandle = document.getElementById('splitHandle');

let isSliding = false;

function setSplitPosition(x) {
  const rect = splitSlider.getBoundingClientRect();
  let pos = ((x - rect.left) / rect.width) * 100;
  pos = Math.max(10, Math.min(90, pos));
  splitOverlay.style.width = `${pos}%`;
  splitHandle.style.left = `${pos}%`;
}

splitSlider.addEventListener('mousedown', (e) => {
  isSliding = true;
  setSplitPosition(e.clientX);
  playSound('click');
});

window.addEventListener('mousemove', (e) => {
  if (!isSliding) return;
  setSplitPosition(e.clientX);
});

window.addEventListener('mouseup', () => {
  isSliding = false;
});

// Touch support
splitSlider.addEventListener('touchstart', (e) => {
  isSliding = true;
  setSplitPosition(e.touches[0].clientX);
});

window.addEventListener('touchmove', (e) => {
  if (!isSliding) return;
  setSplitPosition(e.touches[0].clientX);
});

window.addEventListener('touchend', () => {
  isSliding = false;
});

// ── Live Code Scenario Sandbox ──────────────────────────────────
const scenarios = {
  dp: {
    title: 'LeetCode 72: Edit Distance (Dynamic Programming)',
    code: `<span class="code-comment">// Compute minimum operations to convert word1 to word2</span><br>
<span class="code-kw">def</span> <span class="code-fn">minDistance</span>(word1: str, word2: str) -&gt; int:<br>
&nbsp;&nbsp;&nbsp;&nbsp;m, n = len(word1), len(word2)<br>
&nbsp;&nbsp;&nbsp;&nbsp;dp = [[0] * (n + 1) <span class="code-kw">for</span> _ <span class="code-kw">in</span> range(m + 1)]<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-kw">for</span> i <span class="code-kw">in</span> range(m + 1): dp[i][0] = i<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-kw">for</span> j <span class="code-kw">in</span> range(n + 1): dp[0][j] = j<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-comment">// Optimal recurrence relation:</span>`,
    solution: {
      title: 'Optimal Recurrence: O(M×N) Time, O(N) Space',
      items: [
        'If <code>word1[i-1] == word2[j-1]</code>: <code>dp[i][j] = dp[i-1][j-1]</code>',
        'Else: <code>dp[i][j] = 1 + min(insert, delete, replace)</code>',
        'Space can be reduced to 2 rolling rows: <code>O(N)</code> space',
        'All 114 test cases pass with 0ms runtime overhead'
      ],
      model: 'Gemini 2.0 Flash',
      ocr: '11ms',
      ai: '648ms'
    }
  },
  ml: {
    title: 'Machine Learning: Ridge Regression L2 Regularization',
    code: `<span class="code-comment">// Ridge Regression Closed-Form Normal Equation</span><br>
<span class="code-kw">import</span> numpy <span class="code-kw">as</span> np<br>
<span class="code-kw">def</span> <span class="code-fn">ridge_regression</span>(X, y, alpha=1.0):<br>
&nbsp;&nbsp;&nbsp;&nbsp;d = X.shape[1]<br>
&nbsp;&nbsp;&nbsp;&nbsp;I = np.identity(d)<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-kw">return</span> np.linalg.inv(X.T @ X + alpha * I) @ X.T @ y`,
    solution: {
      title: 'Proof & Complexity: Analytical Solution',
      items: [
        'Objective: <code>min_w ||Xw - y||² + λ||w||²</code>',
        'Gradient: <code>∇_w = 2Xᵀ(Xw - y) + 2λw = 0</code>',
        'Closed-form: <code>w = (XᵀX + λI)⁻¹Xᵀy</code>',
        'Strictly invertible when <code>λ &gt; 0</code>; avoids multicollinearity'
      ],
      model: 'Gemini 2.0 Flash',
      ocr: '14ms',
      ai: '782ms'
    }
  },
  rate: {
    title: 'System Design: Distributed Token Bucket Rate Limiter',
    code: `<span class="code-comment">// High-throughput Redis Token Bucket Implementation</span><br>
<span class="code-kw">async def</span> <span class="code-fn">allow_request</span>(user_id: str, capacity: int = 100, refill_rate: float = 10.0):<br>
&nbsp;&nbsp;&nbsp;&nbsp;key = f"bucket:{user_id}"<br>
&nbsp;&nbsp;&nbsp;&nbsp;now = time.time()<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-comment">// Atomic evaluation using Lua script:</span>`,
    solution: {
      title: 'Atomic Redis Lua Script Solution',
      items: [
        'Calculate delta: <code>tokens = min(cap, tokens + delta * rate)</code>',
        'If <code>tokens &gt;= 1</code>: decrement & allow; else: return 429 Too Many Requests',
        'Atomic single round-trip execution handles 500k RPS',
        'P99 latency &lt; 1.2ms across distributed clusters'
      ],
      model: 'Claude 3.5 Sonnet',
      ocr: '9ms',
      ai: '795ms'
    }
  },
  thread: {
    title: 'Concurrency: Dining Philosophers Deadlock Prevention',
    code: `<span class="code-comment">// Fix circular wait condition in mutex acquisition</span><br>
<span class="code-kw">class</span> <span class="code-fn">Philosopher</span>(threading.Thread):<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-kw">def</span> <span class="code-fn">__init__</span>(self, left_fork, right_fork):<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;self.left = left_fork<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;self.right = right_fork<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="code-comment">// How to prevent circular wait deadlock?</span>`,
    solution: {
      title: 'Resource Hierarchy Solution (Dijkstra Proof)',
      items: [
        'Enforce global lock ordering: always acquire lower ID fork first',
        'Break circular wait condition: <code>first = min(left, right); second = max(left, right)</code>',
        'Guaranteed deadlock-free without lock timeouts',
        'Zero starvation probability with fair queueing'
      ],
      model: 'GPT-4o Mini',
      ocr: '12ms',
      ai: '710ms'
    }
  }
};

let currentScenarioKey = 'dp';
const sandboxCodeDisplay = document.getElementById('sandboxCodeDisplay');
const sandboxHudBody = document.getElementById('sandboxHudBody');
const sandboxHudStatus = document.getElementById('sandboxHudStatus');
const sandboxLatency = document.getElementById('sandboxLatency');
const sandboxModelBadge = document.getElementById('sandboxModelBadge');
const sandboxScanBtn = document.getElementById('sandboxScanBtn');
const laserBeam = document.getElementById('laserBeam');
const scenarioPills = document.querySelectorAll('.scenario-pill');

function loadScenario(key) {
  currentScenarioKey = key;
  const s = scenarios[key];
  sandboxCodeDisplay.innerHTML = s.code;
  
  // Reset HUD state
  sandboxHudStatus.textContent = 'STEALTH AI · READY';
  sandboxModelBadge.textContent = s.solution.model;
  sandboxLatency.textContent = `OCR ${s.solution.ocr} · AI ${s.solution.ai} · Ready`;
  
  sandboxHudBody.innerHTML = `
    <div class="sim-hud-title">⚡ ${s.title}</div>
    <ul class="sim-hud-list">
      <li>Press <b>[F9]</b> or <b>[Ctrl+Alt+S]</b> to scan screen</li>
      <li>Instant solution reasoning with ${s.solution.model}</li>
    </ul>
  `;
}
loadScenario('dp');

scenarioPills.forEach(pill => {
  pill.addEventListener('click', () => {
    scenarioPills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    loadScenario(pill.dataset.scenario);
    playSound('click');
  });
});

let isScanningSandbox = false;

function triggerSandboxScan() {
  if (isScanningSandbox) return;
  isScanningSandbox = true;

  playSound('scan');
  laserBeam.classList.remove('scanning');
  void laserBeam.offsetWidth; // trigger reflow
  laserBeam.classList.add('scanning');

  sandboxHudStatus.textContent = 'STEALTH AI · CAPTURING...';
  sandboxScanBtn.textContent = '⏳ Scanning...';
  sandboxScanBtn.disabled = true;
  sandboxLatency.textContent = 'Snapping silent screen buffer...';

  setTimeout(() => {
    sandboxHudStatus.textContent = 'STEALTH AI · REASONING...';
    sandboxLatency.textContent = 'OCR 11ms · Reasoning with Gemini 2.0...';

    setTimeout(() => {
      const s = scenarios[currentScenarioKey];
      sandboxHudStatus.textContent = 'STEALTH AI · ANSWER READY';
      sandboxModelBadge.textContent = s.solution.model;
      sandboxLatency.textContent = `OCR ${s.solution.ocr} · AI ${s.solution.ai} · Total < 1s`;

      sandboxHudBody.innerHTML = `
        <div class="sim-hud-title">⚡ ${s.solution.title}</div>
        <ul class="sim-hud-list">
          ${s.solution.items.map(it => `<li>${it}</li>`).join('')}
        </ul>
      `;

      playSound('success');
      sandboxScanBtn.textContent = '⚡ Scan Screen (F9)';
      sandboxScanBtn.disabled = false;
      isScanningSandbox = false;
      showToast('Scan complete! Solution rendered on HUD.', '⚡');
    }, 750);
  }, 400);
}

sandboxScanBtn.addEventListener('click', triggerSandboxScan);

// ── Interactive Virtual Keyboard Playground ────────────────────
const lastKeyPressed = document.getElementById('lastKeyPressed');
const lastVkCode = document.getElementById('lastVkCode');
const vkbKeys = document.querySelectorAll('.vkb-key');

window.addEventListener('keydown', (e) => {
  lastKeyPressed.textContent = e.key.toUpperCase();
  lastVkCode.textContent = `0x${(e.keyCode || 0).toString(16).toUpperCase()}`;

  // Highlight virtual key
  const matchingKey = document.querySelector(`.vkb-key[data-key="${e.code}"]`) ||
                     document.querySelector(`.vkb-key[data-key="${e.key}"]`) ||
                     document.querySelector(`.vkb-key[data-key="${e.key.toUpperCase()}"]`);
  if (matchingKey) {
    matchingKey.classList.add('active');
    playSound('click');
  }

  // Global F9 Trigger
  if (e.key === 'F9') {
    e.preventDefault();
    triggerSandboxScan();
  }
});

window.addEventListener('keyup', (e) => {
  const matchingKey = document.querySelector(`.vkb-key[data-key="${e.code}"]`) ||
                     document.querySelector(`.vkb-key[data-key="${e.key}"]`) ||
                     document.querySelector(`.vkb-key[data-key="${e.key.toUpperCase()}"]`);
  if (matchingKey) {
    matchingKey.classList.remove('active');
  }
});

// Click on virtual keys
vkbKeys.forEach(key => {
  key.addEventListener('mousedown', () => {
    const k = key.dataset.key || key.textContent;
    lastKeyPressed.textContent = k.toUpperCase();
    key.classList.add('active');
    playSound('click');

    if (k === 'F9') {
      triggerSandboxScan();
    }
  });

  key.addEventListener('mouseup', () => {
    key.classList.remove('active');
  });
});

// ── Theme Studio Live Color Transformer ────────────────────────
const themeCards = document.querySelectorAll('.theme-card-picker');
const themeHexMap = {
  emerald: { hex: '#10e599', rgb: '16, 229, 153' },
  obsidian: { hex: '#818cf8', rgb: '129, 140, 248' },
  cyberpunk: { hex: '#f43f5e', rgb: '244, 63, 94' },
  amber: { hex: '#f59e0b', rgb: '245, 158, 11' },
  frost: { hex: '#38bdf8', rgb: '56, 189, 248' },
  crimson: { hex: '#ff4d4d', rgb: '255, 77, 77' },
  vaporwave: { hex: '#a855f7', rgb: '168, 85, 247' }
};

themeCards.forEach(card => {
  card.addEventListener('click', () => {
    themeCards.forEach(c => c.classList.remove('active'));
    card.classList.add('active');
    
    const theme = card.dataset.theme;
    const colors = themeHexMap[theme];
    if (colors) {
      document.documentElement.style.setProperty('--theme-accent', colors.hex);
      document.documentElement.style.setProperty('--theme-accent-rgb', colors.rgb);
      document.documentElement.style.setProperty('--theme-glow', `rgba(${colors.rgb}, 0.35)`);
      
      // Update sandbox HUD theme class
      const sandboxHud = document.getElementById('sandboxHud');
      sandboxHud.className = `sim-hud hud-theme-${theme}`;
      
      playSound('click');
      showToast(`Theme switched to ${theme.toUpperCase()}!`, '🎨');
    }
  });
});

// ── Searchable FAQ Filter ───────────────────────────────────────
const faqSearchInput = document.getElementById('faqSearchInput');
const faqItems = document.querySelectorAll('.faq-item');

if (faqSearchInput) {
  faqSearchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    faqItems.forEach(item => {
      const text = item.textContent.toLowerCase();
      if (text.includes(q)) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  });
}

// ── 3D Card Spotlight Hover Physics ─────────────────────────────
document.querySelectorAll('.feature-card, .step-card, .cta-box').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty('--mouse-x', `${x}px`);
    card.style.setProperty('--mouse-y', `${y}px`);
  });
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
  }, 3000);
}

// Copy HUD Button
const hudCopyBtn = document.getElementById('hudCopyBtn');
if (hudCopyBtn) {
  hudCopyBtn.addEventListener('click', () => {
    showToast('Solution copied to clipboard!', '📋');
    playSound('click');
  });
}

// ── Floating Back to Top Button ────────────────────────────────
const backToTopBtn = document.createElement('button');
backToTopBtn.id = 'backToTopBtn';
backToTopBtn.innerHTML = '↑';
backToTopBtn.title = 'Back to top';
document.body.appendChild(backToTopBtn);

window.addEventListener('scroll', () => {
  if (window.scrollY > 450) {
    backToTopBtn.classList.add('visible');
  } else {
    backToTopBtn.classList.remove('visible');
  }
});

backToTopBtn.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
  playSound('click');
});

// Download button tracking
document.querySelectorAll('a[href*="releases"]').forEach(btn => {
  btn.addEventListener('click', () => {
    showToast('Downloading DesktopWindowHelper.exe...', '📦');
    playSound('success');
  });
});
