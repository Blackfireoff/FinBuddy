"use client";
import { CheckCircle, AlertTriangle, TrendingUp, Shield, Cpu } from "lucide-react";

// Simple loading spinner
function Spinner() {
  return (
    <div className="border-4 border-white/20 border-t-white rounded-full w-8 h-8 animate-spin" />
  );
}

export default function AiAnalysisBox({ isLoading, error, explanation }) {
  const parsedExplanations = Array.isArray(explanation) ? explanation : [];

  const badge = (label, score, cls) => (
    <span className={`px-3 py-1 rounded-md text-sm ${cls}`}>
      {label}:{" "}
      {Number.isFinite(Math.round(Number(score) || 0))
        ? `${Math.round(Number(score) || 0)}%`
        : "—"}
    </span>
  );

  return (
    <section className="w-full h-full rounded-2xl p-0 text-white">
      <div className="flex items-center justify-between mb-3">
        <h2
          className="text-lg font-semibold tracking-tight"
          style={{ fontFamily: "var(--font-display)" }}
        >
          AI Analysis
        </h2>
      </div>

      <div className="rounded-2xl border border-subtle bg-surface-1 p-4 min-h-[240px]">
        {isLoading && (
          <div className="flex flex-col items-center gap-2 opacity-80 h-full justify-center">
            <Spinner />
            <span>Analyzing transactions...</span>
          </div>
        )}

        {error && (
          <div className="text-red-400 p-2 rounded bg-red-900/20 border border-red-500/20">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!isLoading && !error && parsedExplanations.length > 0 && (
          <div className="space-y-6">
            {parsedExplanations.map((tx, idx) => {
              const scores =
                tx && typeof tx.scores === "object" ? tx.scores : {};
              return (
                <div
                  key={idx}
                  className="rounded-xl bg-surface-2 border border-subtle p-4 card-hover"
                >
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <div>
                      <h3 className="text-base font-semibold text-white/90">
                        🧾 Transaction {idx + 1}
                      </h3>
                      <div className="text-xs text-muted font-mono">
                        {tx.tx_hash?.slice(0, 12)}…
                      </div>
                    </div>
                    {/* Header badges */}
                    <div className="flex flex-wrap gap-2">
                      {badge(
                        "Economic",
                        scores.economic,
                        "bg-emerald-500/10 text-emerald-400"
                      )}
                      {badge(
                        "Technical",
                        scores.technical,
                        "bg-blue-500/10 text-blue-400"
                      )}
                      {badge(
                        "Risk/Security",
                        scores.risk_security,
                        "bg-red-500/10 text-red-400"
                      )}
                      {badge(
                        "Strategic",
                        scores.strategic,
                        "bg-yellow-500/10 text-yellow-400"
                      )}
                    </div>
                  </div>

                  {tx.overall_comment && (
                    <p className="mt-3 text-sm text-white/80 italic">
                      “{tx.overall_comment}”
                    </p>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                    {Object.entries(tx.per_dimension || {}).map(([key, val]) => {
                      const labelMap = {
                        economic: {
                          label: "Economic",
                          cls: "text-emerald-400",
                          Icon: TrendingUp,
                        },
                        technical: {
                          label: "Technical",
                          cls: "text-blue-400",
                          Icon: Cpu,
                        },
                        risk_security: {
                          label: "Risk / Security",
                          cls: "text-red-400",
                          Icon: Shield,
                        },
                        strategic: {
                          label: "Strategic",
                          cls: "text-yellow-400",
                          Icon: AlertTriangle,
                        },
                      };
                      const conf = labelMap[key] || {
                        label: key,
                        cls: "",
                        Icon: CheckCircle,
                      };
                      const { Icon } = conf;
                      return (
                        <div
                          key={key}
                          className="p-4 rounded-xl bg-surface-3 border border-subtle"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Icon className={`w-4 h-4 ${conf.cls}`} />
                            <h4 className={`text-sm font-semibold ${conf.cls}`}>
                              {conf.label}
                            </h4>
                          </div>
                          <p className="text-xs text-white/80 mb-1">
                            <span className="font-semibold">Why:</span> {val.why || "—"}
                          </p>
                          <p className="text-xs text-white/60">
                            <span className="font-semibold">How to improve:</span>{" "}
                            {val.how_to_improve || "—"}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!isLoading && !error && parsedExplanations.length === 0 && (
          <div className="opacity-70 text-center">
            Click <strong>Analyze with AI</strong> to see insights.
          </div>
        )}
      </div>
    </section>
  );
}
