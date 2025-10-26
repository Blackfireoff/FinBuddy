"use client";

import { useEffect, useMemo, useState } from "react";

/** ================= Utils ================= */
const WEI_PER_ETH = 10n ** 18n;

// Affichage ETH propre (wei -> ETH)
function formatWeiToEth(weiStr, maxFrac = 6) {
  if (weiStr == null) return "—";
  try {
    const wei = BigInt(String(weiStr));
    const whole = wei / WEI_PER_ETH;
    const frac = wei % WEI_PER_ETH;
    let fracStr = frac
      .toString()
      .padStart(18, "0")
      .slice(0, maxFrac)
      .replace(/0+$/, "");
    return fracStr ? `${whole}.${fracStr}` : whole.toString();
  } catch {
    const n = Number(weiStr) / 1e18;
    return Number.isFinite(n) ? n.toFixed(Math.min(maxFrac, 6)) : "—";
  }
}

// 0x1 / 1 / '0X1' -> '0x1'
function normalizeChainId(cid) {
  if (!cid) return "";
  if (typeof cid === "string" && cid.startsWith("0x")) return cid.toLowerCase();
  const asNum = Number(cid);
  if (Number.isFinite(asNum)) return `0x${asNum.toString(16)}`;
  return String(cid).toLowerCase();
}

// chainId -> "mainnet" | "sepolia" (par défaut mainnet)
function networkFromChainId(chainId) {
  switch (normalizeChainId(chainId)) {
    case "0xaa36a7":
      return "sepolia";
    case "0x1":
    default:
      return "mainnet";
  }
}

// Pour liens d’explorateur
function blockscoutBaseByNetwork(network) {
  return network === "sepolia"
    ? "https://eth-sepolia.blockscout.com"
    : "https://eth.blockscout.com";
}


