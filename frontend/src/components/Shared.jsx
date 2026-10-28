import { ResponsiveContainer } from "recharts";
import { BookOpen } from "lucide-react";
export function Panel({ title, subtitle, children, action, className = "" }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-head">
        <div>
          <h3>{title}</h3>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
export function Chart({ children, height = 220 }) {
  return (
    <div style={{ width: "100%", height, minWidth: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        {children}
      </ResponsiveContainer>
    </div>
  );
}
export function Notice({ children }) {
  return (
    <div className="notice">
      <BookOpen size={16} />
      <div>{children}</div>
    </div>
  );
}
export function Stat({ label, value, unit, note, icon: Icon, tone }) {
  return (
    <div className="stat">
      <div className="stat-top">
        {label}
        <Icon size={17} />
      </div>
      <div className="stat-value">
        {value}
        <span>{unit}</span>
      </div>
      <div className={`stat-note ${tone || ""}`}>
        <span className="tiny-dot" />
        {note}
      </div>
    </div>
  );
}
