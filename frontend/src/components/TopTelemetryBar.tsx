"use client";

import React from "react";
import { Activity, Cpu, Radio, Sparkles, LayoutGrid, Terminal } from "lucide-react";

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
}) => {
  return (
    <header className="h-[52px] min-h-[52px] w-full bg-[#0d0d12] border-b border-[#1f1f28] px-6 flex items-center justify-between z-50 select-none">
      {/* Left: Brand + Breadcrumb */}
      <div className="flex items-center space-x-3.5">
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 bg-gradient-to-tr from-[#10b981] to-[#059669] rounded-lg flex items-center justify-center font-mono text-xs font-black text-black tracking-tighter shadow-md shadow-[#10b981]/20">
            VF
          </div>
          <span className="text-sm font-bold tracking-tight text-white">
            Voxera Voice AI
          </span>
          <span className="text-[#5b5b66] text-xs">/</span>
          <span className="text-xs font-medium text-[#9494a0]">
            {activeDomainSlug || "brew-bite-cafe"}
          </span>
        </div>

        <div className="h-3.5 w-[1px] bg-[#22222c]" />

        <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#10b981]/10 border border-[#10b981]/20">
          <span className="w-1.5 h-1.5 rounded-full bg-[#10b981] animate-pulse" />
          <span className="font-mono text-[11px] text-[#10b981] font-semibold">
            live
          </span>
        </div>
      </div>

      {/* Center: 2 Clean Modes (Main Studio vs Developer Inspector) */}
      <div className="flex items-center p-1 bg-[#14141c] border border-[#22222e] rounded-xl">
        <button
          id="btn-nav-main"
          onClick={() => setActiveTab("main")}
          className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === "main"
              ? "bg-[#10b981] text-black shadow-lg shadow-[#10b981]/20"
              : "text-[#9494a0] hover:text-white"
          }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Voice Agent Studio</span>
        </button>

        <button
          id="btn-nav-dev"
          onClick={() => setActiveTab("dev")}
          className={`relative flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === "dev"
              ? "bg-[#38bdf8] text-black shadow-lg shadow-[#38bdf8]/20"
              : "text-[#9494a0] hover:text-white"
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Developer Inspector</span>
          {activeHoldCount > 0 && (
            <span className="ml-1 px-1.5 py-0.2 bg-[#ef4444] text-white rounded text-[10px] font-bold">
              {activeHoldCount}
            </span>
          )}
        </button>
      </div>

      {/* Right: Live Telemetry */}
      <div className="flex items-center space-x-3 text-xs font-mono">
        <div className="flex items-center space-x-1.5 text-[#9494a0] bg-[#14141c] px-3 py-1 rounded-lg border border-[#22222e]">
          <Radio className={`w-3.5 h-3.5 ${wsConnected ? "text-[#10b981] animate-pulse" : "text-[#5b5b66]"}`} />
          <span>ConvAI:</span>
          <span className={wsConnected ? "text-[#10b981] font-bold" : "text-[#5b5b66]"}>
            {wsConnected ? "Connected" : "Ready"}
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-[#9494a0] bg-[#14141c] px-3 py-1 rounded-lg border border-[#22222e]">
          <Cpu className="w-3.5 h-3.5 text-[#9494a0]" />
          <span>LLM:</span>
          <span className={groqReady ? "text-[#10b981] font-bold" : "text-[#f59e0b]"}>
            llama-3.3
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-[#9494a0] bg-[#14141c] px-3 py-1 rounded-lg border border-[#22222e]">
          <Activity className="w-3.5 h-3.5 text-[#10b981]" />
          <span>TTS:</span>
          <span className="text-white font-bold">
            {liveTtsLatencyMs > 0 ? `${liveTtsLatencyMs}ms` : "flash_v2"}
          </span>
        </div>
      </div>
    </header>
  );
};
