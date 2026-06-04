export function CornerBrackets({ className = "" }) {
  return (
    <>
      <span className={`absolute top-0 left-0 w-5 h-5 border-t-2 border-l-2 border-[#ccff00] ${className}`} />
      <span className={`absolute top-0 right-0 w-5 h-5 border-t-2 border-r-2 border-[#ccff00] ${className}`} />
      <span className={`absolute bottom-0 left-0 w-5 h-5 border-b-2 border-l-2 border-[#ccff00] ${className}`} />
      <span className={`absolute bottom-0 right-0 w-5 h-5 border-b-2 border-r-2 border-[#ccff00] ${className}`} />
    </>
  );
}

export function SectionLabel({ idx, children, color = "#ccff00" }) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <span className="mono-label" style={{ color }}>{String(idx).padStart(2, "0")} · {children}</span>
      <span className="h-px flex-1 bg-white/5" />
    </div>
  );
}
