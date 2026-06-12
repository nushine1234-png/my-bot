// Mobile Toggle
const toggle = document.querySelector('.mobile-toggle');
const nav = document.querySelector('.nav');
if (toggle) {
  toggle.addEventListener('click', () => {
    nav.classList.toggle('open');
    toggle.classList.toggle('open');
  });
}

// Header scroll
const header = document.querySelector('.header');
window.addEventListener('scroll', () => {
  if (window.scrollY > 50) {
    header.classList.add('scrolled');
  } else {
    header.classList.remove('scrolled');
  }
});

// Close mobile nav on link click
document.querySelectorAll('.nav a').forEach(link => {
  link.addEventListener('click', () => {
    nav.classList.remove('open');
    toggle.classList.remove('open');
  });
});

// Fade-in observer
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right').forEach(el => {
  observer.observe(el);
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    if (href === '#') return;
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// Phone formatting
document.querySelectorAll('.phone-link').forEach(el => {
  const raw = el.textContent.replace(/[\s\-\(\)]/g, '');
  el.href = 'tel:' + raw;
});

// Current year in footer
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// Active nav link
const currentPath = window.location.pathname.replace(/\\/g, '/');
document.querySelectorAll('.nav a').forEach(link => {
  const href = link.getAttribute('href');
  if (href && !href.startsWith('http') && !href.startsWith('tel:') && !href.startsWith('#') && !href.startsWith('javascript') && !href.startsWith('mailto:')) {
    const base = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
    let full = base + href;
    while (full.includes('/../')) {
      full = full.replace(/\/[^\/]+\/\.\.\//, '/');
    }
    full = full.replace(/\/\.\//g, '/');
    if (currentPath === full || currentPath === full + '/' || currentPath + '/' === full) {
      link.classList.add('active');
    }
  }
});

// Contact form handler
const contactForm = document.getElementById('contact-form');
if (contactForm) {
  contactForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const btn = this.querySelector('.form-btn');
    const orig = btn.textContent;
    btn.textContent = 'Sending...';
    btn.disabled = true;
    const formData = new FormData(this);
    const data = {};
    formData.forEach((val, key) => data[key] = val);
    const msg = `Hi Nu Shine Dental! I'd like to enquire:
Name: ${data.name || ''}
Phone: ${data.phone || ''}
Email: ${data.email || ''}
Branch: ${data.branch || ''}
Message: ${data.message || ''}`;
    const url = `https://wa.me/919491821145?text=${encodeURIComponent(msg)}`;
    btn.textContent = 'Redirecting to WhatsApp...';
    setTimeout(() => {
      window.open(url, '_blank');
      btn.textContent = '✓ Message Sent';
      btn.style.background = '#059669';
      setTimeout(() => {
        btn.textContent = orig;
        btn.disabled = false;
        btn.style.background = '';
        contactForm.reset();
      }, 3000);
    }, 800);
  });
}

// Appointment form handler
const form = document.getElementById('appointment-form');
if (form) {
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    const btn = this.querySelector('.form-btn');
    const orig = btn.textContent;
    btn.textContent = 'Sending...';
    btn.disabled = true;

    const formData = new FormData(this);
    const data = {};
    formData.forEach((val, key) => data[key] = val);

    // Compose WhatsApp message
    const msg = `Hi Nu Shine Dental! I'd like to book an appointment:
Name: ${data.name || ''}
Phone: ${data.phone || ''}
Branch: ${data.branch || ''}
Treatment: ${data.treatment || ''}
Message: ${data.message || ''}`;

    const url = `https://wa.me/919491821145?text=${encodeURIComponent(msg)}`;

    btn.textContent = 'Redirecting to WhatsApp...';
    setTimeout(() => {
      window.open(url, '_blank');
      btn.textContent = '✓ Appointment Request Sent';
      btn.style.background = '#059669';
      setTimeout(() => {
        btn.textContent = orig;
        btn.disabled = false;
        btn.style.background = '';
        form.reset();
      }, 3000);
    }, 800);
  });
}

