import { useEffect, useRef } from 'react';
export default function WorkspaceDepth() {
  const layer = useRef(null);
  useEffect(() => {
    const media = matchMedia('(prefers-reduced-motion: reduce)');
    let frame = 0;
    const paint = () => {
      frame = 0;
      const disabled = media.matches || document.documentElement.dataset.motion === 'off';
      const distance = document.documentElement.scrollHeight - innerHeight;
      layer.current?.style.setProperty('--drift', `${disabled ? 0 : Math.min(scrollY * .075, 100)}px`);
      layer.current?.style.setProperty('--progress', disabled ? '0' : String(distance > 0 ? scrollY / distance : 0));
    };
    const update = () => { if (!frame) frame = requestAnimationFrame(paint); };
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    window.addEventListener('agi-motion-change', update);
    media.addEventListener('change', update);
    const resize = new ResizeObserver(update); resize.observe(document.body);
    paint();
    return () => { cancelAnimationFrame(frame); resize.disconnect(); window.removeEventListener('scroll', update); window.removeEventListener('resize', update); window.removeEventListener('agi-motion-change', update); media.removeEventListener('change', update); };
  }, []);
  return <div className="workspace-depth" ref={layer} aria-hidden="true">
    <div className="depth-wash" />
    <div className="depth-contours"><i/><i/><i/><i/><i/></div>
    <div className="depth-grid" />
    <div className="reading-progress" />
  </div>;
}
