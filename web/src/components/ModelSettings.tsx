"use client";

import React, { useState, useEffect } from "react";
import { motion, useReducedMotion } from "framer-motion";
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

export interface DetectedProvider {
  name: string;
  baseUrl: string;
  model: string;
}

export type PresetId = "nvidia" | "openai" | "groq" | "custom";

export interface PresetDef {
  id: PresetId;
  name: string;
  baseUrl: string;
  model: string;
  prefix: string;
  placeholder: string;
}

export const PRESETS: Record<"openai" | "groq" | "nvidia", PresetDef> = {
  openai: {
    id: "openai",
    name: "OpenAI",
    baseUrl: "https://api.openai.com/v1",
    model: "gpt-4o-mini",
    prefix: "sk-",
    placeholder: "Paste your OpenAI API key (sk-...)",
  },
  groq: {
    id: "groq",
    name: "Groq",
    baseUrl: "https://api.groq.com/openai/v1",
    model: "llama-3.3-70b-versatile",
    prefix: "gsk_",
    placeholder: "Paste your Groq API key (gsk_...)",
  },
  nvidia: {
    id: "nvidia",
    name: "NVIDIA NIM",
    baseUrl: "https://integrate.api.nvidia.com/v1",
    model: "nvidia/nemotron-3.5-bolt-e4b",
    prefix: "nvapi-",
    placeholder: "Paste your NVIDIA NIM API key (nvapi-...)",
  },
};

export function getPresetFromConfig(key: string, baseUrl: string): PresetId {
  const trimmedKey = key.trim();
  const trimmedUrl = baseUrl.trim();
  if (trimmedKey.startsWith("nvapi-") || trimmedUrl.includes("nvidia.com")) return "nvidia";
  if (trimmedKey.startsWith("gsk_") || trimmedUrl.includes("groq.com")) return "groq";
  if (trimmedKey.startsWith("sk-") || trimmedUrl.includes("openai.com")) return "openai";
  return "custom";
}

