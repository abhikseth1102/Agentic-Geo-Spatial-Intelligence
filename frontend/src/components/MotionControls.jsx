import { useEffect, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import './motion.css';

export default function MotionControls() {
  const [off, setOff] = useState(() => { try { return localStorage.getItem('agi-motion') === 'off'; } catch { return false; } });
  useEffect(() => {
    document.documentElement.dataset.motion = off ? 'off' : 'on';
    try { localStorage.setItem('agi-motion', off ? 'off' : 'on'); } catch { /* Storage is optional. */ }
    window.dispatchEvent(new Event('agi-motion-change'));
  }, [off]);
  return <button className="motion-control" aria-pressed={off} aria-label="Reduce decorative motion" onClick={() => setOff(!off)} title="System reduced-motion preferences are always respected">
    {off ? <Play size={12}/> : <Pause size={12}/>}<span>{off ? 'Motion off' : 'Gentle motion'}</span>
  </button>;
}
