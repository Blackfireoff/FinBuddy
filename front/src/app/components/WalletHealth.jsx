"use client";

import { useEffect, useMemo, useState } from "react";
import { CircularProgress } from "@heroui/react";

/** ================= Utils ================= */
// ... (all your existing util functions: formatWeiToEth, normalizeChainId, etc. - no changes needed here)
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
  return network === "sepolia"? "https://eth-sepolia.blockscout.com": "https://eth.blockscout.com";
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
  console.log(API_BASE)
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
    <section className="w-full max-w-xl rounded-2xl p-6 bg-[#0e1a26] text-white">
      {/* Header with inline settings button */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">🪙 Wallet Global Health</h2>
        <button
          type="button"
          onClick={onOpenSettings}
          className="px-3 py-1.5 rounded-md bg-white/10 hover:bg-white/15 text-white text-sm border border-white/10"
        >
          ⚙️ Paramètres IA
        </button>
      </div>

      <div className="mt-2 text-sm opacity-80">
        Address: <span className="font-mono">{address}</span>
      </div>
      <div className="mt-1 text-sm opacity-80">
        Network:{" "}
        <span className="font-mono">
         {network} ({chainIdNorm || "—"})
        </span>
      </div>

      {loading && <div className="mt-4">Chargement…</div>}
      {err && <div className="mt-4 text-red-400">{err}</div>}

      {!loading && !err && (
        <>
          <div className="mt-4 text-base">
            ETH Balance: <strong>{balanceEth}</strong>
          </div>

          <div className="mt-6">
            <div className="font-medium mb-2">
              Recent Transactions (scored):
            </div>
            <div className="space-y-3 max-h-80 overflow-auto rounded-md border border-white/10 p-3">
              {scored.length === 0 && (
                <div className="opacity-70">
                  No transactions found on this network.
                </div>
              )}

              {/* ... (your existing scored.map - no changes) ... */}
              {scored.map((s) => {
                const det = s?.enhanced_data?.transaction_details || {};
                const from = det?.from?.hash || det?.from || "—";
                const to = det?.to?.hash || det?.to || "—";
                const ts = det?.timestamp || "—";
                const valueEth = formatWeiToEth(det?.value ?? 0, 6);
                const feeEth = formatWeiToEth(det?.fee?.value ?? 0, 6);

                return (
                  <div
                    key={s.tx_hash}
                    className="text-sm rounded-md p-3 bg-white/5"
                  >
                    <div className="flex items-center gap-3 flex-wrap">
                      <a
                        className="underline"
                        href={`${explorerBase}/tx/${s.tx_hash}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        {s.tx_hash.slice(0, 10)}…
                      </a>
                      <div className="flex items-center gap-2">
                        <CircularProgress
                          color="success"
                          formatOptions={{ style: "unit", unit: "kilometer" }}
                          label="Score"
                          showValueLabel={true}
                          size="lg"
                          value={Math.round(s.final_score || 0)}
                          maxValue={100}
                        />
                        <span className="px-2 py-0.5 rounded-full text-xs bg-white/10">
                          Risk: {s.risk_level || "—"}
                        </span>
                      </div>
                    </div>
                    <div className="mt-1">
                      From: <span className="font-mono">{from}</span>
                    </div>
                    <div>
                      To: <span className="font-mono">{to}</span>
                    </div>
                    <div>
                      Date: <span className="font-mono">{ts}</span>
                    </div>
                    <div>
                      Value: <strong>{valueEth} ETH</strong>
                    </div>
                    <div>
                      Fee: <span className="font-mono">{feeEth} ETH</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action buttons row: Analyze + Settings */}
          {scored.length > 0 && (
            <div className="mt-4 flex gap-3">
              <button
                onClick={onAnalyzeClick}
                disabled={isAnalysisLoading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalysisLoading ? "Analyzing..." : "🤖 Analyze Transactions with AI"}
              </button>
              <button
                type="button"
                onClick={onOpenSettings}
                className="px-4 py-2 bg-white/10 text-white rounded-lg border border-white/10 hover:bg-white/15"
              >
                ⚙️ Paramètres IA
              </button>
            </div>
          )}


          {/* ... (your existing Debug details - no changes) ... */}
          <details className="mt-4 opacity-70">
            <summary>Debug</summary>
            <pre className="whitespace-pre-wrap text-xs mt-2">
              {JSON.stringify(debug, null, 2)}
            </pre>
          </details>
        </>
      )}
    </section>
  );
}