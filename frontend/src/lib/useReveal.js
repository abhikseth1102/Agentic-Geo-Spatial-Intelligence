import { useEffect, useRef } from 'react';
export function useReveal() {
  const ref = useRef(null);
  useEffect(() => {
    const node = ref.current;
    if (!node || !('IntersectionObserver' in window)) return;
    let animation;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      if (document.documentElement.dataset.motion === 'off' || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      animation = node.animate([
        { opacity: 0.45, transform: 'perspective(1400px) translateY(22px) rotateX(2deg)', transformOrigin: 'center top' },
        { opacity: 1, transform: 'none', transformOrigin: 'center top' },
      ], { duration: 620, easing: 'cubic-bezier(.2,.7,.2,1)' });
    }, { threshold: 0, rootMargin: '0px 0px -16px 0px' });
    observer.observe(node);
    const stop = () => animation?.cancel();
    window.addEventListener('agi-motion-change', stop);
    const media = matchMedia('(prefers-reduced-motion: reduce)');
    media.addEventListener('change', stop);
    return () => { observer.disconnect(); stop(); window.removeEventListener('agi-motion-change', stop); media.removeEventListener('change', stop); };
  }, []);
  return ref;
}
