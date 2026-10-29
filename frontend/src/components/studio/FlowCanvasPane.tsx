"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Radio,
  FileCode,
  CheckCircle,
  AlertTriangle,
  Copy,
  Check,
  GitBranch,
  Sparkles,
} from "lucide-react";
import { DomainProfile } from "@/lib/api";
import { LiveVoiceTestDock, NodeStateTelemetry } from "./LiveVoiceTestDock";

interface FlowCanvasPaneProps {
  activeDomain: DomainProfile | null;
}

export const FlowCanvasPane: React.FC<FlowCanvasPaneProps> = ({
  activeDomain,
}) => {
  const [nodeTelemetry, setNodeTelemetry] = useState<NodeStateTelemetry>({
    activeNode: 1,
    nodeSubState: "IDLE",
  });
  const [copiedEnum, setCopiedEnum] = useState(false);

  // Listen to WebSocket telemetry for live tool execution illumination
  useEffect(() => {
    const wsUrl = "ws://127.0.0.1:8000/ws/telemetry";
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "GUARDRAIL_EVALUATED") {
            const isPass = data.match_type === "DETERMINISTIC_PASS";
            setNodeTelemetry({
              activeNode: 3,
              nodeSubState: "DECISION_GATE",
              spokenEntity: data.spoken_entity,
              guardrailScore: data.score,
              guardrailBranch: isPass ? "PASS" : "HOLD",
            });
          } else if (data.type === "ACTION_COMMITTED") {
            setNodeTelemetry({
              activeNode: 3,
              nodeSubState: "IDLE",
              guardrailBranch: "PASS",
              spokenEntity: data.entry?.action,
            });
          }
        } catch {}
      };
    } catch {}
    return () => {
      if (ws) ws.close();
    };
  }, []);

  const copyPydanticEnum = () => {
    const enumSnippet = `from typing import Literal\n\n${
      activeDomain?.name.replace(/\s+/g, "") || "Domain"
    }Item = Literal[\n${(activeDomain?.catalog_items || [])
      .map((i) => `    "${i.canonical_name}"`)
      .join(",\n")}\n]`;
    navigator.clipboard.writeText(enumSnippet);
    setCopiedEnum(true);
    setTimeout(() => setCopiedEnum(false), 2000);
  };

  const isNode1Active = nodeTelemetry.activeNode === 1;
  const isNode2Active = nodeTelemetry.activeNode === 2;
  const isNode3Active = nodeTelemetry.activeNode === 3;

  return (
    <div className="flex-1 h-full flex flex-col justify-between overflow-hidden bg-[#09090b]">
      {/* Radial Dotted Grid Canvas */}
      <div className="flex-1 radial-dot-canvas overflow-y-auto p-6 flex flex-col items-center justify-start space-y-6 select-none">
        {/* Canvas Header Pill */}
        <div className="flex items-center space-x-2 px-3 py-1 bg-[#101013]/90 border border-[#1f1f24] rounded-full text-xs font-mono backdrop-blur-sm">
          <GitBranch className="w-3.5 h-3.5 text-[#10b981]" />
          <span className="text-[#9494a0]">Deterministic Pipeline Architecture:</span>
          <span className="text-[#f4f4f6] font-semibold">
            {activeDomain?.name || "Active Domain"}
          </span>
        </div>

        {/* Node 01: Inbound Greeting & AI Disclosure */}
        <div
          onClick={() => setNodeTelemetry({ activeNode: 1, nodeSubState: "IDLE" })}
          className={`w-full max-w-[620px] rounded-[6px] border transition-all cursor-pointer ${
            isNode1Active
              ? "bg-[#101013] border-[#10b981] shadow-lg shadow-[#10b981]/10 ring-1 ring-[#10b981]/30"
              : "bg-[#101013]/80 border-[#1f1f24] hover:border-[#2c2c35]"
          }`}
        >
          <div className="px-4 py-2.5 border-b border-[#1f1f24] flex items-center justify-between">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span
                className={`px-1.5 py-0.5 rounded-[3px] border font-semibold text-[10px] ${
                  isNode1Active
                    ? "bg-[#10b981]/20 border-[#10b981] text-[#10b981]"
                    : "bg-[#16161a] border-[#2c2c35] text-[#9494a0]"
                }`}
              >
                NODE 01
              </span>
              <span className="font-semibold text-[#f4f4f6]">
                Inbound Greeting & AI Disclosure
              </span>
            </div>
            <div className="flex items-center space-x-2 font-mono text-[10px]">
              {nodeTelemetry.nodeSubState === "SPEAKING_GREETING" ? (
                <span className="px-2 py-0.5 rounded-[3px] bg-[#10b981]/20 border border-[#10b981] text-[#10b981] font-semibold animate-pulse">
                  SPEAKING GREETING
                </span>
              ) : (
                <span className="text-[#9494a0]">420ms Barge-In Locked</span>
              )}
            </div>
          </div>

          <div className="p-4 space-y-2">
            <div className="text-[11px] font-mono text-[#5b5b66] uppercase">
              Spoken First Message (&lt;10 words):
            </div>
            <div className="text-sm font-medium text-[#f4f4f6] bg-[#09090b] border border-[#1f1f24] rounded-[4px] p-2.5 font-sans leading-relaxed">
              "{activeDomain?.first_message || "Namaste! How may I assist you today?"}"
            </div>
            <div className="flex items-center justify-between text-[11px] font-mono text-[#9494a0] pt-1">
              <span>Dialect: Hinglish / Indian English</span>
              <span className="text-[#10b981]">Flash v2.5 Synthesizer</span>
            </div>
          </div>
        </div>

        {/* Down Connector */}
        <div className="flex flex-col items-center">
          <div
            className={`w-[1px] h-6 transition-colors ${
              isNode2Active ? "bg-[#10b981]" : "bg-[#2c2c35]"
            }`}
          />
          <div
            className={`w-1.5 h-1.5 rounded-full transition-colors ${
              isNode2Active ? "bg-[#10b981] animate-ping" : "bg-[#5b5b66]"
            }`}
          />
        </div>

        {/* Node 02: Phonetic-Pydantic Catalog Validator */}
        <div
          onClick={() => setNodeTelemetry({ activeNode: 2, nodeSubState: "IDLE" })}
          className={`w-full max-w-[620px] rounded-[6px] border transition-all cursor-pointer ${
            isNode2Active
              ? "bg-[#101013] border-[#10b981] shadow-lg shadow-[#10b981]/15 ring-1 ring-[#10b981]/40"
              : "bg-[#101013]/80 border-[#1f1f24] hover:border-[#2c2c35]"
          }`}
        >
          <div className="px-4 py-2.5 border-b border-[#1f1f24] flex items-center justify-between">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span
                className={`px-1.5 py-0.5 rounded-[3px] border font-semibold text-[10px] ${
                  isNode2Active
                    ? "bg-[#10b981]/20 border-[#10b981] text-[#10b981]"
                    : "bg-[#16161a] border-[#2c2c35] text-[#9494a0]"
                }`}
              >
                NODE 02
              </span>
              <span className="font-semibold text-[#f4f4f6]">
                Phonetic-Pydantic Catalog Validator
              </span>
            </div>

            <div className="flex items-center space-x-2">
              {nodeTelemetry.nodeSubState === "VALIDATING" && (
                <span className="px-2 py-0.5 rounded-[3px] bg-[#10b981]/20 border border-[#10b981] text-[#10b981] font-mono text-[10px] font-semibold animate-pulse">
                  VALIDATING: "{nodeTelemetry.spokenEntity}"
                </span>
              )}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  copyPydanticEnum();
                }}
                className="flex items-center space-x-1 px-2 py-0.5 rounded-[3px] bg-[#16161a] border border-[#1f1f24] hover:border-[#2c2c35] text-[#9494a0] hover:text-[#f4f4f6] font-mono text-[10px] transition-all"
              >
                {copiedEnum ? (
                  <>
                    <Check className="w-2.5 h-2.5 text-[#10b981]" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-2.5 h-2.5" />
                    <span>Copy Enum</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="p-4 space-y-2.5">
            <div className="flex items-center justify-between text-[11px] font-mono text-[#5b5b66]">
              <span>Pydantic v2 Dynamic Literal Lock</span>
              <span className="text-[#10b981]">
                {activeDomain?.catalog_items.length || 0} Entities Indexed
              </span>
            </div>

            {/* Code Block for Dynamic Literal Enum */}
            <div className="bg-[#09090b] border border-[#1f1f24] rounded-[4px] p-2.5 font-mono text-[11px] text-[#9494a0] max-h-36 overflow-y-auto leading-relaxed">
              <div className="text-[#5b5b66]"># Tool: verify_catalog_item(spoken_entity)</div>
              <div>
                <span className="text-[#e4e4e7]">CatalogEntity</span> ={" "}
                <span className="text-[#10b981]">Literal</span>[
              </div>
              {(activeDomain?.catalog_items || []).slice(0, 5).map((item, idx) => (
                <div key={item.id} className="pl-4 text-[#f4f4f6]">
                  "{item.canonical_name}"
                  {idx < (activeDomain?.catalog_items.length || 0) - 1 ? "," : ""}
                  <span className="text-[#5b5b66] ml-2 font-sans">
                    — ₹{item.price_inr}
                  </span>
                </div>
              ))}
              {(activeDomain?.catalog_items.length || 0) > 5 && (
                <div className="pl-4 text-[#5b5b66]">
                  ... +{(activeDomain?.catalog_items.length || 0) - 5} more canonical items
                </div>
              )}
              <div>]</div>
            </div>

            <div className="flex items-center justify-between text-[10px] font-mono text-[#9494a0] bg-[#16161a] p-2 rounded-[3px] border border-[#1f1f24]">
              <span>S = 0.60·S_lex + 0.40·S_phon</span>
              <span className="text-[#e4e4e7]">RapidFuzz + Jellyfish Metaphone</span>
            </div>
          </div>
        </div>

        {/* Down Connector */}
        <div className="flex flex-col items-center">
          <div
            className={`w-[1px] h-6 transition-colors ${
              isNode3Active ? "bg-[#10b981]" : "bg-[#2c2c35]"
            }`}
          />
          <div
            className={`w-1.5 h-1.5 rounded-full transition-colors ${
              isNode3Active ? "bg-[#10b981] animate-ping" : "bg-[#5b5b66]"
            }`}
          />
        </div>

        {/* Node 03: Confidence Branching Gate */}
        <div
          onClick={() => setNodeTelemetry({ activeNode: 3, nodeSubState: "IDLE" })}
          className={`w-full max-w-[620px] rounded-[6px] border transition-all cursor-pointer ${
            isNode3Active
              ? "bg-[#101013] border-[#10b981] shadow-lg shadow-[#10b981]/15 ring-1 ring-[#10b981]/40"
              : "bg-[#101013]/80 border-[#1f1f24] hover:border-[#2c2c35]"
          }`}
        >
          <div className="px-4 py-2.5 border-b border-[#1f1f24] flex items-center justify-between">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span
                className={`px-1.5 py-0.5 rounded-[3px] border font-semibold text-[10px] ${
                  isNode3Active
                    ? "bg-[#10b981]/20 border-[#10b981] text-[#10b981]"
                    : "bg-[#16161a] border-[#2c2c35] text-[#9494a0]"
                }`}
              >
                NODE 03
              </span>
              <span className="font-semibold text-[#f4f4f6]">
                Confidence Branching Gate
              </span>
            </div>

            <span className="font-mono text-[10px] text-[#5b5b66]">
              Threshold: 0.85
            </span>
          </div>

          <div className="p-4 grid grid-cols-2 gap-3">
            {/* Branch A: Score >= 0.85 (Pass) */}
            <div
              className={`p-3 rounded-[4px] border space-y-1.5 font-mono transition-all ${
                nodeTelemetry.guardrailBranch === "PASS"
                  ? "bg-[#10b981]/20 border-[#10b981] shadow-md shadow-[#10b981]/20 ring-1 ring-[#10b981]"
                  : "bg-[#10b981]/5 border-[#10b981]/30"
              }`}
            >
              <div className="flex items-center space-x-1.5 text-xs text-[#10b981] font-semibold">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>SCORE &ge; 0.85</span>
                {nodeTelemetry.guardrailBranch === "PASS" && (
                  <span className="ml-auto text-[10px] bg-[#10b981] text-black px-1.5 py-0.2 rounded font-bold">
                    ACTIVE
                  </span>
                )}
              </div>
              <div className="text-[11px] text-[#f4f4f6] font-medium font-sans">
                Deterministic Read-Back
              </div>
              <p className="text-[10px] text-[#9494a0] font-sans leading-tight">
                Mandatory price read-back invoked. Locks order into operations ledger upon caller confirmation.
              </p>
            </div>

            {/* Branch B: Score < 0.85 (Hold) */}
            <div
              className={`p-3 rounded-[4px] border space-y-1.5 font-mono transition-all ${
                nodeTelemetry.guardrailBranch === "HOLD"
                  ? "bg-[#f59e0b]/20 border-[#f59e0b] shadow-md shadow-[#f59e0b]/20 ring-1 ring-[#f59e0b]"
                  : "bg-[#f59e0b]/5 border-[#f59e0b]/30"
              }`}
            >
              <div className="flex items-center space-x-1.5 text-xs text-[#f59e0b] font-semibold">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>SCORE &lt; 0.85</span>
                {nodeTelemetry.guardrailBranch === "HOLD" && (
                  <span className="ml-auto text-[10px] bg-[#f59e0b] text-black px-1.5 py-0.2 rounded font-bold animate-pulse">
                    HOLD
                  </span>
                )}
              </div>
              <div className="text-[11px] text-[#f4f4f6] font-medium font-sans">
                Whisper Intercept Hold
              </div>
              <p className="text-[10px] text-[#9494a0] font-sans leading-tight">
                Blocks DB write. Dispatches instant Telegram/PWA push to owner with 8.0s SLA fallback.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Live Browser Test Bar */}
      <LiveVoiceTestDock
        activeDomain={activeDomain}
        onNodeStateChange={setNodeTelemetry}
      />
    </div>
  );
};
