// ========================================
// PORTFOLIO — SCRIPT
// ========================================

document.addEventListener('DOMContentLoaded', () => {
  initParticles();
  initTypewriter();
  initNavbar();
  initRevealAnimations();
  initCountUp();
  initSmoothScroll();
});

// ========================================
// PARTICLE SYSTEM
// ========================================
function initParticles() {
  const canvas = document.getElementById('particleCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 1.8 + 0.4;
      this.speedX = (Math.random() - 0.5) * 0.25;
      this.speedY = (Math.random() - 0.5) * 0.25;
      this.opacity = Math.random() * 0.35 + 0.08;
      this.color = Math.random() > 0.5 ? '124,92,252' : '0,229,200';
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
      if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${this.color}, ${this.opacity})`;
      ctx.fill();
    }
  }

  function create() {
    const count = Math.min(70, Math.floor((canvas.width * canvas.height) / 18000));
    particles = [];
    for (let i = 0; i < count; i++) particles.push(new Particle());
  }

  function connectParticles() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 140) {
          const opacity = (1 - dist / 140) * 0.08;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(124,92,252,${opacity})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    connectParticles();
    requestAnimationFrame(animate);
  }

  resize();
  create();
  animate();
  window.addEventListener('resize', () => { resize(); create(); });
}

// ========================================
// TYPEWRITER
// ========================================
function initTypewriter() {
  const el = document.getElementById('typewriter');
  if (!el) return;

  const phrases = [
    'CS Engineering Student',
    'AI & Embedded Systems Developer',
    'Voice-Controlled Robotics Builder',
    'Python & C Programmer',
    'Software Testing Enthusiast'
  ];

  let phraseIdx = 0, charIdx = 0, deleting = false, delay = 100;

  function type() {
    const current = phrases[phraseIdx];
    if (deleting) {
      el.textContent = current.substring(0, charIdx - 1);
      charIdx--;
      delay = 35;
    } else {
      el.textContent = current.substring(0, charIdx + 1);
      charIdx++;
      delay = 70;
    }
    if (!deleting && charIdx === current.length) {
      delay = 2500;
      deleting = true;
    } else if (deleting && charIdx === 0) {
      deleting = false;
      phraseIdx = (phraseIdx + 1) % phrases.length;
      delay = 400;
    }
    setTimeout(type, delay);
  }

  setTimeout(type, 1400);
}

// ========================================
// NAVBAR
// ========================================
function initNavbar() {
  const navbar = document.getElementById('navbar');
  const toggle = document.getElementById('navToggle');
  const links = document.getElementById('navLinks');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  });

  toggle.addEventListener('click', () => {
    links.classList.toggle('open');
    toggle.classList.toggle('active');
  });

  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      links.classList.remove('open');
      toggle.classList.remove('active');
    });
  });

  // Active link highlight
  const sections = document.querySelectorAll('section[id]');
  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(sec => {
      if (window.scrollY >= sec.offsetTop - 100) {
        current = sec.getAttribute('id');
      }
    });
    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('href') === `#${current}`) {
        link.classList.add('active');
      }
    });
  });
}

// ========================================
// REVEAL ON SCROLL
// ========================================
function initRevealAnimations() {
  const elements = document.querySelectorAll('[data-reveal]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, idx) => {
      if (entry.isIntersecting) {
        setTimeout(() => entry.target.classList.add('revealed'), idx * 100);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  elements.forEach(el => observer.observe(el));
}

// ========================================
// COUNT-UP
// ========================================
function initCountUp() {
  const counters = document.querySelectorAll('[data-count]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const target = parseInt(entry.target.getAttribute('data-count'));
        animateCount(entry.target, target);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  counters.forEach(el => observer.observe(el));
}

function animateCount(el, target) {
  let current = 0;
  const increment = Math.max(1, Math.floor(target / 30));
  const stepTime = 1500 / (target / increment);
  const timer = setInterval(() => {
    current += increment;
    if (current >= target) { current = target; clearInterval(timer); }
    el.textContent = current;
  }, stepTime);
}

// ========================================
// SMOOTH SCROLL
// ========================================
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}
