"use client";

import { useEffect, useMemo, useState } from "react";

/**
 * SettingsModal
 * - Configure AI provider/model and API key
 * - When provider is 'ollama' (LLaMA local), API key field is disabled
 */
export default function SettingsModal({ isOpen, onClose, onSave, initialConfig }) {
  const [provider, setProvider] = useState(initialConfig?.provider || "ollama");
  const [apiKey, setApiKey] = useState(initialConfig?.api_key || "");
  const [error, setError] = useState("");

  useEffect(() => {
    setProvider(initialConfig?.provider || "ollama");
    setApiKey(initialConfig?.api_key || "");
    setError("");
  }, [initialConfig, isOpen]);

  const isOllama = useMemo(() => provider === "ollama", [provider]);

  const handleSave = () => {
    // Validate
    if (!isOllama && !apiKey.trim()) {
      setError("La clé API est obligatoire pour ce modèle.");
      return;
    }
    setError("");
    onSave?.({ provider, api_key: isOllama ? "" : apiKey.trim() });
    onClose?.();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-xl bg-[#0e1a26] text-white shadow-xl border border-white/10">
        <div className="flex items-center justify-between p-4 border-b border-white/10">
          <h3 className="text-lg font-semibold">Paramètres IA</h3>
          <button onClick={onClose} className="text-white/70 hover:text-white">✕</button>
        </div>

        <div className="p-4 space-y-4">
          <div>
            <label className="block text-sm mb-1">Modèle</label>
            <select
              className="w-full bg-white/10 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="ollama">LLaMA (Ollama local)</option>
              <option value="openai">OpenAI (o4-mini)</option>
              <option value="gemini">Gemini (2.5-flash)</option>
              <option value="groq">Groq (LLaMA 3.3 70B)</option>
              <option value="deepseek">DeepSeek (chat)</option>
            </select>
            <p className="mt-1 text-xs text-white/50">
              Sélectionnez le fournisseur de modèle IA. LLaMA via Ollama ne nécessite pas de clé API.
            </p>
          </div>

          <div>
            <label className="block text-sm mb-1">Clé API</label>
            <input
              type="password"
              className={`w-full bg-white/10 border border-white/10 rounded-md px-3 py-2 outline-none focus:ring-2 ${
                isOllama ? "opacity-60 cursor-not-allowed" : "focus:ring-blue-500"
              }`}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={isOllama ? "Non requise pour LLaMA (Ollama)" : "Saisissez votre clé API"}
              disabled={isOllama}
            />
            {!isOllama && (
              <p className="mt-1 text-xs text-white/50">Ce champ est obligatoire pour ce fournisseur.</p>
            )}
          </div>

          {error && (
            <div className="text-red-400 text-sm">{error}</div>
          )}
        </div>

        <div className="p-4 border-t border-white/10 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-md bg-white/10 hover:bg-white/15"
          >
            Annuler
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 font-semibold"
          >
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
}