// Treatment Carousel
let currentSlide = 0;
const slides = document.getElementById('treatmentSlides');
const dots = document.querySelectorAll('.carousel-dot');
function updateCarousel() {
  if (slides) { slides.style.transform = `translateX(-${currentSlide * 100}%)`; }
  dots.forEach((d, i) => d.classList.toggle('active', i === currentSlide));
}
function nextSlide() { if (slides) { currentSlide = (currentSlide + 1) % slides.children.length; updateCarousel(); } }
function prevSlide() { if (slides) { currentSlide = (currentSlide - 1 + slides.children.length) % slides.children.length; updateCarousel(); } }
function goToSlide(n) { currentSlide = n; updateCarousel(); }

// Auto-play carousel
let carouselInterval;
function startCarousel() {
  if (!slides || slides.children.length < 2) return;
  if (carouselInterval) clearInterval(carouselInterval);
  carouselInterval = setInterval(() => { nextSlide(); }, 5000);
}
document.querySelectorAll('.treatment-carousel').forEach(() => {
  startCarousel();
  // Pause on hover
  document.querySelector('.treatment-carousel')?.addEventListener('mouseenter', () => { clearInterval(carouselInterval); });
  document.querySelector('.treatment-carousel')?.addEventListener('mouseleave', () => { startCarousel(); });
});

// FAQ Accordion
document.querySelectorAll('.faq-q').forEach(btn => {
  btn.addEventListener('click', function() {
    const item = this.parentElement;
    const isOpen = item.classList.contains('open');
    // Close all siblings
    item.parentElement.querySelectorAll('.faq-item.open').forEach(el => {
      if (el !== item) el.classList.remove('open');
    });
    item.classList.toggle('open');
  });
});

// Interactive Branch Map (OpenStreetMap + Leaflet.js) — Hybrid Model
(function() {
  var canvas = document.getElementById('gmaps-canvas');
  if (!canvas) return;

  var branches = [
    { name: 'Nu Shine Dental - Guntur', lat: 16.2919777, lng: 80.4346562, addr: 'Main Road, Guntur, Andhra Pradesh', phone: '+919440303206', slug: 'guntur' },
    { name: 'Nu Shine Dental - Eluru', lat: 16.71022, lng: 81.09465, addr: 'Eluru, Andhra Pradesh', phone: '+919491821145', slug: 'eluru' },
    { name: 'Nu Shine Dental - Bhimadole', lat: 16.8207193, lng: 81.2630635, addr: 'Bhimadole, Andhra Pradesh', phone: '+917730966566', slug: 'bhimadole' },
    { name: 'Nu Shine Dental - Kamavarapukota', lat: 17.0124178, lng: 81.2053008, addr: 'Kamavarapukota, Andhra Pradesh', phone: '+919441023035', slug: 'kamavarapukota' },
    { name: 'Nu Shine Dental - Tadikalapudi', lat: 16.8979817, lng: 81.1752095, addr: 'Tadikalapudi, Andhra Pradesh', phone: '+919704702601', slug: 'tadikalapudi' },
    { name: 'Nu Shine Dental - Pedakadimi', lat: 16.7367336, lng: 81.0261808, addr: 'Pedakadimi, Andhra Pradesh', phone: '+918143193509', slug: 'pedakadimi' }
  ];

  var map = L.map('gmaps-canvas');

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);

  var markers = [];
  var markerGroup = L.featureGroup();

  branches.forEach(function(b, i) {
    var m = L.marker([b.lat, b.lng])
      .bindPopup('<b>Nu Shine Dental</b><br>' + b.name.replace('Nu Shine Dental - ', '') + '<br><small>' + b.addr + '</small>');
    m._branchIdx = i;
    m.on('click', function() {
      flyToBranch(i);
    });
    markers.push(m);
    markerGroup.addLayer(m);
  });

  markerGroup.addTo(map);
  map.fitBounds(markerGroup.getBounds(), { padding: [40, 40] });

  function flyToBranch(idx) {
    var b = branches[idx];
    map.flyTo([b.lat, b.lng], 15, { duration: 1.2 });
    setTimeout(function() {
      markers[idx].openPopup();
    }, 1300);
    document.querySelectorAll('.bmp-btn').forEach(function(b2, i2) {
      b2.classList.toggle('active', i2 === idx);
    });
    var card = document.getElementById('activeBranchCard');
    if (card) {
      card.classList.add('fade-out');
      setTimeout(function() {
        var shortName = b.name.replace('Nu Shine Dental - ', '');
        card.innerHTML =
          '<div class="branch-info">' +
            '<h3>' + shortName + '</h3>' +
            '<p class="branch-addr">' + b.addr + '</p>' +
            '<p class="branch-phone"><a href="tel:' + b.phone + '">' + b.phone + '</a></p>' +
            '<div class="branch-links">' +
              '<a href="https://wa.me/' + b.phone.replace('+', '') + '?text=Hi%20Nu%20Shine%20Dental%20-%20' + encodeURIComponent(shortName) + '" target="_blank" class="btn btn-whatsapp btn-sm"> WhatsApp</a>' +
              '<a href="tel:' + b.phone + '" class="btn btn-teal btn-sm"> Call</a>' +
              '<a href="branches/' + b.slug + '.html" class="btn btn-outline-teal btn-sm">View</a>' +
            '</div>' +
          '</div>';
        card.classList.remove('fade-out');
      }, 300);
    }
  }

  document.querySelectorAll('.bmp-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var idx = parseInt(this.getAttribute('data-idx'), 10);
      flyToBranch(idx);
    });
  });
})();

