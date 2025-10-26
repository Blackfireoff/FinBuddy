"use client";

export default function SettingsFab() {
  const handleClick = () => {
    try {
      window.dispatchEvent(new CustomEvent("open-ai-settings"));
    } catch {}
  };

  return (
    <div className="fixed bottom-5 right-5 z-40 group">
      <button
        aria-label="Paramètres IA"
        onClick={handleClick}
        className="px-4 py-3 rounded-full bg-[#2563eb] text-white shadow-lg border border-white/10 transition-colors group-hover:bg-[#1e4fd6]"
        style={{ boxShadow: "0 0 0 0 rgba(37,99,235,0.4)" }}
        onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 0 0 6px rgba(37,99,235,0.15)"; }}
        onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 0 0 0 rgba(37,99,235,0.4)"; }}
        title="Paramètres IA"
      >
        ⚙️
      </button>
      <div className="pointer-events-none absolute right-full mr-2 top-1/2 -translate-y-1/2 px-2 py-1 rounded-md bg-black/70 text-white text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
        Paramètres IA
      </div>
    </div>
  );
}
