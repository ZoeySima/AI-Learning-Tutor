// GSAP animations for AI Learning Tutor
// Load GSAP first in HTML: <script src="/static/js/lib/gsap.min.js"></script>

// Fade in message (for streaming chunks)
function fadeInMessage(element) {
  if (!window.gsap) return;
  gsap.from(element, {
    opacity: 0,
    y: 8,
    duration: 0.3,
    ease: 'power2.out',
  });
}

// Celebrate chapter completion
function celebrateChapter(element) {
  if (!window.gsap) return;
  gsap.from(element.querySelector('p'), {
    scale: 0,
    duration: 0.5,
    ease: 'back.out(1.7)',
  });
}

// Shake card (for wrong answer)
function shakeCard(element) {
  if (!window.gsap) return;
  gsap.to(element, {
    x: [-4, 4, -4, 4, 0],
    duration: 0.4,
    ease: 'power2.inOut',
  });
}

// Pop-in (for correct answer feedback)
function popIn(element) {
  if (!window.gsap) return;
  gsap.from(element, {
    scale: 0,
    duration: 0.4,
    ease: 'back.out(1.7)',
  });
}

// Slide up (for quiz cards appearing)
function slideUp(element) {
  if (!window.gsap) return;
  gsap.from(element, {
    y: 16,
    opacity: 0,
    duration: 0.4,
    ease: 'power2.out',
  });
}

// Progress bar tween
function progressTo(element, percent) {
  if (!window.gsap) return;
  gsap.to(element, {
    width: `${percent}%`,
    duration: 0.8,
    ease: 'power2.out',
  });
}

// Flip flashcard (3D rotate)
function flipFlashcard(element) {
  if (!window.gsap) return;
  gsap.to(element, {
    rotateY: 180,
    duration: 0.6,
    ease: 'power2.inOut',
    transformStyle: 'preserve-3d',
  });
}

// Export for use in learn.js
if (typeof window !== 'undefined') {
  window.animations = {
    fadeInMessage,
    celebrateChapter,
    shakeCard,
    popIn,
    slideUp,
    progressTo,
    flipFlashcard,
  };
}