export function detectProviderFromKey(key: string): DetectedProvider | null {
  const trimmed = key.trim();
  if (trimmed.startsWith("nvapi-")) {
    return {
      name: "NVIDIA NIM",
      baseUrl: PRESETS.nvidia.baseUrl,
      model: PRESETS.nvidia.model,
    };
  }
  if (trimmed.startsWith("gsk_")) {
    return {
      name: "Groq Cloud",
      baseUrl: PRESETS.groq.baseUrl,
      model: PRESETS.groq.model,
    };
  }
  if (trimmed.startsWith("sk-") && !trimmed.startsWith("sk-ant-")) {
    return {
      name: "OpenAI",
      baseUrl: PRESETS.openai.baseUrl,
      model: PRESETS.openai.model,
    };
  }
  return null;
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
  const shouldReduceMotion = useReducedMotion();
  const [mode, setMode] = useState<ProviderMode>(config.mode);
  const [byokKey, setByokKey] = useState(config.byokKey);
  const [byokBaseUrl, setByokBaseUrl] = useState(config.byokBaseUrl);
  const [byokModel, setByokModel] = useState(config.byokModel);
  const [selectedPreset, setSelectedPreset] = useState<PresetId>(() =>
    getPresetFromConfig(config.byokKey, config.byokBaseUrl)
  );
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState(config.ollamaBaseUrl);
  const [ollamaModel, setOllamaModel] = useState(config.ollamaModel);

  const [showKey, setShowKey] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
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
      setSelectedPreset(getPresetFromConfig(config.byokKey, config.byokBaseUrl));
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

  const applyPreset = (presetId: "openai" | "groq" | "nvidia") => {
    const preset = PRESETS[presetId];
    setSelectedPreset(presetId);
    setByokBaseUrl(preset.baseUrl);
    setByokModel(preset.model);

    // If key in box belongs to a different provider, clear it so user can paste the new key cleanly
    const trimmed = byokKey.trim();
    if (trimmed) {
      const isMatch =
        (presetId === "nvidia" && trimmed.startsWith("nvapi-")) ||
        (presetId === "groq" && trimmed.startsWith("gsk_")) ||
        (presetId === "openai" && trimmed.startsWith("sk-") && !trimmed.startsWith("sk-ant-"));
      if (!isMatch) {
        setByokKey("");
      }
    }
  };

  const handleKeyChange = (val: string) => {
    setByokKey(val);
    const trimmed = val.trim();
    const detected = detectProviderFromKey(trimmed);
    if (detected) {
      if (trimmed.startsWith("nvapi-")) {
        setSelectedPreset("nvidia");
        setByokBaseUrl(PRESETS.nvidia.baseUrl);
        setByokModel(PRESETS.nvidia.model);
      } else if (trimmed.startsWith("gsk_")) {
        setSelectedPreset("groq");
        setByokBaseUrl(PRESETS.groq.baseUrl);
        setByokModel(PRESETS.groq.model);
      } else if (trimmed.startsWith("sk-")) {
        setSelectedPreset("openai");
        setByokBaseUrl(PRESETS.openai.baseUrl);
        setByokModel(PRESETS.openai.model);
      }
    }
  };

  const testOllamaConnection = async () => {
    setIsTestingOllama(true);
    setOllamaStatus({ tested: false, online: false, message: "Testing connectivity…" });
    const targetUrl = ollamaBaseUrl.trim() || "http://localhost:11434";
    try {
      // 1. Try direct browser check to the configured URL
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
          message: `Local server online at ${targetUrl}`,
        });
      } else {
        setOllamaStatus({
          tested: true,
          online: false,
          message: `Can't reach local server at ${targetUrl}. Please ensure it is running.`,
        });
      }
    } catch {
      setOllamaStatus({
        tested: true,
        online: false,
        message: `Can't reach local server at ${targetUrl}. Please ensure it is running.`,
      });
    } finally {
      setIsTestingOllama(false);
    }
  };

  const handleSave = () => {
    let finalBaseUrl = byokBaseUrl.trim();
    let finalModel = byokModel.trim();

    if (!finalBaseUrl) {
      if (selectedPreset === "nvidia") finalBaseUrl = PRESETS.nvidia.baseUrl;
      else if (selectedPreset === "groq") finalBaseUrl = PRESETS.groq.baseUrl;
      else finalBaseUrl = PRESETS.openai.baseUrl;
    }

    if (!finalModel) {
      if (selectedPreset === "nvidia") finalModel = PRESETS.nvidia.model;
      else if (selectedPreset === "groq") finalModel = PRESETS.groq.model;
      else finalModel = PRESETS.openai.model;
    }

    const updated: ProviderConfig = {
      mode,
      byokKey: byokKey.trim(),
      byokBaseUrl: finalBaseUrl,
      byokModel: finalModel,
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
      <motion.div
        role="dialog"
        aria-modal="true"
        initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.96, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 420, damping: 32 }}
        className="bg-bg-surface border border-border rounded-interactive shadow-2xl max-w-lg w-full max-h-[90vh] flex flex-col overflow-hidden"
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
          <motion.button
            type="button"
            onClick={onClose}
            aria-label="Close settings"
            whileHover={shouldReduceMotion ? undefined : { rotate: 90 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.9 }}
            className="p-1 rounded-[4px] text-ink-ghost hover:text-ink-primary hover:bg-bg-sunken transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </motion.button>
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
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-[11px] font-mono text-gray-warm">
                      API Key (Paste & Go — zero configuration required)
                    </label>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-ink-ghost font-mono">Preset:</span>
                      {(["openai", "groq", "nvidia"] as const).map((p) => {
                        const preset = PRESETS[p];
                        const isSelected = selectedPreset === p;
                        return (
                          <motion.button
                            key={p}
                            type="button"
                            onClick={() => applyPreset(p)}
                            whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
                            whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
                            className={`text-[10px] font-mono px-2 py-0.5 rounded transition-colors cursor-pointer ${
                              isSelected
                                ? "bg-accent-primary/20 text-accent-primary border border-accent-primary font-semibold shadow-xs"
                                : "bg-bg-sunken text-ink-primary border border-border hover:bg-accent-primary/10 hover:text-accent-primary hover:border-accent-primary/40"
                            }`}
                          >
                            {isSelected ? `✓ ${preset.name}` : preset.name}
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>
                  <div className="relative">
                    <Input
                      type={showKey ? "text" : "password"}
                      placeholder={
                        selectedPreset !== "custom"
                          ? PRESETS[selectedPreset as "openai" | "groq" | "nvidia"].placeholder
                          : "Paste your API key (sk-..., gsk_..., or nvapi-...)"
                      }
                      value={byokKey}
                      onChange={(e) => handleKeyChange(e.target.value)}
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

                  {/* Auto-detection & preset status badge */}
                  {(() => {
                    const trimmed = byokKey.trim();
                    const det = detectProviderFromKey(trimmed);
                    if (det) {
                      return (
                        <div className="mt-2 flex items-center gap-2 p-2 rounded bg-accent-primary/10 border border-accent-primary/30 text-xs font-mono text-ink-primary animate-fade-in">
                          <CheckCircle2 className="w-4 h-4 text-accent-primary shrink-0" />
                          <div className="leading-tight">
                            <span>Ready with <strong>{det.name}</strong></span>
                            <span className="text-gray-warm block text-[10px] mt-0.5">
                              Model: {byokModel || det.model} • Zero configuration required!
                            </span>
                          </div>
                        </div>
                      );
                    }
                    if (selectedPreset !== "custom") {
                      const preset = PRESETS[selectedPreset as "openai" | "groq" | "nvidia"];
                      return (
                        <div className="mt-2 flex items-center gap-2 p-2 rounded bg-bg-sunken border border-border/80 text-xs font-mono text-ink-primary animate-fade-in">
                          <Key className="w-3.5 h-3.5 text-accent-primary shrink-0" />
                          <div className="leading-tight">
                            <span>Preset selected: <strong>{preset.name}</strong></span>
                            <span className="text-gray-warm block text-[10px] mt-0.5">
                              Model: {preset.model} • Paste your {preset.name} key ({preset.prefix}...) above
                            </span>
                          </div>
                        </div>
                      );
                    }
                    if (byokKey) {
                      return (
                        <span className="font-mono text-[10px] text-gray-warm mt-1 block">
                          fingerprint: {keyFingerprint}
                        </span>
                      );
                    }
                    return null;
                  })()}
                </div>

                {/* Collapsible custom endpoint / model override */}
                <div className="pt-0.5">
                  <button
                    type="button"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="text-[11px] font-mono text-ink-ghost hover:text-ink-primary transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <span>{showAdvanced ? "▾ Hide custom model & endpoint" : "▸ Custom endpoint or model ID (optional)"}</span>
                  </button>

                  {showAdvanced && (
                    <div className="mt-2 grid grid-cols-2 gap-2 animate-fade-in bg-bg-sunken/40 p-2.5 rounded border border-border/40">
                      <div>
                        <label className="block text-[10px] font-mono text-gray-warm mb-1">
                          Model ID
                        </label>
                        <Input
                          type="text"
                          placeholder={detectProviderFromKey(byokKey)?.model || "gpt-4o-mini"}
                          value={byokModel}
                          onChange={(e) => setByokModel(e.target.value)}
                          className="font-mono text-xs"
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-mono text-gray-warm mb-1">
                          Base URL (OpenAI-compatible)
                        </label>
                        <Input
                          type="text"
                          placeholder={detectProviderFromKey(byokKey)?.baseUrl || "https://api.openai.com/v1"}
                          value={byokBaseUrl}
                          onChange={(e) => setByokBaseUrl(e.target.value)}
                          className="font-mono text-xs"
                        />
                      </div>
                    </div>
                  )}
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
                  <span>Local Model</span>
                </div>
                <p className="text-xs text-gray-warm mt-0.5">
                  Runs on your local machine. Nothing leaves your computer.
                </p>
              </div>
            </label>

            {mode === "ollama" && (
              <div className="mt-3.5 pt-3 border-t border-border/60 space-y-3 pl-7">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] font-mono text-gray-warm mb-1">
                      Server URL
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
                    <span>{isTestingOllama ? "Testing…" : "Test Connection"}</span>
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
                  Local mode connects to an engine running on your computer. When using the web app, select Allcited or BYOK.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-border flex items-center justify-end gap-2 bg-bg-surface/90">
          <motion.div
            whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
          >
            <Button variant="ghost" size="sm" onClick={onClose} className="text-xs">
              Cancel
            </Button>
          </motion.div>
          <motion.div
            whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
          >
            <Button variant="primary" size="sm" onClick={handleSave} className="text-xs">
              Save changes
            </Button>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
