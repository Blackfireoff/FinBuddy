"use client";
import { CircularProgress } from "@heroui/react";
import { useEffect, useMemo, useState } from "react";

/** ================= Utils ================= */
const WEI_PER_ETH = 10n ** 18n;

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

function normalizeChainId(cid) {
  if (!cid) return "";
  if (typeof cid === "string" && cid.startsWith("0x")) return cid.toLowerCase();
  const asNum = Number(cid);
  if (Number.isFinite(asNum)) return `0x${asNum.toString(16)}`;
  return String(cid).toLowerCase();
}

function networkFromChainId(chainId) {
  switch (normalizeChainId(chainId)) {
    case "0xaa36a7":
      return "sepolia";
    case "0x1":
    default:
      return "mainnet";
  }
}

function blockscoutBaseByNetwork(network) {
  return network === "sepolia"
    ? "https://eth-sepolia.blockscout.com"
    : "https://eth.blockscout.com";
}

/** ================= Component ================= */
export default function WalletHealth({
  address,
  chainId,
  onTransactionsLoaded,
  onAnalyzeClick,
  isAnalysisLoading,
}) {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [balanceWei, setBalanceWei] = useState(null);
  const [scored, setScored] = useState([]);
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
      if (onTransactionsLoaded) onTransactionsLoaded([]);

      const url = `${API_BASE}/transactions/${network}/${address}/scores`;
      try {
        const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        const items = Array.isArray(data?.scored_transactions)
          ? data.scored_transactions
          : [];

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
          setScored(items);
          setBalanceWei(balanceCandidate);
          setDebug({ url, network, chainId: chainIdNorm, items: items.length });
          if (onTransactionsLoaded) onTransactionsLoaded(data);
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
  }, [address, network, API_BASE, chainIdNorm, onTransactionsLoaded]);

  const balanceEth = useMemo(() => formatWeiToEth(balanceWei, 6), [balanceWei]);

  return (
    <section className="w-full max-w-xl rounded-2xl p-6 bg-[#0e1a26] text-white">
      <h2 className="text-lg font-semibold">🪙 Wallet Global Health</h2>

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
            <div className="font-medium mb-2">Recent Transactions (scored):</div>
            <div className="space-y-3 max-h-80 overflow-auto rounded-md border border-white/10 p-3">
              {scored.length === 0 && (
                <div className="opacity-70">
                  No transactions found on this network.
                </div>
              )}

              {scored.map((s) => {
                const det = s?.enhanced_data?.transaction_details || {};
                const from = det?.from?.hash || det?.from || "—";
                const to = det?.to?.hash || det?.to || "—";
                const ts = det?.timestamp || "—";
                const valueEth = formatWeiToEth(det?.value ?? 0, 6);
                const feeEth = formatWeiToEth(det?.fee?.value ?? 0, 6);

                const scorePercent = Math.round(s?.final_score ?? 0);
                const risk = s?.risk_level?.toLowerCase() || "low";
                const color =
                  risk === "high"
                    ? "danger"
                    : risk === "medium"
                    ? "warning"
                    : "success";

                return (
                  <div
                    key={s.tx_hash}
                    className="text-sm rounded-md p-3 bg-white/5 flex flex-col md:flex-row md:items-center gap-4"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <a
                          className="underline"
                          href={`${explorerBase}/tx/${s.tx_hash}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {s.tx_hash.slice(0, 10)}…
                        </a>
                        <span className="px-2 py-0.5 rounded-full text-xs bg-white/10">
                          Risk: {risk}
                        </span>
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

                    {/* Circular Progress Gauge */}
                    <div className="flex justify-center items-center">
                      <CircularProgress
                        aria-label="score"
                        value={scorePercent}
                        color={color}
                        showValueLabel
                        size="lg"
                        classNames={{
                          svg: "drop-shadow-md",
                          value: "text-sm font-bold text-white",
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {scored.length > 0 && (
            <div className="mt-4">
              <button
                onClick={onAnalyzeClick}
                disabled={isAnalysisLoading}
                className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalysisLoading
                  ? "Analyzing..."
                  : "🤖 Analyze Transactions with AI"}
              </button>
            </div>
          )}

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