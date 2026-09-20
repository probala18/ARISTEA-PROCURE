/**
 * GSAP Animation Utilities for ARISTEA-PROCURE Next.js Frontend
 * SSR-safe, smooth hardware-accelerated animations.
 */
import gsap from 'gsap';

export function animateHeroText(target: string | HTMLElement) {
  if (typeof window === 'undefined') return;
  
  gsap.fromTo(
    target,
    {
      opacity: 0,
      y: 28,
      filter: 'blur(8px)',
    },
    {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      duration: 1.1,
      ease: 'power3.out',
      stagger: 0.15,
    }
  );
}

export function animateStaggerCards(container: string | HTMLElement, itemSelector: string) {
  if (typeof window === 'undefined') return;

  gsap.fromTo(
    typeof container === 'string' ? `${container} ${itemSelector}` : container.querySelectorAll(itemSelector),
    {
      opacity: 0,
      y: 20,
      scale: 0.98,
    },
    {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.6,
      stagger: 0.08,
      ease: 'power2.out',
    }
  );
}

export function pulseAttention(target: string | HTMLElement) {
  if (typeof window === 'undefined') return;

  gsap.fromTo(
    target,
    { scale: 1, boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.6)' },
    {
      scale: 1.02,
      boxShadow: '0 0 20px 4px rgba(239, 68, 68, 0.4)',
      duration: 0.35,
      yoyo: true,
      repeat: 3,
      ease: 'power1.inOut',
    }
  );
}

export function springDropzone(target: string | HTMLElement) {
  if (typeof window === 'undefined') return;

  gsap.fromTo(
    target,
    { scale: 0.96, borderColor: 'rgba(226, 232, 240, 0.8)' },
    {
      scale: 1,
      borderColor: 'rgba(79, 70, 229, 0.8)',
      duration: 0.5,
      ease: 'elastic.out(1, 0.4)',
    }
  );
}

export function countUpNumber(element: HTMLElement, targetValue: number, duration = 1.2) {
  if (typeof window === 'undefined') return;

  const obj = { val: 0 };
  gsap.to(obj, {
    val: targetValue,
    duration,
    ease: 'power2.out',
    onUpdate: () => {
      element.innerText = Math.round(obj.val).toLocaleString();
    },
  });
}
