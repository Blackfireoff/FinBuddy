"use client";

import { useEffect, useState } from "react";

export default function WalletHealth({ address }) {
  const [data, setData] = useState(null);
  const [transactions , setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!address) return;

    const fetchWalletData = async () => {
      try {
        const reswallet = await fetch(`https://eth.blockscout.com/api/v2/addresses/${address}`);
        const restrans = await fetch(`https://eth.blockscout.com/api/v2/addresses/${address}/transactions`);
        if (!reswallet.ok) throw new Error("Failed to fetch wallet data");
          const resultwallet = await res.json();
          setData(result);
      if (!res.ok) throw new Error("Failed to fetch transactions");
      const result = await res.json();
      console.log("Transactions:", result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchWalletData();
  }, [address]);

  const fetchTransactions = async () => {
    try {

      setTransactions(result.items || []);
    } catch (err) {
      console.error(err);
    }
  }

  if (loading) return <div className="text-gray-500">Loading wallet data...</div>;
  if (error) return <div className="text-red-600">Error: {error}</div>;
  if (!data) return null;

  return (
    <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-md w-full max-w-lg mx-auto">
      <h2 className="text-xl font-semibold mb-4 text-center">💰 Wallet Global Health</h2>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Address:</span>
          <span className="truncate max-w-[160px] text-right">{address}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-500">ETH Balance:</span>
          <span>{Number(data?.coin_balance || 0).toFixed(4)} {data.coin_balance?.symbol || "ETH"}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-500">Transactions:</span>
          <span>{data.transaction_count}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-500">Contract Type:</span>
          <span>{data.smart_contract ? "Smart Contract" : "Externally Owned"}</span>
        </div>
      </div>

      <div className="mt-6 text-center">
        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs">
          {data.transaction_count > 100 ? "Active wallet" : "Low activity"}
        </span>
      </div>
    </div>
  );
}