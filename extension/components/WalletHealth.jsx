import { useEffect, useState } from "react";

export default function WalletHealth({ address }) {
  const [data, setData] = useState(null);
  const [transactions , setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!address) return;

    const fetchWalletData = async () => {
      
        fetch(`https://eth.blockscout.com/api/v2/addresses/${address}`).then(async (reswallet) => {
          try {
            if (!reswallet.ok) throw new Error("Failed to fetch wallet data");
              let res  = await reswallet.json();
              setData(res);
            } catch (err) {
              setError(err.message);
            } finally {
              setLoading(false);
            }
          });
         fetch(`https://eth.blockscout.com/api/v2/addresses/${address}/transactions`).then(async (restransactions) => {
          try {
            if (!restransactions.ok) throw new Error("Failed to fetch transactions");
              let res = await restransactions.json();
              setTransactions(res.items || []);
            } catch (err) {
              setError(err.message);
            } finally {
              setLoading(false);
            }
          });
    };
    fetchWalletData();
  }, [address]);

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
        <div>
          <h3 className="text-gray-500 mb-2">Recent Transactions:</h3>
          {transactions.length > 0 ? (
            <div className="max-h-64 overflow-y-auto border rounded-lg p-2 space-y-2 bg-gray-50 dark:bg-gray-800">
              {transactions.slice(0, 10).map((tx) => (
                <div key={tx.hash} className="p-2 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium truncate max-w-[150px]">
                      Hash:{" "}
                      <a
                        href={`https://eth.blockscout.com/tx/${tx.hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {tx.hash.slice(0, 10)}...
                      </a>
                    </span>
                    <span className="text-gray-500">{new Date(tx.timestamp).toLocaleString()}</span>
                  </div>

                  <div className="flex justify-between text-xs mt-1">
                    <span>From:</span>
                    <span className="truncate max-w-[120px]">{tx.from?.hash?.slice(0, 10)}...</span>
                  </div>

                  <div className="flex justify-between text-xs">
                    <span>To:</span>
                    <span className="truncate max-w-[120px]">{tx.to?.hash?.slice(0, 10) || "Contract Creation"}</span>
                  </div>

                  <div className="text-right text-xs mt-1">
                    <span className="text-green-600">{Number(tx.value) / 1e18} ETH</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No transactions found.</p>
          )}
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