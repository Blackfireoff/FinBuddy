"use client";

import { useState } from "react";
import WalletHealth from "./components/WalletHealth";
import ConnectWallet from "./components/ConnectWallet.jsx";
import AiAnalysisBox from "./components/AiAnalysisBox.jsx";

export default function Home() {
  const [address, setAddress] = useState("");
  const [chainId, setChainId] = useState("");

  // State lifted up for AI analysis
  const [scoredTransactions, setScoredTransactions] = useState([]);
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");

  // 🔥 New: WebSocket-based AI Analysis
  const handleAnalyzeTransactions = async () => {
    if (!address || scoredTransactions.length === 0) return;

    setAiLoading(true);
    setAiError("");
    setAiExplanation("");

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

    try {
      // Convert http:// to ws:// for WebSocket connection
      const wsUrl = API_BASE.replace("http", "ws") + "/aiservice/analyse";
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        // When connected, send the ExplainRequest payload
        const payload = scoredTransactions
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
            // Optional: show progress updates if backend streams them
            setAiExplanation((prev) => prev + `\n${data.status}`);
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
    </main>
  );
}
