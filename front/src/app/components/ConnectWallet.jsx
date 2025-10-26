"use client";

import { useEffect, useMemo, useState } from "react";

// Réseaux proposés
const CHAINS = [
    {
        id: "0x1",
        name: "Ethereum Mainnet",
        params: {
            chainId: "0x1",
            chainName: "Ethereum Mainnet",
            nativeCurrency: { name: "Ether", symbol: "ETH", decimals: 18 },
            rpcUrls: ["https://rpc.ankr.com/eth"],
            blockExplorerUrls: ["https://etherscan.io"],
        },
    },
    {
        id: "0xaa36a7",
        name: "Sepolia",
        params: {
            chainId: "0xaa36a7",
            chainName: "Sepolia",
            nativeCurrency: { name: "Sepolia Ether", symbol: "ETH", decimals: 18 },
            rpcUrls: ["https://rpc.sepolia.org"],
            blockExplorerUrls: ["https://sepolia.etherscan.io"],
        },
    },
    {
        id: "0x89",
        name: "Polygon",
        params: {
            chainId: "0x89",
            chainName: "Polygon",
            nativeCurrency: { name: "MATIC", symbol: "MATIC", decimals: 18 },
            rpcUrls: ["https://polygon-rpc.com"],
            blockExplorerUrls: ["https://polygonscan.com"],
        },
    },
];

function getProvider() {
    if (typeof window === "undefined") return undefined;
    return window.ethereum;
}

export default function ConnectWallet({
                                          onAddress,
                                          onChainId,              // <- remonte le chainId au parent
                                          autoConnect = true,
                                          desiredChainId,         // ex: "0xaa36a7" pour forcer Sepolia (optionnel)
                                          allowNetworkSwitch = true,
                                      }) {
    const [address, setAddress] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [chainId, setChainId] = useState("");
    const [targetChainId, setTargetChainId] = useState(desiredChainId || "");

    const chainName = useMemo(() => {
        const found = CHAINS.find(c => c.id.toLowerCase() === (chainId || "").toLowerCase());
        return found?.name || (chainId ? `Unknown (${chainId})` : "—");
    }, [chainId]);

    const setAddr = (addr) => {
        setAddress(addr);
        if (typeof onAddress === "function") onAddress(addr);
    };
    const setCid = (cid) => {
        setChainId(cid);
        if (typeof onChainId === "function") onChainId(cid);
    };

    // Auto-connexion + lecture du réseau si autorisé
    useEffect(() => {
        const provider = getProvider();
        if (!provider) return;

        (async () => {
            try {
                const cid = await provider.request({ method: "eth_chainId" });
                setCid(cid);

                if (autoConnect) {
                    const accounts = await provider.request({ method: "eth_accounts" });
                    if (accounts && accounts.length > 0) setAddr(accounts[0]);
                }

                if (desiredChainId && cid?.toLowerCase() !== desiredChainId.toLowerCase()) {
                    await switchToChain(desiredChainId);
                }
            } catch {
                /* noop */
            }
        })();
    }, [autoConnect, desiredChainId]);

    // Sync compte + réseau
    useEffect(() => {
        const provider = getProvider();
        if (!provider?.on) return;

        const handleAccounts = (accounts) => setAddr(accounts?.[0] || "");
        const handleChain = (cid) => setCid(cid);

        provider.on("accountsChanged", handleAccounts);
        provider.on("chainChanged", handleChain);
        return () => {
            provider.removeListener?.("accountsChanged", handleAccounts);
            provider.removeListener?.("chainChanged", handleChain);
        };
    }, []);

    const connect = async () => {
        setError("");
        const provider = getProvider();
        if (!provider) {
            setError("Aucun wallet détecté. Installe MetaMask ou un wallet compatible.");
            return;
        }
        try {
            setLoading(true);
            const accounts = await provider.request({ method: "eth_requestAccounts" });
            if (accounts && accounts.length > 0) setAddr(accounts[0]);

            const cid = await provider.request({ method: "eth_chainId" });
            setCid(cid);

            const wanted = desiredChainId || targetChainId;
            if (wanted && cid?.toLowerCase() !== wanted.toLowerCase()) {
                await switchToChain(wanted);
            }
        } catch (e) {
            setError(e?.message || "Connexion refusée.");
        } finally {
            setLoading(false);
        }
    };

    const switchToChain = async (hexChainId) => {
        setError("");
        const provider = getProvider();
        if (!provider) {
            setError("Wallet introuvable pour changer de réseau.");
            return;
        }
        try {
            await provider.request({
                method: "wallet_switchEthereumChain",
                params: [{ chainId: hexChainId }],
            });
            setCid(hexChainId);
        } catch (e) {
            if (e?.code === 4902) {
                const found = CHAINS.find(c => c.id.toLowerCase() === hexChainId.toLowerCase());
                if (!found) {
                    setError("Réseau non supporté dans la config du bouton.");
                    return;
                }
                try {
                    await provider.request({
                        method: "wallet_addEthereumChain",
                        params: [found.params],
                    });
                    setCid(found.id);
                } catch (addErr) {
                    setError(addErr?.message || "Ajout de réseau refusé.");
                }
            } else {
                setError(e?.message || "Changement de réseau refusé.");
            }
        }
    };

    return (
        <div className="flex flex-col items-center gap-3">
            <button
                onClick={connect}
                disabled={loading}
                className="px-4 py-2 rounded-lg border font-medium hover:opacity-90 disabled:opacity-60"
                aria-busy={loading}
            >
                {address ? "Wallet connecté ✅" : loading ? "Connexion..." : "Connect Wallet"}
            </button>

            {address && (
                <div className="text-xs opacity-80">
                    Adresse: <span className="font-mono">{address}</span>
                </div>
            )}

            <div className="text-xs opacity-80">
                Réseau: <span className="font-mono">{chainName}</span>
            </div>

            {allowNetworkSwitch && (
                <div className="flex items-center gap-2">
                    <select
                        className="border rounded-md px-2 py-1"
                        value={targetChainId || chainId || ""}
                        onChange={(e) => setTargetChainId(e.target.value)}
                    >
                        <option value="" disabled>Choisir un réseau…</option>
                        {CHAINS.map((c) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                    <button
                        className="px-3 py-1 rounded-md border hover:opacity-90"
                        onClick={() => switchToChain(targetChainId || chainId)}
                        disabled={!targetChainId && !chainId}
                    >
                        Switch
                    </button>
                </div>
            )}

            {error && <div className="text-sm text-red-600">{error}</div>}

            {!getProvider() && (
                <a
                    className="text-sm underline opacity-80"
                    href="https://metamask.io/download/"
                    target="_blank"
                    rel="noreferrer"
                >
                    Installer MetaMask
                </a>
            )}
        </div>
    );
}
