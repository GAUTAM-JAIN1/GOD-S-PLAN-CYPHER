"use client";

import React, { useState } from "react";
import {
  Code,
  GitBranch,
  Radio,
  FileCode,
  Layers,
  Database,
  Cpu,
  Sparkles,
  Smartphone
} from "lucide-react";
import { DomainProfile } from "@/lib/api";
import { AgentSpecPane } from "@/components/studio/AgentSpecPane";
import { FlowCanvasPane } from "@/components/studio/FlowCanvasPane";
import { LiveWhisperGatePane } from "@/components/ops/LiveWhisperGatePane";
import { VerifiedLedgerPane } from "@/components/ops/VerifiedLedgerPane";
import { MobilePairingModal } from "@/components/ops/MobilePairingModal";

interface DeveloperWorkbenchViewProps {
  domains: DomainProfile[];
  activeDomain: DomainProfile | null;
  onSelectDomain: (domain: DomainProfile) => void;
  onDomainUpdated: (domain: DomainProfile) => void;
}

export const DeveloperWorkbenchView: React.FC<DeveloperWorkbenchViewProps> = ({
  domains,
  activeDomain,
  onSelectDomain,
  onDomainUpdated,
}) => {
  const [devTab, setDevTab] = useState<"spec" | "flow" | "whisper" | "ledger">("spec");
  const [showPairingModal, setShowPairingModal] = useState<boolean>(false);

  return (
    <div className="w-full h-full flex flex-col bg-[#09090b] text-[#f4f4f6] overflow-hidden">
      {/* Dev Navigation Sub-bar */}
      <div className="h-11 min-h-[44px] px-6 border-b border-[#1f1f24] bg-[#0d0d10] flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setDevTab("spec")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              devTab === "spec"
                ? "bg-[#181820] text-[#f4f4f6] border border-[#2d2d38] shadow-sm"
                : "text-[#9494a0] hover:text-[#f4f4f6]"
            }`}
          >
            <Code className="w-3.5 h-3.5 text-[#38bdf8]" />
            <span>01. Prompt & Catalog Compiler</span>
          </button>

          <button
            onClick={() => setDevTab("flow")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              devTab === "flow"
                ? "bg-[#181820] text-[#f4f4f6] border border-[#2d2d38] shadow-sm"
                : "text-[#9494a0] hover:text-[#f4f4f6]"
            }`}
          >
            <GitBranch className="w-3.5 h-3.5 text-[#10b981]" />
            <span>02. Deterministic State Machine</span>
          </button>

          <button
            onClick={() => setDevTab("whisper")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              devTab === "whisper"
                ? "bg-[#181820] text-[#f4f4f6] border border-[#2d2d38] shadow-sm"
                : "text-[#9494a0] hover:text-[#f4f4f6]"
            }`}
          >
            <Radio className="w-3.5 h-3.5 text-[#f59e0b]" />
            <span>03. Live Whisper Gate & SLA</span>
          </button>

          <button
            onClick={() => setDevTab("ledger")}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              devTab === "ledger"
                ? "bg-[#181820] text-[#f4f4f6] border border-[#2d2d38] shadow-sm"
                : "text-[#9494a0] hover:text-[#f4f4f6]"
            }`}
          >
            <Database className="w-3.5 h-3.5 text-[#a78bfa]" />
            <span>04. SQLite Ledger & Cryptographic Token</span>
          </button>
        </div>

        {/* Telegram Pairing Button */}
        <button
          onClick={() => setShowPairingModal(true)}
          className="flex items-center space-x-1.5 px-3 py-1 rounded-md bg-[#16161e] border border-[#262635] hover:bg-[#1f1f2c] text-xs font-mono text-[#9494a0] hover:text-[#f4f4f6] transition-colors"
        >
          <Smartphone className="w-3.5 h-3.5 text-[#38bdf8]" />
          <span>Pair Telegram Bot</span>
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 w-full overflow-hidden flex">
        {devTab === "spec" && (
          <div className="w-full h-full flex">
            <div className="w-full max-w-[420px] h-full border-r border-[#1f1f24]">
              <AgentSpecPane
                domains={domains}
                activeDomain={activeDomain}
                onSelectDomain={onSelectDomain}
                onDomainUpdated={onDomainUpdated}
              />
            </div>
            <div className="flex-1 h-full overflow-y-auto p-6 bg-[#0c0c0e]">
              <div className="max-w-4xl mx-auto space-y-5">
                <div className="p-5 rounded-2xl bg-[#121217] border border-[#22222b]">
                  <h3 className="text-sm font-bold text-[#f4f4f6] flex items-center space-x-2">
                    <FileCode className="w-4 h-4 text-[#10b981]" />
                    <span>Dynamic Pydantic Literal Validation Schema</span>
                  </h3>
                  <p className="text-xs text-[#9494a0] mt-1">
                    Generated dynamically from the compiled catalog. Every spoken turn must resolve to these literal enum types.
                  </p>
                  <pre className="mt-3 p-4 rounded-xl bg-[#09090b] border border-[#1f1f26] text-xs font-mono text-[#34d399] overflow-x-auto leading-relaxed">
{`# Dynamically Compiled Pydantic Enum for ${activeDomain?.name || "Brew & Bite"}
from typing import Literal
from pydantic import BaseModel, Field

${activeDomain?.name?.replace(/[^a-zA-Z0-9]/g, "") || "Domain"}Item = Literal[
${activeDomain?.catalog_items?.map((i) => `    "${i.canonical_name}"`).join(",\n") || '    "Hazelnut Cold Brew"'}
]

class VerifiedActionModel(BaseModel):
    selected_entity: ${activeDomain?.name?.replace(/[^a-zA-Z0-9]/g, "") || "Domain"}Item
    quantity: int = Field(default=1, ge=1, le=50)
    modifiers: list[str] = Field(default_factory=list)
    unit_price_inr: float
    total_price_inr: float
    caller_phone: str`}
                  </pre>
                </div>

                {/* Strict Policies Box */}
                <div className="p-5 rounded-2xl bg-[#121217] border border-[#22222b]">
                  <h3 className="text-sm font-bold text-[#f4f4f6] flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-[#f59e0b]" />
                    <span>Compiled Strict Policies & Guardrail Invariants</span>
                  </h3>
                  <div className="mt-3 space-y-2">
                    {activeDomain?.strict_policies?.map((pol, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-[#16161e] border border-[#232330] flex items-center justify-between text-xs"
                      >
                        <span className="text-[#f4f4f6]">{pol.rule}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#ef4444]/20 text-[#ef4444]">
                          {pol.severity}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {devTab === "flow" && (
          <div className="w-full h-full">
            <FlowCanvasPane activeDomain={activeDomain} />
          </div>
        )}

        {devTab === "whisper" && (
          <div className="w-full h-full flex">
            <div className="w-[480px] h-full border-r border-[#1f1f24]">
              <LiveWhisperGatePane />
            </div>
            <div className="flex-1 h-full">
              <VerifiedLedgerPane />
            </div>
          </div>
        )}

        {devTab === "ledger" && (
          <div className="w-full h-full p-4 overflow-y-auto">
            <VerifiedLedgerPane />
          </div>
        )}
      </div>

      <MobilePairingModal
        isOpen={showPairingModal}
        onClose={() => setShowPairingModal(false)}
      />
    </div>
  );
};
