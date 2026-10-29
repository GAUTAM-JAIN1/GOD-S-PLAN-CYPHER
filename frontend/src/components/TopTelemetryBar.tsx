"use client";

import React from "react";
import { Terminal, LayoutGrid, Radio, Plus, Cpu } from "lucide-react";

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
    <header className="h-[60px] min-h-[60px] w-full px-7 flex items-center justify-between z-50 select-none apple-glass-surface border-b border-[#E9EBEF]/80">
      {/* Left: Brand + Breadcrumb */}
      <div className="flex items-center space-x-3.5">
        <div className="flex items-center space-x-2.5">
          {/* Monochrome Minimalist Logo Mark */}
          <div className="w-7 h-7 rounded-lg bg-[#151619] flex items-center justify-center text-white shadow-xs">
            <svg
              className="w-3.5 h-3.5 fill-white"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span className="text-[14px] font-semibold tracking-tight text-[#151619]">
            Voxera
          </span>
          <span className="text-[#B8BEC7] text-xs">/</span>
          <span className="text-xs font-medium text-[#34373D] bg-[#F7F8FA] px-2.5 py-0.5 rounded-full border border-[#E9EBEF]">
            {activeDomainSlug || "brew-bite-cafe"}
          </span>
        </div>

        <div className="h-3.5 w-[1px] bg-[#E9EBEF]" />

        {/* Monochrome Live Status Pill */}
        <div className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#F7F8FA] border border-[#E9EBEF]">
          <span className="w-1.5 h-1.5 rounded-full mono-live-dot" />
          <span className="text-[11px] font-medium text-[#34373D]">
            Live
          </span>
        </div>
      </div>

      {/* Center: The 2 Core Tabs (Voice Agent Studio vs Developer Inspector) */}
      <div className="flex items-center p-1 bg-[#F7F8FA] border border-[#E9EBEF] rounded-full shadow-xs">
        <button
          id="btn-nav-main"
          onClick={() => setActiveTab("main")}
          className={`flex items-center space-x-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
            activeTab === "main"
              ? "bg-[#151619] text-white shadow-xs"
              : "text-[#737B8B] hover:text-[#151619] hover:bg-white/80"
          }`}
        >
          <LayoutGrid className="w-3.5 h-3.5" />
          <span>Voice Agent Studio</span>
        </button>

        <button
          id="btn-nav-dev"
          onClick={() => setActiveTab("dev")}
          className={`relative flex items-center space-x-2 px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
            activeTab === "dev"
              ? "bg-[#151619] text-white shadow-xs"
              : "text-[#737B8B] hover:text-[#151619] hover:bg-white/80"
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>Developer Inspector</span>
          {activeHoldCount > 0 && (
            <span className="ml-1 px-1.5 py-0.2 bg-[#34373D] text-white rounded-full text-[10px] font-semibold">
              {activeHoldCount}
            </span>
          )}
        </button>
      </div>

      {/* Right: Live Telemetry & CTA */}
      <div className="flex items-center space-x-2.5 text-xs">
        {/* ConvAI Pill */}
        <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white border border-[#E9EBEF] shadow-xs text-[#737B8B]">
          <Radio className={`w-3 h-3 ${wsConnected ? "text-[#151619]" : "text-[#B8BEC7]"}`} />
          <span className="text-[11px] font-medium">ConvAI:</span>
          <span className="text-[11px] font-semibold text-[#151619]">
            {wsConnected ? "Connected" : "Ready"}
          </span>
        </div>

        {/* Latency Pill */}
        <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white border border-[#E9EBEF] shadow-xs text-[#737B8B] font-mono text-[11px]">
          <Cpu className="w-3 h-3 text-[#34373D]" />
          <span className="text-[11px] font-medium text-[#737B8B]">Groq:</span>
          <span className="text-[11px] font-semibold text-[#151619]">{liveTtsLatencyMs}ms</span>
        </div>

        {/* + Create Agent Action Button */}
        <button
          onClick={onCreateAgentClick}
          className="btn-apple-primary px-3.5 py-1.5 text-xs flex items-center space-x-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Create Agent</span>
        </button>
      </div>
    </header>
  );
};
