// ── Interactive Background Particle Canvas ───────────────────────
const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');

let particles = [];
const particleCount = 48;

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
  
  // Draw connecting mesh lines
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

// ── Toast Notification System ───────────────────────────────────
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

// ── Card Spotlight Hover Physics ────────────────────────────────
document.querySelectorAll('.feature-card, .step-card, .cta-box').forEach(card => {
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    card.style.setProperty('--mouse-x', `${x}px`);
    card.style.setProperty('--mouse-y', `${y}px`);
  });
});

// ── Live HUD Simulator Logic ────────────────────────────────────
const simHud = document.getElementById('simHud');
const simDesktop = document.getElementById('simDesktop');
const simHudStatusText = document.getElementById('simHudStatusText');
const simHudBody = document.getElementById('simHudBody');
const simLatency = document.getElementById('simLatency');
const simModelBadge = document.getElementById('simModelBadge');
const simScanBtn = document.getElementById('simScanBtn');
const themePills = document.querySelectorAll('.theme-pill');

let hudFontSize = 0.9; // rem

// Theme Switcher
themePills.forEach(pill => {
  pill.addEventListener('click', () => {
    themePills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    const theme = pill.dataset.theme;
    simHud.className = `sim-hud hud-theme-${theme}`;
    showToast(`HUD Theme switched to ${theme.toUpperCase()}!`, '🎨');
  });
});

// Simulated AI Responses
const simulatedSolutions = [
  {
    title: 'Option B: Ridge Regression with L2 Regularization',
    items: [
      'Penalty term <code>λ∑w²</code> prevents coefficient explosion',
      'Closed-form solution: <code>w = (XᵀX + λI)⁻¹Xᵀy</code>',
      'Time complexity: <code>O(d³ + d²n)</code>'
    ],
    ocr: '12ms',
    ai: '742ms',
    model: 'Gemini 2.0 Flash'
  },
  {
    title: 'Optimal Approach: Dynamic Programming O(N)',
    items: [
      'State relation: <code>dp[i] = max(dp[i-1], dp[i-2] + nums[i])</code>',
      'Space optimization: 2 variables reduce memory to <code>O(1)</code>',
      'All 42 test cases pass'
    ],
    ocr: '9ms',
    ai: '618ms',
    model: 'Gemini 2.5 Flash-Lite'
  },
  {
    title: 'System Design: Distributed Token Bucket Rate Limiter',
    items: [
      'Store bucket state in Redis using atomic Lua script',
      'Refill tokens dynamically based on timestamp delta',
      'Handles 500k RPS with P99 latency < 1.4ms'
    ],
    ocr: '14ms',
    ai: '810ms',
    model: 'Claude 3.5 Sonnet'
  }
];

let solutionIdx = 0;
let isScanning = false;

function triggerSimulatedScan() {
  if (isScanning) return;
  isScanning = true;

  simHudStatusText.textContent = 'STEALTH AI · SCANNING...';
  simScanBtn.textContent = '⏳ Scanning Screen...';
  simScanBtn.disabled = true;
  simLatency.textContent = 'Capturing screen buffer...';

  // Step 1: Simulated OCR Capture
  setTimeout(() => {
    simHudStatusText.textContent = 'STEALTH AI · REASONING...';
    simLatency.textContent = 'OCR 11ms · Reasoning with Gemini 2.0...';
    
    // Step 2: Simulated AI Response
    setTimeout(() => {
      const sol = simulatedSolutions[solutionIdx % simulatedSolutions.length];
      solutionIdx++;

      simHudStatusText.textContent = 'STEALTH AI · ANSWER';
      simModelBadge.textContent = sol.model;
      simLatency.textContent = `OCR ${sol.ocr} · AI ${sol.ai} · Latency < 1s`;

      simHudBody.innerHTML = `
        <div class="sim-hud-title">⚡ ${sol.title}</div>
        <ul class="sim-hud-list">
          ${sol.items.map(it => `<li>${it}</li>`).join('')}
        </ul>
      `;

      simScanBtn.textContent = '⚡ Trigger Scan (F9)';
      simScanBtn.disabled = false;
      isScanning = false;
      showToast('Scan complete! Answer ready.', '⚡');
    }, 750);
  }, 350);
}

simScanBtn.addEventListener('click', triggerSimulatedScan);

// Interactive HUD Header Buttons (Font scale, copy, close)
document.addEventListener('click', e => {
  if (e.target.matches('.sim-btn-pill')) {
    const text = e.target.textContent.trim();
    if (text.includes('Scan')) {
      triggerSimulatedScan();
    } else if (text === 'A⁺') {
      hudFontSize = Math.min(hudFontSize + 0.1, 1.25);
      simHudBody.style.fontSize = `${hudFontSize}rem`;
      showToast(`HUD Font scaled up to ${Math.round(hudFontSize * 100)}%`, '🔍');
    } else if (text === 'A⁻') {
      hudFontSize = Math.max(hudFontSize - 0.1, 0.75);
      simHudBody.style.fontSize = `${hudFontSize}rem`;
      showToast(`HUD Font scaled down to ${Math.round(hudFontSize * 100)}%`, '🔍');
    } else if (text === '⚙️') {
      showToast('Settings window opened (Ctrl+Alt+O)', '⚙️');
    }
  } else if (e.target.matches('.sim-btn-close')) {
    simHud.style.opacity = '0';
    showToast('HUD hidden via Panic Hide (Esc). Press F9 to restore.', '🛡️');
    setTimeout(() => {
      simHud.style.opacity = '1';
    }, 2500);
  }
});

// Draggable Simulated HUD
let isDragging = false;
let startX, startY, initialLeft, initialTop;

simHud.addEventListener('mousedown', e => {
  if (e.target.closest('.sim-btn-pill') || e.target.closest('.sim-btn-close')) return;
  isDragging = true;
  startX = e.clientX;
  startY = e.clientY;
  const rect = simHud.getBoundingClientRect();
  const parentRect = simDesktop.getBoundingClientRect();
  initialLeft = rect.left - parentRect.left;
  initialTop = rect.top - parentRect.top;
});

window.addEventListener('mousemove', e => {
  if (!isDragging) return;
  const dx = e.clientX - startX;
  const dy = e.clientY - startY;
  simHud.style.left = `${Math.max(10, initialLeft + dx)}px`;
  simHud.style.top = `${Math.max(10, initialTop + dy)}px`;
  simHud.style.right = 'auto';
});

window.addEventListener('mouseup', () => {
  isDragging = false;
});

// Global Keyboard Shortcuts
window.addEventListener('keydown', e => {
  if (e.key === 'F9') {
    e.preventDefault();
    triggerSimulatedScan();
  } else if (e.key === 'Escape') {
    simHud.style.opacity = '0';
    showToast('Panic Hide triggered via ESC', '🛡️');
    setTimeout(() => { simHud.style.opacity = '1'; }, 2000);
  }
});

// ── Back to Top Floating Button ────────────────────────────────
const backToTopBtn = document.createElement('button');
backToTopBtn.id = 'backToTopBtn';
backToTopBtn.innerHTML = '↑';
backToTopBtn.title = 'Back to top';
document.body.appendChild(backToTopBtn);

window.addEventListener('scroll', () => {
  if (window.scrollY > 400) {
    backToTopBtn.classList.add('visible');
  } else {
    backToTopBtn.classList.remove('visible');
  }
});

backToTopBtn.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Download button click toast
document.querySelectorAll('a[href*="releases"]').forEach(btn => {
  btn.addEventListener('click', () => {
    showToast('Downloading DesktopWindowHelper.exe...', '📦');
  });
});
