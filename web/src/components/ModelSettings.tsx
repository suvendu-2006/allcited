"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  Key,
  Server,
  Cloud,
  CheckCircle2,
  AlertTriangle,
  Eye,
  EyeOff,
  Check,
  Loader2,
} from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/Input";

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
  apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
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
    setOllamaStatus({ tested: false, online: false, message: "Testing connectivity…" });
    const targetUrl = ollamaBaseUrl.trim() || "http://localhost:11434";
    try {
      // 1. Try direct browser check to the configured Ollama URL
      let isOnline = false;
      try {
        const directRes = await fetch(`${targetUrl.replace(/\/$/, "")}/api/tags`, {
          signal: AbortSignal.timeout(1200),
        });
        if (directRes.ok) isOnline = true;
      } catch {
        // Direct probe failed (e.g. CORS or network boundary), fallback to backend probe
      }

      // 2. Fallback to checking via backend endpoint
      if (!isOnline) {
        const res = await fetch(`${apiUrl}/v1/models`);
        if (res.ok) {
          const data = await res.json();
          const ollamaMode = (data.modes || []).find(
            (m: { provider: string }) => m.provider === "ollama"
          );
          if (ollamaMode && ollamaMode.detected) {
            isOnline = true;
          }
        }
      }

      if (isOnline) {
        setOllamaStatus({
          tested: true,
          online: true,
          message: `Ollama service online at ${targetUrl}`,
        });
      } else {
        setOllamaStatus({
          tested: true,
          online: false,
          message: "Can't reach your local Ollama. Is it running? (ollama serve)",
        });
      }
    } catch {
      setOllamaStatus({
        tested: true,
        online: false,
        message: "Can't reach your local Ollama. Is it running? (ollama serve)",
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
    }, 1200);
  };

  const keyFingerprint = byokKey ? `••••${byokKey.slice(-4)}` : "••••7f2a";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        className="bg-bg-surface border border-border rounded-interactive shadow-2xl max-w-lg w-full max-h-[90vh] flex flex-col overflow-hidden animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between px-6 py-4 border-b border-border bg-bg-surface/90">
          <div>
            <h2 className="text-base font-semibold text-ink-primary font-display">
              Who does the thinking?
            </h2>
            <p className="text-xs text-gray-warm mt-0.5">
              Choose your reasoning engine and privacy model.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close settings"
            className="p-1 rounded-[4px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs text-ink-primary">
          {savedToast && (
            <div className="p-3 rounded-interactive bg-accent-primary/10 border border-accent-primary/30 text-ink-primary flex items-center gap-2 font-mono text-xs animate-fade-in">
              <Check className="w-4 h-4 text-accent-primary" />
              <span>Key saved — only you can see the last four: {keyFingerprint}</span>
            </div>
          )}

          <label
            className={`flex items-start gap-3 p-3.5 rounded-interactive border cursor-pointer transition-all ${
              mode === "groq"
                ? "border-accent-primary bg-accent-primary/5 ring-1 ring-accent-primary/30"
                : "border-border bg-bg-surface hover:bg-bg-sunken/40"
            }`}
          >
            <input
              type="radio"
              name="provider_mode"
              checked={mode === "groq"}
              onChange={() => setMode("groq")}
              className="mt-1 text-accent-primary focus:ring-accent-primary"
            />
            <div className="flex-1">
              <div className="flex items-center gap-1.5 font-semibold text-sm text-ink-primary">
                <Cloud className="w-4 h-4 text-accent-primary" />
                <span>Allcited Free</span>
              </div>
              <p className="text-xs text-gray-warm mt-0.5">
                Our key, shared fairly. Busy at peak times.
              </p>
            </div>
          </label>

          <div
            className={`p-3.5 rounded-interactive border transition-all ${
              mode === "byok"
                ? "border-accent-primary bg-accent-primary/5 ring-1 ring-accent-primary/30"
                : "border-border bg-bg-surface hover:bg-bg-sunken/40"
            }`}
          >
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="provider_mode"
                checked={mode === "byok"}
                onChange={() => setMode("byok")}
                className="mt-1 text-accent-primary focus:ring-accent-primary"
              />
              <div className="flex-1">
                <div className="flex items-center gap-1.5 font-semibold text-sm text-ink-primary">
                  <Key className="w-4 h-4 text-accent-primary" />
                  <span>Your own key</span>
                </div>
                <p className="text-xs text-gray-warm mt-0.5">
                  Your key, your speed, your limits.
                </p>
                <p className="font-sans text-[11px] text-gray-warm mt-1.5 bg-bg-sunken p-2 border border-border/60">
                  Stays in your browser. Never stored, never logged, never sent anywhere but your provider.
                </p>
              </div>
            </label>

            {mode === "byok" && (
              <div className="mt-3.5 pt-3 border-t border-border/60 space-y-3 pl-7">
                <div>
                  <label className="block text-[11px] font-mono text-gray-warm mb-1">
                    API Key (OpenAI, Anthropic, or Groq)
                  </label>
                  <div className="relative">
                    <Input
                      type={showKey ? "text" : "password"}
                      placeholder="sk-..."
                      value={byokKey}
                      onChange={(e) => setByokKey(e.target.value)}
                      className="pr-9 font-mono text-xs"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-ghost hover:text-ink-primary"
                    >
                      {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                  {byokKey && (
                    <span className="font-mono text-[10px] text-gray-warm mt-1 block">
                      fingerprint: {keyFingerprint}
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] font-mono text-gray-warm mb-1">
                      Model ID
                    </label>
                    <Input
                      type="text"
                      placeholder="gpt-4o-mini"
                      value={byokModel}
                      onChange={(e) => setByokModel(e.target.value)}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-gray-warm mb-1">
                      Custom Base URL (optional)
                    </label>
                    <Input
                      type="text"
                      placeholder="https://api.openai.com/v1"
                      value={byokBaseUrl}
                      onChange={(e) => setByokBaseUrl(e.target.value)}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div
            className={`p-3.5 rounded-interactive border transition-all ${
              mode === "ollama"
                ? "border-accent-primary bg-accent-primary/5 ring-1 ring-accent-primary/30"
                : "border-border bg-bg-surface hover:bg-bg-sunken/40"
            }`}
          >
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="radio"
                name="provider_mode"
                checked={mode === "ollama"}
                onChange={() => setMode("ollama")}
                className="mt-1 text-accent-primary focus:ring-accent-primary"
              />
              <div className="flex-1">
                <div className="flex items-center gap-1.5 font-semibold text-sm text-ink-primary">
                  <Server className="w-4 h-4 text-accent-primary" />
                  <span>Local (Ollama)</span>
                </div>
                <p className="text-xs text-gray-warm mt-0.5">
                  Runs on your machine. Nothing leaves it.
                </p>
              </div>
            </label>

            {mode === "ollama" && (
              <div className="mt-3.5 pt-3 border-t border-border/60 space-y-3 pl-7">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] font-mono text-gray-warm mb-1">
                      Ollama Host
                    </label>
                    <Input
                      type="text"
                      placeholder="http://localhost:11434"
                      value={ollamaBaseUrl}
                      onChange={(e) => setOllamaBaseUrl(e.target.value)}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-mono text-gray-warm mb-1">
                      Model Name
                    </label>
                    <Input
                      type="text"
                      placeholder="llama3.2"
                      value={ollamaModel}
                      onChange={(e) => setOllamaModel(e.target.value)}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={isTestingOllama}
                    onClick={testOllamaConnection}
                    className="text-xs h-7 gap-1"
                  >
                    {isTestingOllama && <Loader2 className="w-3 h-3 animate-spin" />}
                    <span>{isTestingOllama ? "Probing…" : "Probe Ollama"}</span>
                  </Button>

                  {ollamaStatus.tested && (
                    <span
                      className={`font-mono text-[11px] flex items-center gap-1 ${
                        ollamaStatus.online ? "text-accent-primary" : "text-danger"
                      }`}
                    >
                      {ollamaStatus.online ? (
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      ) : (
                        <AlertTriangle className="w-3.5 h-3.5" />
                      )}
                      <span>{ollamaStatus.message}</span>
                    </span>
                  )}
                </div>

                <p className="font-sans text-[10px] text-gray-warm">
                  Local mode needs Allcited running on your computer. On the web, pick another mode.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border flex items-center justify-end gap-2 bg-bg-surface/90">
          <Button variant="ghost" size="sm" onClick={onClose} className="text-xs">
            Cancel
          </Button>
          <Button variant="primary" size="sm" onClick={handleSave} className="text-xs">
            Save changes
          </Button>
        </div>
      </div>
    </div>
  );
}
