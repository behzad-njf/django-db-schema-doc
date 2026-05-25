/** Decorative animated schema motif for the landing page. */
export default function DatabaseBackground() {
  return (
    <div className="db-bg" aria-hidden>
      <div className="db-bg__grid" />
      <svg className="db-bg__lines" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
        <path className="db-bg__edge db-bg__edge--1" d="M120,180 L320,120 L520,200" />
        <path className="db-bg__edge db-bg__edge--2" d="M80,380 L280,320 L480,400 L680,340" />
        <path className="db-bg__edge db-bg__edge--3" d="M200,480 L400,420 L600,500" />
      </svg>
      <div className="db-bg__nodes">
        <span className="db-bg__node" style={{ left: "12%", top: "22%" }} />
        <span className="db-bg__node" style={{ left: "38%", top: "14%" }} />
        <span className="db-bg__node" style={{ left: "62%", top: "28%" }} />
        <span className="db-bg__node" style={{ left: "78%", top: "18%" }} />
        <span className="db-bg__node" style={{ left: "8%", top: "58%" }} />
        <span className="db-bg__node" style={{ left: "32%", top: "48%" }} />
        <span className="db-bg__node" style={{ left: "55%", top: "62%" }} />
        <span className="db-bg__node" style={{ left: "72%", top: "52%" }} />
        <span className="db-bg__node" style={{ left: "88%", top: "68%" }} />
      </div>
      <div className="db-bg__pulse" />
    </div>
  );
}