// Testimonials Slider
(function() {
  const slider = document.getElementById('t-slider');
  if (!slider) return;
  const pairs = slider.querySelectorAll('.ba-pair');
  let idx = 0;
  if (pairs.length) pairs[0].classList.add('active');
  function show(n) {
    pairs.forEach(p => p.classList.remove('active'));
    idx = (n + pairs.length) % pairs.length;
    pairs[idx].classList.add('active');
  }
  const prev = document.querySelector('.ts-prev');
  const next = document.querySelector('.ts-next');
  if (prev) prev.addEventListener('click', () => show(idx - 1));
  if (next) next.addEventListener('click', () => show(idx + 1));
  // Auto-cycle every 4s
  if (pairs.length > 1) {
    let ti = setInterval(() => show(idx + 1), 4000);
    slider.addEventListener('mouseenter', () => clearInterval(ti));
    slider.addEventListener('mouseleave', () => { ti = setInterval(() => show(idx + 1), 4000); });
  }
})();




// === Animated Counters ===
(function() {
  var counterEls = document.querySelectorAll('.stat-number');
  if (!counterEls.length) return;
  
  function animateCounter(el) {
    var text = el.textContent.trim();
    var suffix = '';
    var target = parseInt(text.replace(/[^0-9]/g, ''), 10);
    if (isNaN(target)) return;
    var m = text.match(/([^0-9]+)$/);
    if (m) suffix = m[1];
    
    var start = 0;
    var duration = 2000;
    var startTime = null;
    
    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.floor(eased * target);
      el.textContent = current + suffix;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target + suffix;
      }
    }
    requestAnimationFrame(step);
  }
  
  var counterObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  
  counterEls.forEach(function(el) { counterObserver.observe(el); });
})();

// === Enhanced Scroll Reveal (supports .reveal, .reveal-left, .reveal-right, .reveal-scale) ===
(function() {
  var revealObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  
  document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale').forEach(function(el) {
    revealObserver.observe(el);
  });
})();

/* === Nova AI Chat Widget Toggle === */
function toggleChat(e) {
  if (e && e.target && e.target.closest && e.target.closest('.chat-widget')) return;
  var widget = document.getElementById('chatWidget');
  var overlay = document.getElementById('chatOverlay');
  if (!widget) return true;
  var isActive = widget.classList.contains('active');
  widget.classList.toggle('active');
  if (overlay) overlay.classList.toggle('active');
  if (!isActive) {
    var btn = document.querySelector('.nova-btn');
    if (btn) btn.style.animation = 'none';
  } else {
    var btn = document.querySelector('.nova-btn');
    if (btn) btn.style.animation = '';
  }
  return false;
}
