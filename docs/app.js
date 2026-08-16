// ── Interactive Background Particle Canvas ───────────────────────
const canvas = document.getElementById('bgCanvas');
const ctx = canvas.getContext('2d');

let particles = [];
const particleCount = 45;

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
    this.vx = (Math.random() - 0.5) * 0.4;
    this.vy = (Math.random() - 0.5) * 0.4;
    this.radius = Math.random() * 1.8 + 0.8;
    this.color = Math.random() > 0.5 ? 'rgba(99, 102, 241, 0.4)' : 'rgba(56, 189, 248, 0.3)';
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
  
  // Draw subtle connecting lines
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 140) {
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(99, 102, 241, ${0.12 * (1 - dist / 140)})`;
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

// ── Live HUD Simulator Logic ────────────────────────────────────
const simHud = document.getElementById('simHud');
const simHudStatusText = document.getElementById('simHudStatusText');
const simHudBody = document.getElementById('simHudBody');
const simLatency = document.getElementById('simLatency');
const simModelBadge = document.getElementById('simModelBadge');
const simScanBtn = document.getElementById('simScanBtn');
const themePills = document.querySelectorAll('.theme-pill');

// Theme Switcher
themePills.forEach(pill => {
  pill.addEventListener('click', () => {
    themePills.forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    const theme = pill.dataset.theme;
    simHud.className = `sim-hud hud-theme-${theme}`;
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
  }
];

let solutionIdx = 0;
let isScanning = false;

function triggerSimulatedScan() {
  if (isScanning) return;
  isScanning = true;

  simHudStatusText.textContent = 'STEALTH AI · SCANNING...';
  simScanBtn.textContent = '⏳ Scanning...';
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
    }, 750);
  }, 350);
}

simScanBtn.addEventListener('click', triggerSimulatedScan);

// Global F9 keyboard trigger for demo in web page
window.addEventListener('keydown', (e) => {
  if (e.key === 'F9') {
    e.preventDefault();
    triggerSimulatedScan();
  }
});
