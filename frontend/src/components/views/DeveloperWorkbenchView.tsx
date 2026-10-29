"use client";

import React, { useState } from "react";
import {
  Code,
  GitBranch,
  Radio,
  FileCode,
  Layers,
  Database,
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
    <div className="w-full h-full flex flex-col apple-glass-canvas text-[#151619] overflow-hidden">
      {/* Dev Navigation Sub-bar (Apple Monochrome Glass) */}
      <div className="h-11 min-h-[44px] px-6 border-b border-[#E9EBEF] bg-white/70 backdrop-blur-md flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setDevTab("spec")}
            className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-all ${
              devTab === "spec"
                ? "bg-[#151619] text-white shadow-xs"
                : "text-[#737B8B] hover:text-[#151619] hover:bg-[#F7F8FA]"
            }`}
          >
            <Code className="w-3.5 h-3.5" />
            <span>01. Compiler</span>
          </button>

          <button
            onClick={() => setDevTab("flow")}
            className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-all ${
              devTab === "flow"
                ? "bg-[#151619] text-white shadow-xs"
                : "text-[#737B8B] hover:text-[#151619] hover:bg-[#F7F8FA]"
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>02. State Machine</span>
          </button>

          <button
            onClick={() => setDevTab("whisper")}
            className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-all ${
              devTab === "whisper"
                ? "bg-[#151619] text-white shadow-xs"
                : "text-[#737B8B] hover:text-[#151619] hover:bg-[#F7F8FA]"
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>03. Whisper Gate & SLA</span>
          </button>

          <button
            onClick={() => setDevTab("ledger")}
            className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium transition-all ${
              devTab === "ledger"
                ? "bg-[#151619] text-white shadow-xs"
                : "text-[#737B8B] hover:text-[#151619] hover:bg-[#F7F8FA]"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>04. SQLite Ledger</span>
          </button>
        </div>

        {/* Telegram Pairing Button */}
        <button
          onClick={() => setShowPairingModal(true)}
          className="btn-apple-secondary px-3 py-1 text-xs flex items-center space-x-1.5"
        >
          <Smartphone className="w-3.5 h-3.5 text-[#151619]" />
          <span>Pair Telegram Bot</span>
        </button>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 w-full overflow-hidden flex">
        {devTab === "spec" && (
          <div className="w-full h-full flex">
            <div className="w-full max-w-[400px] h-full border-r border-[#E9EBEF] bg-white/50">
              <AgentSpecPane
                domains={domains}
                activeDomain={activeDomain}
                onSelectDomain={onSelectDomain}
                onDomainUpdated={onDomainUpdated}
              />
            </div>
            <div className="flex-1 h-full overflow-y-auto p-6 bg-[#F7F8FA]/50">
              <div className="max-w-4xl mx-auto space-y-4">
                {/* Dynamic Pydantic Literal Validation Schema */}
                <div className="p-5 rounded-2xl apple-glass-card space-y-2">
                  <h3 className="text-sm font-semibold text-[#151619] flex items-center space-x-2">
                    <FileCode className="w-4 h-4 text-[#151619]" />
                    <span>Dynamic Pydantic Literal Validation Schema</span>
                  </h3>
                  <p className="text-xs text-[#737B8B]">
                    Generated dynamically from the compiled catalog. Every spoken turn must resolve to these literal enum types.
                  </p>
                  <pre className="mt-2 p-4 rounded-xl bg-white border border-[#E9EBEF] text-xs font-mono text-[#151619] overflow-x-auto leading-relaxed shadow-xs">
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
                <div className="p-5 rounded-2xl apple-glass-card space-y-2">
                  <h3 className="text-sm font-semibold text-[#151619] flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-[#151619]" />
                    <span>Compiled Strict Policies & Guardrail Invariants</span>
                  </h3>
                  <div className="mt-2 space-y-1.5">
                    {activeDomain?.strict_policies?.map((pol, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-white border border-[#E9EBEF] flex items-center justify-between text-xs shadow-xs"
                      >
                        <span className="text-[#151619] font-medium">{pol.rule}</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-[#F7F8FA] border border-[#E9EBEF] text-[#34373D]">
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
            <div className="w-[460px] h-full border-r border-[#E9EBEF]">
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
