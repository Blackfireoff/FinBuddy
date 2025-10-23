"use client";
import { useState } from "react";
import WalletHealth from "./components/WalletHealth";

export default function Home() {
  const [address, setAddress] = useState("");

  return (
    <main className="p-8 flex flex-col items-center space-y-6">
      <input
        type="text"
        placeholder="Enter wallet address"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        className="border rounded-lg p-2 w-80 text-center"
      />
      {address && <WalletHealth address={address} />}
    </main>
  );
}