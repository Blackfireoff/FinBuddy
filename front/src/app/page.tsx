"use client";

import { useState } from "react";
import WalletHealth from "./components/WalletHealth";
import ConnectWallet from "./components/ConnectWallet.jsx";

export default function Home() {
    const [address, setAddress] = useState("");
    const [chainId, setChainId] = useState("");

    return (
        <main className="p-8 flex flex-col items-center space-y-6">
            <ConnectWallet
                onAddress={setAddress}
                onChainId={setChainId}
                desiredChainId="0xaa36a7"   // Sepolia (optionnel: supprime si tu ne veux pas forcer)
                allowNetworkSwitch={true}
            />
            {address && <WalletHealth address={address} chainId={chainId} />}
        </main>
    );
}
