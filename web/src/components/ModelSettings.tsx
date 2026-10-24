"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Shield,
  Key,
  Server,
  Cloud,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Eye,
  EyeOff,
  Check,
} from "lucide-react";

export type ProviderMode = "groq" | "byok" | "ollama";

export interface ProviderConfig {
  mode: ProviderMode;
  byokKey: string;
  byokBaseUrl: string;
  byokModel: string;
  ollamaBaseUrl: string;
  ollamaModel: string;
}

interface ModelSettingsProps {
  isOpen: boolean;
  onClose: () => void;
  config: ProviderConfig;
  onSave: (config: ProviderConfig) => void;
  apiUrl?: string;
}

export function ModelSettings({
  isOpen,
  onClose,
  config,
  onSave,
  apiUrl = "http://localhost:8000",
}: ModelSettingsProps) {
  const [mode, setMode] = useState<ProviderMode>(config.mode);
  const [byokKey, setByokKey] = useState(config.byokKey);
  const [byokBaseUrl, setByokBaseUrl] = useState(config.byokBaseUrl);
  const [byokModel, setByokModel] = useState(config.byokModel);
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState(config.ollamaBaseUrl);
  const [ollamaModel, setOllamaModel] = useState(config.ollamaModel);

  const [showKey, setShowKey] = useState(false);
  const [isTestingOllama, setIsTestingOllama] = useState(false);
  const [ollamaStatus, setOllamaStatus] = useState<{
    tested: boolean;
    online: boolean;
    message: string;
  }>({ tested: false, online: false, message: "" });
  const [savedToast, setSavedToast] = useState(false);

  // Sync internal state when config changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setMode(config.mode);
      setByokKey(config.byokKey);
      setByokBaseUrl(config.byokBaseUrl);
      setByokModel(config.byokModel);
      setOllamaBaseUrl(config.ollamaBaseUrl);
      setOllamaModel(config.ollamaModel);
      setOllamaStatus({ tested: false, online: false, message: "" });
      setSavedToast(false);
    }
  }, [isOpen, config]);

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const testOllamaConnection = async () => {
    setIsTestingOllama(true);
    setOllamaStatus({ tested: false, online: false, message: "Testing connectivity..." });
    try {
      const res = await fetch(`${apiUrl}/v1/models`);
      if (res.ok) {
        const data = await res.json();
        const ollamaMode = (data.modes || []).find(
          (m: { provider: string }) => m.provider === "ollama"
        );
        if (ollamaMode && ollamaMode.detected) {
          setOllamaStatus({
            tested: true,
            online: true,
            message: `Ollama service online at ${ollamaBaseUrl || "http://localhost:11434"}`,
          });
        } else {
          setOllamaStatus({
            tested: true,
            online: false,
            message: "API reachable, but Ollama service is not responding. Ensure 'ollama serve' is running.",
          });
        }
      } else {
        setOllamaStatus({
          tested: true,
          online: false,
          message: "Allcited API returned an error probing models.",
        });
      }
    } catch {
      setOllamaStatus({
        tested: true,
        online: false,
        message: "Failed to connect to API gateway to test Ollama.",
      });
    } finally {
      setIsTestingOllama(false);
    }
  };

  const handleSave = () => {
    const updated: ProviderConfig = {
      mode,
      byokKey: byokKey.trim(),
      byokBaseUrl: byokBaseUrl.trim(),
      byokModel: byokModel.trim() || "gpt-4o-mini",
      ollamaBaseUrl: ollamaBaseUrl.trim() || "http://localhost:11434",
      ollamaModel: ollamaModel.trim() || "llama3.2",
    };

    // Store strictly in localStorage (browser-only)
    if (typeof window !== "undefined") {
      localStorage.setItem("allcited_provider_mode", updated.mode);
      localStorage.setItem("allcited_byok_key", updated.byokKey);
      localStorage.setItem("allcited_byok_base_url", updated.byokBaseUrl);
      localStorage.setItem("allcited_byok_model", updated.byokModel);
      localStorage.setItem("allcited_ollama_base_url", updated.ollamaBaseUrl);
      localStorage.setItem("allcited_ollama_model", updated.ollamaModel);
    }

    onSave(updated);
    setSavedToast(true);
    setTimeout(() => {
      setSavedToast(false);
      onClose();
    }, 700);
  };

  const clearBYOK = () => {
    setByokKey("");
    if (typeof window !== "undefined") {
      localStorage.removeItem("allcited_byok_key");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="w-full max-w-xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden max-h-[90vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
                LLM Provider Settings
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Choose cloud, BYOK key, or local private Ollama inference
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-sm">
          {/* Provider Tabs */}
          <div className="grid grid-cols-3 gap-2 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
            <button
              type="button"
              onClick={() => setMode("groq")}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                mode === "groq"
                  ? "bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <Cloud className="w-3.5 h-3.5" />
              <span>Groq Cloud</span>
            </button>

            <button
              type="button"
              onClick={() => setMode("byok")}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                mode === "byok"
                  ? "bg-white dark:bg-slate-900 text-purple-600 dark:text-purple-400 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <Key className="w-3.5 h-3.5" />
              <span>BYOK Key</span>
            </button>

            <button
              type="button"
              onClick={() => setMode("ollama")}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                mode === "ollama"
                  ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-sm"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>Local Ollama</span>
            </button>
          </div>

          {/* Mode 1: Groq Cloud */}
          {mode === "groq" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="p-4 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/50 dark:bg-blue-950/20 text-xs space-y-2">
                <div className="flex items-center gap-2 font-semibold text-blue-900 dark:text-blue-300">
                  <Cloud className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span>Default Free Cloud Inference</span>
                </div>
                <p className="text-blue-800 dark:text-blue-300/80 leading-relaxed">
                  Fast high-throughput answering using Groq Llama 3 models. No API keys or setup required.
                </p>
              </div>

              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 space-y-1.5 text-xs">
                <div className="flex justify-between text-slate-500">
                  <span>Engine:</span>
                  <span className="font-medium text-slate-700 dark:text-slate-300">Groq LPUs</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Default Model:</span>
                  <span className="font-mono text-slate-700 dark:text-slate-300">llama-3.3-70b-versatile</span>
                </div>
                <div className="flex justify-between text-slate-500">
                  <span>Usage Cost:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">₹0 (Free Tier)</span>
                </div>
              </div>
            </div>
          )}

          {/* Mode 2: BYOK */}
          {mode === "byok" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              {/* Security Banner */}
              <div className="p-3.5 rounded-xl border border-purple-200 dark:border-purple-800/60 bg-purple-50/70 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200 text-xs flex gap-3">
                <Shield className="w-4 h-4 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold">Your key stays in your browser</div>
                  <p className="text-purple-800/90 dark:text-purple-300/90 leading-relaxed text-[11px]">
                    BYOK credentials are saved strictly in your browser&apos;s <code className="bg-purple-200 dark:bg-purple-900/60 px-1 py-0.5 rounded">localStorage</code>. They are sent directly via client headers (<code className="bg-purple-200 dark:bg-purple-900/60 px-1 py-0.5 rounded">X-BYOK-Key</code>) and are <strong>never stored on the server</strong>, never written to disk, and never logged.
                  </p>
                </div>
              </div>

              {/* Quick Presets */}
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-500">Quick Endpoint Presets:</label>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => {
                      setByokBaseUrl("https://api.openai.com/v1");
                      setByokModel("gpt-4o-mini");
                    }}
                    className="px-2.5 py-1 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    OpenAI (gpt-4o-mini)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setByokBaseUrl("https://openrouter.ai/api/v1");
                      setByokModel("anthropic/claude-3.5-haiku");
                    }}
                    className="px-2.5 py-1 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    OpenRouter
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setByokBaseUrl("https://api.groq.com/openai/v1");
                      setByokModel("llama-3.3-70b-versatile");
                    }}
                    className="px-2.5 py-1 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    Groq Cloud
                  </button>
                </div>
              </div>

              {/* Form Fields */}
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                      API Key
                    </label>
                    {byokKey && (
                      <button
                        type="button"
                        onClick={clearBYOK}
                        className="text-[11px] text-rose-500 hover:underline"
                      >
                        Clear Key
                      </button>
                    )}
                  </div>
                  <div className="relative">
                    <input
                      type={showKey ? "text" : "password"}
                      value={byokKey}
                      onChange={(e) => setByokKey(e.target.value)}
                      placeholder="sk-..."
                      className="w-full px-3 py-2 pr-9 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Base URL
                    </label>
                    <input
                      type="text"
                      value={byokBaseUrl}
                      onChange={(e) => setByokBaseUrl(e.target.value)}
                      placeholder="https://api.openai.com/v1"
                      className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Model Name
                    </label>
                    <input
                      type="text"
                      value={byokModel}
                      onChange={(e) => setByokModel(e.target.value)}
                      placeholder="gpt-4o-mini"
                      className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Mode 3: Ollama */}
          {mode === "ollama" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/70 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200 text-xs flex gap-3">
                <Server className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold">Private & Local Execution</div>
                  <p className="text-emerald-800/90 dark:text-emerald-300/90 leading-relaxed text-[11px]">
                    100% offline document Q&A. Model weights run directly on your workstation hardware. Zero data leaves your machine.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Ollama Base URL
                  </label>
                  <input
                    type="text"
                    value={ollamaBaseUrl}
                    onChange={(e) => setOllamaBaseUrl(e.target.value)}
                    placeholder="http://localhost:11434"
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Model Tag
                  </label>
                  <input
                    type="text"
                    value={ollamaModel}
                    onChange={(e) => setOllamaModel(e.target.value)}
                    placeholder="llama3.2"
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* Test Button & Result */}
              <div className="pt-1">
                <button
                  type="button"
                  onClick={testOllamaConnection}
                  disabled={isTestingOllama}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-50 cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isTestingOllama ? "animate-spin" : ""}`} />
                  <span>Test Ollama Connection</span>
                </button>

                {ollamaStatus.tested && (
                  <div
                    className={`mt-2.5 p-2.5 rounded-lg text-xs flex items-center gap-2 border ${
                      ollamaStatus.online
                        ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 border-emerald-200 dark:border-emerald-800"
                        : "bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-200 border-amber-200 dark:border-amber-800"
                    }`}
                  >
                    {ollamaStatus.online ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                    )}
                    <span>{ollamaStatus.message}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 flex items-center justify-between flex-shrink-0">
          <div className="text-xs text-slate-400">
            {savedToast ? (
              <span className="text-emerald-600 dark:text-emerald-400 font-medium flex items-center gap-1">
                <Check className="w-3.5 h-3.5" />
                Settings saved!
              </span>
            ) : (
              <span>Changes take effect on your next question</span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="px-4 py-1.5 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors cursor-pointer"
            >
              Apply Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
