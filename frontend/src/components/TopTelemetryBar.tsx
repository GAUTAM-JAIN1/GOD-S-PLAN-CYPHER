"use client";

import React from "react";
import { Sparkles, Terminal, LayoutGrid, Radio, Plus, ShieldCheck, Cpu } from "lucide-react";

export type ViewTabMode = "main" | "dev";

interface TopTelemetryBarProps {
  activeTab: ViewTabMode;
  setActiveTab: (tab: ViewTabMode) => void;
  activeDomainSlug: string;
  activeHoldCount: number;
  wsConnected: boolean;
  groqReady: boolean;
  elevenlabsReady: boolean;
  liveTtsLatencyMs: number;
  onCreateAgentClick?: () => void;
}

export const TopTelemetryBar: React.FC<TopTelemetryBarProps> = ({
  activeTab,
  setActiveTab,
  activeDomainSlug,
  activeHoldCount,
  wsConnected,
  groqReady,
  elevenlabsReady,
  liveTtsLatencyMs,
  onCreateAgentClick,
}) => {
  return (
    <header className="h-[64px] min-h-[64px] w-full px-6 flex items-center justify-between z-50 select-none liquid-glass-panel border-b border-white/60">
      {/* Left: Brand + Breadcrumb */}
      <div className="flex items-center space-x-3.5">
        <div className="flex items-center space-x-2.5">
          {/* Logo mark */}
          <div className="w-8 h-8 rounded-xl bg-black flex items-center justify-center text-white shadow-md shadow-black/10">
            <svg
              className="w-4 h-4 fill-white"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="text-base font-bold tracking-tight text-neutral-900">
            Voxera
          </span>
          <span className="text-neutral-400 text-xs">/</span>
          <span className="text-xs font-semibold text-neutral-600 bg-neutral-100/80 px-2.5 py-1 rounded-full border border-neutral-200/60">
            {activeDomainSlug || "brew-bite-cafe"}
          </span>
        </div>

        <div className="h-4 w-[1px] bg-neutral-200" />

        {/* Live Status Pill */}
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-semibold text-emerald-700 tracking-tight">
            Live
          </span>
        </div>
      </div>

      {/* Center: The 2 Core Tabs (Voice Agent Studio vs Developer Inspector) */}
      <div className="flex items-center p-1 bg-neutral-100/80 backdrop-blur-md border border-neutral-200/70 rounded-full shadow-inner">
        <button
          id="btn-nav-main"
          onClick={() => setActiveTab("main")}
          className={`flex items-center space-x-2 px-5 py-2 rounded-full text-xs font-semibold transition-all duration-200 ${
            activeTab === "main"
              ? "bg-black text-white shadow-md shadow-black/15"
              : "text-neutral-600 hover:text-black hover:bg-white/60"
          }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Voice Agent Studio</span>
        </button>

        <button
          id="btn-nav-dev"
          onClick={() => setActiveTab("dev")}
          className={`relative flex items-center space-x-2 px-5 py-2 rounded-full text-xs font-semibold transition-all duration-200 ${
            activeTab === "dev"
              ? "bg-black text-white shadow-md shadow-black/15"
              : "text-neutral-600 hover:text-black hover:bg-white/60"
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Developer Inspector</span>
          {activeHoldCount > 0 && (
            <span className="ml-1.5 px-1.5 py-0.5 bg-rose-500 text-white rounded-full text-[10px] font-bold">
              {activeHoldCount}
            </span>
          )}
        </button>
      </div>

      {/* Right: Live Telemetry & CTA */}
      <div className="flex items-center space-x-3 text-xs">
        {/* ConvAI Pill */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-white/80 border border-neutral-200/80 shadow-sm text-neutral-600">
          <Radio className={`w-3.5 h-3.5 ${wsConnected ? "text-emerald-500 animate-pulse" : "text-neutral-400"}`} />
          <span className="font-medium text-neutral-500">ConvAI:</span>
          <span className={`font-semibold ${wsConnected ? "text-emerald-600" : "text-neutral-700"}`}>
            {wsConnected ? "Connected" : "Ready"}
          </span>
        </div>

        {/* Latency Pill */}
        <div className="hidden md:flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-white/80 border border-neutral-200/80 shadow-sm text-neutral-600 font-mono text-[11px]">
          <Cpu className="w-3.5 h-3.5 text-blue-500" />
          <span className="text-neutral-500">Groq:</span>
          <span className="font-semibold text-neutral-800">{liveTtsLatencyMs}ms</span>
        </div>

        {/* + Create Agent Action Button */}
        <button
          onClick={onCreateAgentClick}
          className="btn-pill-primary px-4 py-2 text-xs flex items-center space-x-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Create Agent</span>
        </button>
      </div>
    </header>
  );
};
