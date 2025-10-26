"use client";
import { useMemo } from "react";
import { CheckCircle, AlertTriangle, TrendingUp, Shield, Cpu } from "lucide-react";

// Simple loading spinner
function Spinner() {
  return (
    <div className="border-4 border-white/20 border-t-white rounded-full w-8 h-8 animate-spin" />
  );
}

export default function AiAnalysisBox({ isLoading, error, explanation }) {
 const parsedExplanations = Array.isArray(explanation) ? explanation : [];

  // Dimension icons + colors
  const dimensionConfig = {
    economic: {
      label: "Economic",
      icon: TrendingUp,
      color: "text-emerald-400",
    },
    technical: {
      label: "Technical",
      icon: Cpu,
      color: "text-blue-400",
    },
    risk_security: {
      label: "Risk / Security",
      icon: Shield,
      color: "text-red-400",
    },
    strategic: {
      label: "Strategic",
      icon: AlertTriangle,
      color: "text-yellow-400",
    },
  };

  return (
    <section className="w-full h-full rounded-2xl p-6 bg-[#0e1a26] text-white shadow-xl border border-white/10">
      <h2 className="text-lg font-semibold flex items-center gap-2">
        🤖 AI Analysis
      </h2>

      <div className="mt-4 p-4 min-h-[200px] rounded-md border border-white/10 bg-white/5">
        {isLoading && (
          <div className="flex flex-col items-center gap-2 opacity-80 h-full justify-center">
            <Spinner />
            <span>Analyzing transactions...</span>
          </div>
        )}

        {error && (
          <div className="text-red-400 p-2 rounded bg-red-900/20">
            <strong>Error:</strong> {error}
          </div>
        )}

        {!isLoading && !error && parsedExplanations.length > 0 && (
          <div className="space-y-6">
            {parsedExplanations.map((tx, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-white/10 bg-[#172a3a] p-4 transition hover:bg-[#1d3245]"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-white/90">
                    🧾 Transaction {idx + 1}
                  </h3>
                  <span className="text-xs text-white/40 font-mono">
                    {tx.tx_hash?.slice(0, 10)}...
                  </span>
                </div>

                {/* Overall comment */}
                {tx.overall_comment && (
                  <p className="mt-2 text-sm text-white/70 italic">
                    “{tx.overall_comment}”
                  </p>
                )}

                {/* Per-dimension grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                  {Object.entries(tx.per_dimension || {}).map(
                    ([key, val]) => {
                      const conf = dimensionConfig[key] || {};
                      const Icon = conf.icon || CheckCircle;
                      return (
                        <div
                          key={key}
                          className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <Icon className={`w-4 h-4 ${conf.color}`} />
                            <h4 className={`text-sm font-semibold ${conf.color}`}>
                              {conf.label}
                            </h4>
                          </div>
                          <p className="text-xs text-white/80 mb-1">
                            <span className="font-semibold">Why:</span>{" "}
                            {val.why || "—"}
                          </p>
                          <p className="text-xs text-white/60">
                            <span className="font-semibold">How to improve:</span>{" "}
                            {val.how_to_improve || "—"}
                          </p>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {!isLoading && !error && parsedExplanations.length === 0 && (
          <div className="opacity-70 text-center">
            Click <strong>"Analyze Transactions"</strong> in the wallet panel to
            see AI-powered insights here.
          </div>
        )}
      </div>
    </section>
  );
}
