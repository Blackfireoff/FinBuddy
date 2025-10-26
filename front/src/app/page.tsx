"use client";

import { useEffect, useState } from "react";
import WalletHealth from "./components/WalletHealth";
import ConnectWallet from "./components/ConnectWallet.jsx";
import AiAnalysisBox from "./components/AiAnalysisBox.jsx";
import SettingsModal from "./components/SettingsModal.jsx";
/* eslint-disable @typescript-eslint/no-explicit-any */

export default function Home() {
  const [address, setAddress] = useState("");
  const [chainId, setChainId] = useState("");

  // State lifted up for AI analysis
  const [scoredTransactions, setScoredTransactions] = useState<any>({});
  const [aiExplanation, setAiExplanation] = useState<any[]>([]);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");

  // Settings modal state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [aiConfig, setAiConfig] = useState<any>(null);

  // Load settings from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem("aiConfig");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") setAiConfig(parsed);
      } else {
        setAiConfig({ provider: "ollama" });
      }
    } catch {
      setAiConfig({ provider: "ollama" });
    }
  }, []);

  // Listen to global FAB event
  useEffect(() => {
    const open = () => setSettingsOpen(true);
    window.addEventListener("open-ai-settings", open as any);
    return () => window.removeEventListener("open-ai-settings", open as any);
  }, []);

  const handleSaveSettings = (cfg: any) => {
    setAiConfig(cfg);
    try {
      localStorage.setItem("aiConfig", JSON.stringify(cfg));
    } catch {}
  };

  // WebSocket-based AI Analysis including AI settings
  const handleAnalyzeTransactions = async () => {
    if (!address) return;
    const hasTx = !!scoredTransactions?.scored_transactions && Array.isArray(scoredTransactions.scored_transactions) && scoredTransactions.scored_transactions.length > 0;
    if (!hasTx) return;

    // Validate AI config
    const provider = (aiConfig?.provider || "ollama").toLowerCase();
    const apiKey = aiConfig?.api_key || "";
    if (provider !== "ollama" && !apiKey) {
      setAiError("Veuillez configurer une clé API pour le fournisseur choisi.");
      setSettingsOpen(true);
      return;
    }

    setAiLoading(true);
    setAiError("");
    setAiExplanation([]);

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

    try {
      const wsUrl = API_BASE.replace("http", "ws") + "/aiservice/analyse";
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        const ai = provider === "ollama" ? { provider: "ollama" } : { provider, api_key: apiKey };
        const payload = { ...scoredTransactions, ai };
        ws.send(JSON.stringify(payload));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            setAiError(data.error);
            ws.close();
          } else if (data.explanations) {
            setAiExplanation(data.explanations);
            ws.close();
          } else if (data.status) {
            // optional status messages
          }
        } catch (err) {
          console.error("Invalid message from AI WebSocket:", err);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket error:", err);
        setAiError("WebSocket connection failed.");
        setAiLoading(false);
      };

      ws.onclose = () => {
        setAiLoading(false);
      };
    } catch (e) {
      console.error("AI analysis failed:", e);
      setAiError("Failed to start AI analysis.");
      setAiLoading(false);
    }
  };

  return (
    <main className="p-8 flex flex-col items-center space-y-6">
      <ConnectWallet
        onAddress={setAddress}
        onChainId={setChainId}
        desiredChainId="0xaa36a7"
        allowNetworkSwitch={true}
      />

      {address && (
        <div className="w-full max-w-6xl mx-auto flex flex-col md:flex-row gap-6">
          {/* Left Panel */}
          <div className="flex-1">
            <WalletHealth
              address={address}
              chainId={chainId}
              onTransactionsLoaded={setScoredTransactions}
              onAnalyzeClick={handleAnalyzeTransactions}
              isAnalysisLoading={aiLoading}
              onOpenSettings={() => setSettingsOpen(true)}
            />
          </div>

          {/* Right Panel */}
          <div className="flex-1">
            <AiAnalysisBox
              isLoading={aiLoading}
              explanation={aiExplanation}
              error={aiError}
            />
          </div>
        </div>
      )}

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSave={handleSaveSettings}
        initialConfig={aiConfig || { provider: "ollama" }}
      />
    </main>
  );
}