/** ================= Composant ================= */
export default function WalletHealth({ 
  address, 
  chainId,
  onTransactionsLoaded,
  onAnalyzeClick,
  isAnalysisLoading,
  onOpenSettings
}) {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [balanceWei, setBalanceWei] = useState(null);
  const [scored, setScored] = useState([]); // Keep internal state for rendering
  const [debug, setDebug] = useState(null);

  const network = useMemo(() => networkFromChainId(chainId), [chainId]);
  const explorerBase = useMemo(
    () => blockscoutBaseByNetwork(network),
    [network],
  );
  const chainIdNorm = useMemo(() => normalizeChainId(chainId), [chainId]);

  useEffect(() => {
    if (!address) return;

    let cancelled = false;
    (async () => {
      setLoading(true);
      setErr("");
      // Reset parent state on new fetch
      if (onTransactionsLoaded) onTransactionsLoaded([]);

      const url = `${API_BASE}/transactions/${network}/${address}/scores`;
      try {
        const res = await fetch(url, {
          headers: { "Content-Type": "application/json" },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const items = Array.isArray(data?.scored_transactions)
          ? data.scored_transactions
          : [];

        // ... (your existing balance logic - no change)
        let balanceCandidate = null;
        for (const it of items) {
          const cb = it?.enhanced_data?.address_info?.coin_balance;
          const ah = it?.enhanced_data?.address_info?.hash;
          if (ah && ah.toLowerCase() === address.toLowerCase() && cb != null) {
            balanceCandidate = cb;
            break;
          }
          if (balanceCandidate == null && cb != null) balanceCandidate = cb;
        }


        if (!cancelled) {
          setScored(items); // Set internal state for rendering list
          setBalanceWei(balanceCandidate);
          setDebug({ url, network, chainId: chainIdNorm, items: items.length });
          
          // --- New line ---
          // Report transactions to parent component
          if (onTransactionsLoaded) onTransactionsLoaded(data);
          // --- End new line ---
        }
      } catch (e) {
        if (!cancelled) setErr(e?.message || "Fetch error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  // Add onTransactionsLoaded to dependency array
  }, [address, network, API_BASE, chainIdNorm, onTransactionsLoaded]);

  const balanceEth = useMemo(() => formatWeiToEth(balanceWei, 6), [balanceWei]);

  return (
    <section className="w-full max-w-3xl rounded-2xl p-0 text-white">
      {/* Header without redundant settings button */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold tracking-tight" style={{fontFamily:"var(--font-display)"}}>Wallet</h2>
        {/* Removed: redundant Paramètres IA button */}
      </div>

      {/* Compact wallet summary card */}
      <div className="card rounded-2xl p-4 bg-surface-1">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="space-y-1">
            <div className="text-xs text-muted">Address</div>
            <div className="font-mono text-sm opacity-95">{address}</div>
          </div>
          <div className="space-y-1 min-w-[140px]">
            <div className="text-xs text-muted">Network</div>
            <div className="font-mono text-sm opacity-95">{network} ({chainIdNorm || "—"})</div>
          </div>
          <div className="space-y-1 min-w-[160px] text-right ml-auto">
            <div className="text-xs text-muted">ETH Balance</div>
            <div className="text-base font-semibold">{balanceEth}</div>
          </div>
        </div>
      </div>

      {/* Transactions list */}
      <div className="mt-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-base font-medium text-white/90" style={{fontFamily:"var(--font-display)"}}>Recent Transactions (scored)</h3>
          {scored.length > 0 && (
            <button
              onClick={onAnalyzeClick}
              disabled={isAnalysisLoading}
              className="px-4 py-2 bg-[#2563eb] text-white font-semibold rounded-xl shadow-md hover:bg-[#1e4fd6] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalysisLoading ? "Analyzing..." : "Analyze with AI"}
            </button>
          )}
        </div>

        <div className="rounded-2xl border border-subtle bg-surface-1 p-3 max-h-96 overflow-auto">
          {loading && <div className="p-3">Chargement…</div>}
          {err && <div className="p-3 text-red-400">{err}</div>}

          {!loading && !err && scored.length === 0 && (
            <div className="opacity-70 p-3">No transactions found on this network.</div>
          )}

          {!loading && !err && scored.length > 0 && (
            <div className="space-y-3">
              {scored.map((s) => {
                const det = s?.enhanced_data?.transaction_details || {};
                const from = det?.from?.hash || det?.from || "—";
                const to = det?.to?.hash || det?.to || "—";
                const ts = det?.timestamp || "—";
                const valueEth = formatWeiToEth(det?.value ?? 0, 6);
                const feeEth = formatWeiToEth(det?.fee?.value ?? 0, 6);
                const subs = s?.subscores || {};
                const subList = [
                  { key: "economic", label: "Economic", cls: "text-economic" },
                  { key: "technical", label: "Technical", cls: "text-technical" },
                  { key: "risk_security", label: "Risk/Security", cls: "text-risk" },
                  { key: "strategic", label: "Strategic", cls: "text-strategic" },
                ];

                return (
                  <div key={s.tx_hash} className="rounded-xl bg-surface-2 border border-subtle p-3 card-hover">
                    <div className="flex items-center justify-between gap-4 flex-wrap">
                      <div className="flex items-center gap-3">
                        <a className="underline" href={`${explorerBase}/tx/${s.tx_hash}`} target="_blank" rel="noreferrer">
                          {s.tx_hash.slice(0, 10)}…
                        </a>
                        <span className="pill text-xs px-2 py-0.5 rounded-full">Risk: {s.risk_level || "—"}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        {/* Replaced CircularProgress with a simple chip */}
                        <span className="px-3 py-1 rounded-md bg-white/10 text-white text-sm font-semibold">
                          Score: {Number.isFinite(Math.round(s.final_score || 0)) ? `${Math.round(s.final_score || 0)}%` : "—"}
                        </span>
                      </div>
                    </div>

                    {/* Subscore chips (simple flex row) */}
                    <div className="flex flex-wrap gap-2 mt-2">
                      {subList.map(({ key, label }) => {
                        const v = Math.round(Number(subs?.[key] ?? 0));
                        const cls =
                          key === "economic"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : key === "technical"
                            ? "bg-blue-500/10 text-blue-400"
                            : key === "risk_security"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-yellow-500/10 text-yellow-400"; // strategic
                        return (
                          <span
                            key={key}
                            className={`${cls} px-3 py-1 rounded-md text-sm`}
                          >
                            {label}: {Number.isFinite(v) ? `${v}%` : "—"}
                          </span>
                        );
                      })}
                    </div>

                    <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-1 text-sm">
                      <div className="col-span-2 md:col-span-2 min-w-0">
                        From: <span className="font-mono block md:max-w-[280px] md:whitespace-nowrap md:overflow-hidden md:text-ellipsis break-all">{from}</span>
                      </div>
                      <div className="col-span-2 md:col-span-2 min-w-0">
                        To: <span className="font-mono block md:max-w-[280px] md:whitespace-nowrap md:overflow-hidden md:text-ellipsis break-all">{to}</span>
                      </div>
                      <div>Date: <span className="font-mono">{ts}</span></div>
                      <div>Value: <strong>{valueEth} ETH</strong></div>
                      <div>Fee: <span className="font-mono">{feeEth} ETH</span></div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Debug (collapsible) */}
      <details className="mt-4 opacity-70">
        <summary>Debug</summary>
        <pre className="whitespace-pre-wrap text-xs mt-2">{JSON.stringify(debug, null, 2)}</pre>
      </details>
    </section>
  );
}