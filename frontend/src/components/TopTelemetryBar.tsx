"use client";

import React from "react";
import { Terminal, LayoutGrid, Radio, Plus, Sparkles, ShieldCheck } from "lucide-react";

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
    <header className="w-full px-6 py-3 flex items-center justify-between z-50 select-none apple-glass-surface border-b border-[#E9EBEF]/80 sticky top-0">
      {/* Left: Brand Logo Mark matching screenshot */}
      <div className="flex items-center space-x-3">
        <div
          className="flex items-center space-x-2.5 cursor-pointer"
          onClick={() => setActiveTab("main")}
        >
          {/* Custom Voxera Fluid Glass Wing Mark */}
          <div className="w-7 h-7 rounded-lg bg-[#151619] flex items-center justify-center text-white shadow-xs">
            <svg
              className="w-3.5 h-3.5 fill-white"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M3.5 6.5C5.5 10 8 14.5 12 18.5C16 14.5 18.5 10 20.5 6.5C18.5 7.5 15.5 8.5 12 8.5C8.5 8.5 5.5 7.5 3.5 6.5Z" />
            </svg>
          </div>
          <span className="text-[16px] font-bold tracking-tight text-[#151619]">
            Voxera
          </span>
        </div>

        {/* Live Status Indicator */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#F7F8FA] border border-[#E9EBEF]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#151619] mono-live-dot" />
          <span className="text-[11px] font-medium text-[#34373D]">
            {activeDomainSlug || "brew-bite-cafe"}
          </span>
        </div>
      </div>

      {/* Center: Landing Nav Links (Product, Solutions, Pricing, Docs, Enterprise) */}
      <nav className="hidden lg:flex items-center space-x-7 text-xs font-medium text-[#737B8B]">
        <button
          onClick={() => setActiveTab("main")}
          className="hover:text-[#151619] transition-colors"
        >
          Product
        </button>
        <button
          onClick={() => {
            setActiveTab("main");
            const el = document.getElementById("voxera-dashboard");
            el?.scrollIntoView({ behavior: "smooth" });
          }}
          className="hover:text-[#151619] transition-colors"
        >
          Solutions
        </button>
        <button
          onClick={() => alert("Voxera Enterprise: Custom SLA, Dedicated SIP trunks & On-prem Guardrail runtime.")}
          className="hover:text-[#151619] transition-colors"
        >
          Pricing
        </button>
        <button
          onClick={() => window.open("http://localhost:8000/docs", "_blank")}
          className="hover:text-[#151619] transition-colors"
        >
          Docs
        </button>
        <button
          onClick={() => alert("Voxera Enterprise PSTN: Twilio SIP Trunking + 99.99% Uptime SLA.")}
          className="hover:text-[#151619] transition-colors"
        >
          Enterprise
        </button>
      </nav>

      {/* Right: Switcher between Voice Studio & Developer Inspector + CTAs */}
      <div className="flex items-center space-x-3">
        {/* The 2 Core Tabs Switcher */}
        <div className="flex items-center p-0.5 bg-[#F7F8FA] border border-[#E9EBEF] rounded-full shadow-xs">
          <button
            id="btn-nav-main"
            onClick={() => setActiveTab("main")}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
              activeTab === "main"
                ? "bg-[#151619] text-white shadow-xs"
                : "text-[#737B8B] hover:text-[#151619]"
            }`}
          >
            <LayoutGrid className="w-3 h-3" />
            <span className="hidden sm:inline">Studio</span>
          </button>

          <button
            id="btn-nav-dev"
            onClick={() => setActiveTab("dev")}
            className={`relative flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
              activeTab === "dev"
                ? "bg-[#151619] text-white shadow-xs"
                : "text-[#737B8B] hover:text-[#151619]"
            }`}
          >
            <Terminal className="w-3 h-3" />
            <span className="hidden sm:inline">Developer</span>
            {activeHoldCount > 0 && (
              <span className="px-1.5 py-0.2 bg-[#34373D] text-white rounded-full text-[10px] font-semibold">
                {activeHoldCount}
              </span>
            )}
          </button>
        </div>

        {/* Sign in / Get Started */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => alert("Workspace: GAUTAM-JAIN1 (Administrator)")}
            className="text-xs font-medium text-[#34373D] hover:text-[#151619] px-2.5 py-1.5 transition-colors hidden sm:block"
          >
            Sign in
          </button>

          <button
            onClick={onCreateAgentClick}
            className="btn-apple-primary px-3.5 py-1.5 text-xs flex items-center space-x-1.5"
          >
            <span>Get Started</span>
            <span className="text-xs">→</span>
          </button>
        </div>
      </div>
    </header>
  );
};
