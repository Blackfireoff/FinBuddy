"use client";

import { useState } from "react";
import WalletHealth from "./components/WalletHealth";
import ConnectWallet from "./components/ConnectWallet.jsx";
import AiAnalysisBox from "./components/AiAnalysisBox.jsx"; // Import the new component

export default function Home() {
  const [address, setAddress] = useState("");
  const [chainId, setChainId] = useState("");

  // State lifted up for AI analysis
  const [scoredTransactions, setScoredTransactions] = useState([]);
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");

  // API call handler for AI analysis
  const handleAnalyzeTransactions = async () => {
    if (scoredTransactions.length === 0) return;

    setAiLoading(true);
    setAiError("");
    setAiExplanation("");

    // Use the same API_BASE as WalletHealth
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

    try {
      const res = await fetch(`${API_BASE}/aiservice/analyse`, { // Assuming this is your new AI endpoint
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transactions: scoredTransactions })
      });

      if (!res.ok) throw new Error(`API Error: ${res.status}`);

      const data = await res.json();
      // Assuming the API returns an object like { explanation: "..." }
      setAiExplanation(data.explanation || "No explanation provided.");

    } catch (e) {
      //setAiError(e || "Failed to fetch analysis.");
    } finally {
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
        // New layout wrapper for side-by-side components
        <div className="w-full max-w-6xl mx-auto flex flex-col md:flex-row gap-6">
          
          {/* Left Panel */}
          <div className="flex-1">
            <WalletHealth
              address={address}
              chainId={chainId}
              // Pass new props to WalletHealth
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