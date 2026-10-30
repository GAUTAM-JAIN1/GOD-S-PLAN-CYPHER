"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldAlert,
  Play,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Zap,
  Code2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  RefreshCw,
  Terminal,
  FileCheck2,
  Layers,
  Swords,
  Check,
  Volume2,
  Square,
  Sliders,
} from "lucide-react";
import {
  DomainProfile,
  GauntletRunResult,
  GauntletScenarioItem,
  runGauntlet,
  fetchLatestGauntlet,
  resetGauntletVulnerability,
  getWsBase,
  fetchDomain,
  synthesizeDuelAudio,
  refineDomainPolicy,
} from "@/lib/api";

interface GauntletPaneProps {
  activeDomain: DomainProfile | null;
  onDomainUpdated?: (updated: DomainProfile) => void;
}

const AVAILABLE_SUITES = [
  {
    id: "discount_escalation",
    number: 1,
    title: "The Relentless Bargainer & VIP Bully",
    turns: 4,
    badge: "Social Engineering",
    description: "3x discount begging + angry manager takeover alert.",
  },
  {
    id: "domain_flow_trap",
    number: 2,
    title: "Phonetic Barge-In, Off-Menu & PII Probe",
    turns: 4,
    badge: "Phonetics & Privacy",
    description: "Double-Metaphone booking, off-catalog trap, fake UTR & PII defense.",
  },
  {
    id: "off_topic_termination",
    number: 3,
    title: "Persistent Off-Topic Timepasser",
    turns: 2,
    badge: "2-Strike Auto Hangup",
    description: "Strike 1 redirect + Strike 2 terminate_call() disconnection.",
  },
  {
    id: "brutal_injection_flood",
    number: 4,
    title: "Brutal Prompt-Injection & Spammer",
    turns: 2,
    badge: "BrutalShield <10ms",
    description: "Developer debug jailbreaks & <10ms Pre-LLM kill switch.",
  },
];

export const GauntletPane: React.FC<GauntletPaneProps> = ({
  activeDomain,
  onDomainUpdated,
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [activeScenarioId, setActiveScenarioId] = useState<number | null>(null);
  const [gauntletData, setGauntletData] = useState<GauntletRunResult | null>(null);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);
  const [isResetting, setIsResetting] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [selectedSuiteIds, setSelectedSuiteIds] = useState<string[]>([
    "discount_escalation",
    "domain_flow_trap",
  ]);
  const [isAudioPlaying, setIsAudioPlaying] = useState<boolean>(false);
  const [activeAudioTurnIdx, setActiveAudioTurnIdx] = useState<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Toggle selection
  const toggleSuite = (id: string) => {
    setSelectedSuiteIds((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const stopDuelAudio = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsAudioPlaying(false);
    setActiveAudioTurnIdx(null);
  };

  const playDuelAudio = (transcript: Array<{ speaker: string; text: string }>) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window) || !transcript || transcript.length === 0) return;
    stopDuelAudio();
    window.speechSynthesis.resume();
    setIsAudioPlaying(true);

    const voices = window.speechSynthesis.getVoices();
    const indVoice = voices.find(
      (v) => v.lang.includes("IN") || v.lang.includes("hi") || v.name.includes("Google")
    ) || voices[0];

    let currentTurn = 0;
    const playNext = () => {
      if (currentTurn >= transcript.length) {
        setIsAudioPlaying(false);
        setActiveAudioTurnIdx(null);
        return;
      }
      const item = transcript[currentTurn];
      setActiveAudioTurnIdx(currentTurn);

      const isAttacker = item.speaker.toLowerCase().includes("attacker") || item.speaker.toLowerCase().includes("caller");
      const utt = new SpeechSynthesisUtterance(item.text);
      if (indVoice) utt.voice = indVoice;
      utt.rate = 1.15;
      utt.pitch = isAttacker ? 0.85 : 1.15;

      utt.onend = () => {
        currentTurn++;
        setTimeout(playNext, 200);
      };
      utt.onerror = () => {
        setIsAudioPlaying(false);
        setActiveAudioTurnIdx(null);
      };
      window.speechSynthesis.speak(utt);
    };
    playNext();
  };

  // Connect to live WebSocket telemetry
  useEffect(() => {
    const wsUrl = `${getWsBase()}/ws/telemetry`;
    let ws: WebSocket | null = null;

    try {
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "GAUNTLET_STARTED") {
            setIsRunning(true);
            setActiveScenarioId(1);
          } else if (data.type === "GAUNTLET_SCENARIO_RUNNING") {
            setActiveScenarioId(data.scenario_id);
          } else if (data.type === "GAUNTLET_SCENARIO_COMPLETED") {
            setGauntletData((prev) => {
              const updatedScenarios = prev?.scenarios ? [...prev.scenarios] : [];
              const idx = updatedScenarios.findIndex(
                (s) => s.scenario_id === data.scenario_id
              );
              if (idx >= 0) {
                updatedScenarios[idx] = data.scenario;
              } else {
                updatedScenarios.push(data.scenario);
              }
              return {
                success: true,
                run_id: data.run_id,
                domain_id: activeDomain?.id || "brew-bite-cafe",
                scenarios_passed: updatedScenarios.filter((s) => s.status !== "FAIL").length,
                auto_healed_count: updatedScenarios.filter((s) => s.status === "AUTO-PATCHED").length,
                mean_latency_ms: Math.round(
                  updatedScenarios.reduce((acc, s) => acc + s.latency_ms, 0) /
                    (updatedScenarios.length || 1)
                ),
                scenarios: updatedScenarios,
                created_at: new Date().toISOString(),
              };
            });
          } else if (data.type === "GAUNTLET_COMPLETED") {
            setIsRunning(false);
            setActiveScenarioId(null);
          } else if (data.type === "DOMAIN_UPDATED") {
            if (activeDomain && data.domain_id === activeDomain.id) {
              setToastMessage(data.badge || "+ Auto-Healed Policy Synced from Gauntlet");
              setTimeout(() => setToastMessage(null), 4000);
              fetchDomain(activeDomain.id).then((fresh) => {
                if (onDomainUpdated) onDomainUpdated(fresh);
              });
            }
          }
        } catch (e) {
          console.error("Gauntlet WS parse error:", e);
        }
      };
    } catch (err) {
      console.error("Gauntlet WS connect error:", err);
    }

    return () => {
      if (ws) ws.close();
    };
  }, [activeDomain?.id, onDomainUpdated]);

  const handleRunGauntlet = async () => {
    if (!activeDomain || isRunning || selectedSuiteIds.length === 0) return;
    setIsRunning(true);
    setActiveScenarioId(1);
    stopDuelAudio();
    try {
      const res = await runGauntlet(activeDomain.id, true, selectedSuiteIds);
      setGauntletData(res);
      const freshDomain = await fetchDomain(activeDomain.id);
      if (onDomainUpdated) onDomainUpdated(freshDomain);
    } catch (err: any) {
      alert(`Gauntlet execution failed: ${err.message}`);
    } finally {
      setIsRunning(false);
      setActiveScenarioId(null);
    }
  };

  const handleResetVulnerability = async () => {
    if (!activeDomain || isResetting) return;
    setIsResetting(true);
    stopDuelAudio();
    try {
      await resetGauntletVulnerability(activeDomain.id);
      setToastMessage("Vulnerability Demo Reset — Unhardened State");
      setTimeout(() => setToastMessage(null), 3500);
      const freshDomain = await fetchDomain(activeDomain.id);
      if (onDomainUpdated) onDomainUpdated(freshDomain);
      setGauntletData(null);
    } catch (err: any) {
      alert(`Reset failed: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  const scenariosToDisplay = gauntletData?.scenarios || [];

  return (
    <div className="w-[390px] min-w-[390px] h-full bg-[#101013] border-l border-[#1f1f24] flex flex-col justify-between select-none">
      <div className="flex-1 overflow-y-auto p-3.5 space-y-3">
        {/* Pane Header */}
        <div className="flex items-center justify-between pb-1 border-b border-[#1f1f24]">
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 rounded-[4px] bg-[#16161a] border border-[#2c2c35] flex items-center justify-center font-mono text-[10px] font-bold text-[#f59e0b]">
              G
            </div>
            <div>
              <h2 className="text-xs font-semibold text-[#f4f4f6] uppercase tracking-wider font-mono leading-none">
                Anti-Agent Gauntlet
              </h2>
              <span className="text-[10px] text-[#71717a] font-mono">
                Clean-Slate Multi-Select
              </span>
            </div>
          </div>
          <button
            onClick={handleResetVulnerability}
            disabled={isResetting || isRunning}
            title="Reset auto-patched policies"
            className="flex items-center space-x-1 px-2 py-1 rounded-[4px] bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] text-[10px] font-mono text-[#a1a1aa] hover:text-[#f4f4f6] transition-all disabled:opacity-40"
          >
            <RotateCcw className={`w-3 h-3 ${isResetting ? "animate-spin" : ""}`} />
            <span>Reset Demo</span>
          </button>
        </div>

        {/* Live Auto-Healed Toast Banner */}
        {toastMessage && (
          <div className="p-2 rounded-[4px] bg-[#10b981]/15 border border-[#10b981]/40 text-[#10b981] font-mono text-[11px] flex items-center space-x-2 animate-pulse shadow-lg">
            <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
            <span className="truncate">{toastMessage}</span>
          </div>
        )}

        {/* STAGE 1: CLEAN SLATE SUITE SELECTOR (When no battle run is active) */}
        {scenariosToDisplay.length === 0 && !isRunning && (
          <div className="space-y-3">
            <div className="p-2.5 rounded-[6px] bg-[#09090b] border border-[#1f1f24] space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold text-[#f4f4f6] uppercase">
                  Select Anti-Agents
                </span>
                <span className="text-[10px] font-mono text-[#10b981]">
                  {selectedSuiteIds.length} Selected
                </span>
              </div>
              <p className="text-[10px] text-[#71717a] font-mono">
                Choose adversarial attack vectors to run live against {activeDomain?.name}.
              </p>

              <div className="space-y-2 pt-1">
                {AVAILABLE_SUITES.map((s) => {
                  const isChecked = selectedSuiteIds.includes(s.id);
                  return (
                    <div
                      key={s.id}
                      onClick={() => toggleSuite(s.id)}
                      className={`cursor-pointer p-2 rounded-[4px] border transition-all text-xs flex items-start justify-between ${
                        isChecked
                          ? "bg-[#141418] border-[#10b981]/60 text-[#f4f4f6]"
                          : "bg-[#0c0c0f] border-[#1f1f24] text-[#71717a] hover:border-[#27272a]"
                      }`}
                    >
                      <div className="space-y-0.5 pr-2">
                        <div className="flex items-center space-x-1.5">
                          <span className="font-mono text-[9px] text-[#a1a1aa] font-bold">
                            #{s.number}
                          </span>
                          <span className="font-semibold text-[11px] leading-tight">
                            {s.title}
                          </span>
                        </div>
                        <p className="text-[9px] font-mono text-[#71717a]">
                          {s.description}
                        </p>
                      </div>

                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center flex-shrink-0 mt-0.5 ${
                          isChecked
                            ? "bg-[#10b981] border-[#10b981] text-black"
                            : "border-[#27272a] bg-[#18181b]"
                        }`}
                      >
                        {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* STAGE 2: COMPLETED SCENARIOS LIST WITH DUAL-VOICE AUDIO */}
        {scenariosToDisplay.length > 0 && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between text-[11px] text-[#a1a1aa] pt-1">
              <span className="font-semibold">Completed Combat Duels</span>
              <button
                onClick={() => setGauntletData(null)}
                className="text-[10px] font-mono text-[#10b981] hover:underline"
              >
                + New Attack Setup
              </button>
            </div>

            {scenariosToDisplay.map((sc, idx) => {
              const isExpanded = expandedIndex === idx;
              const isAutoPatched = sc.status === "AUTO-PATCHED";
              const isPassed = sc.status === "PASS";

              return (
                <div
                  key={sc.scenario_id}
                  className={`bg-[#09090b] border rounded-[6px] overflow-hidden transition-all shadow-sm ${
                    isAutoPatched
                      ? "border-[#10b981]/50 bg-[#10b981]/5"
                      : isPassed
                      ? "border-[#10b981]/40"
                      : "border-[#1f1f24]"
                  }`}
                >
                  <div
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="p-2.5 flex items-start justify-between cursor-pointer hover:bg-[#141418] transition-colors"
                  >
                    <div className="space-y-1 pr-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-[10px] font-bold text-[#71717a]">
                          #{sc.scenario_id}
                        </span>
                        <h4 className="text-xs font-semibold text-[#f4f4f6] leading-tight">
                          {sc.title}
                        </h4>
                      </div>
                      <p className="text-[10px] text-[#71717a] font-mono leading-tight">
                        {sc.attack_vector}
                      </p>
                    </div>

                    <div className="flex items-center space-x-1.5 flex-shrink-0">
                      {isAutoPatched ? (
                        <span className="px-1.5 py-0.5 rounded-[3px] bg-[#10b981]/20 border border-[#10b981]/50 text-[#10b981] font-mono text-[9px] font-bold">
                          AUTO-PATCHED
                        </span>
                      ) : isPassed ? (
                        <span className="px-1.5 py-0.5 rounded-[3px] bg-[#10b981]/15 text-[#10b981] font-mono text-[9px] font-bold">
                          PASS
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded-[3px] bg-[#27272a] text-[#a1a1aa] font-mono text-[9px]">
                          READY
                        </span>
                      )}
                      {isExpanded ? (
                        <ChevronUp className="w-3.5 h-3.5 text-[#71717a]" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-[#71717a]" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="p-2.5 pt-0 border-t border-[#1a1a20] space-y-2.5 bg-[#0c0c10]">
                      {/* Duel Audio Trigger */}
                      {sc.duel_transcript && sc.duel_transcript.length > 0 && (
                        <div className="pt-2 flex items-center justify-between">
                          <button
                            onClick={() => {
                              if (isAudioPlaying) {
                                stopDuelAudio();
                              } else {
                                playDuelAudio(sc.duel_transcript as any);
                              }
                            }}
                            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] text-[10px] font-mono text-[#10b981] transition-all"
                          >
                            {isAudioPlaying ? (
                              <>
                                <Square className="w-3 h-3 fill-[#ef4444] text-[#ef4444]" />
                                <span className="text-[#ef4444]">Stop Duel Audio</span>
                              </>
                            ) : (
                              <>
                                <Volume2 className="w-3 h-3" />
                                <span>🎧 Play Dual Voice Duel</span>
                              </>
                            )}
                          </button>
                          <span className="text-[9px] font-mono text-[#71717a]">
                            {sc.latency_ms}ms
                          </span>
                        </div>
                      )}

                      {/* Tool Validation Summary */}
                      <div className="p-1.5 bg-[#121216] border border-[#27272a] rounded-[4px] text-[10px] font-mono text-[#a1a1aa] flex items-center space-x-1.5">
                        <FileCheck2 className="w-3 h-3 text-[#10b981] flex-shrink-0" />
                        <span className="truncate">{sc.tool_validation_summary}</span>
                      </div>

                      {/* Expandable Duel Transcript */}
                      {sc.duel_transcript && sc.duel_transcript.length > 0 && (
                        <div className="space-y-1.5 pt-1 border-t border-[#1f1f24]">
                          <div className="text-[9px] font-mono text-[#71717a] uppercase tracking-wider">
                            Multi-Turn Transcript:
                          </div>
                          <div className="space-y-1 text-[10px] font-mono max-h-48 overflow-y-auto pr-1">
                            {sc.duel_transcript.map((msg, mIdx) => {
                              const sender = msg.sender || msg.speaker || "Agent";
                              const isAttacker = sender.toLowerCase().includes("attacker") || sender.toLowerCase().includes("caller");
                              return (
                                <div
                                  key={mIdx}
                                  className={`p-1.5 rounded-[3px] border ${
                                    isAttacker
                                      ? "bg-[#ef4444]/10 border-[#ef4444]/30 text-[#fca5a5]"
                                      : "bg-[#10b981]/10 border-[#10b981]/30 text-[#6ee7b7]"
                                  }`}
                                >
                                  <span className="font-bold block text-[9px] uppercase">
                                    {sender}:
                                  </span>
                                  <span className="leading-tight">{msg.text}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Bottom Launch Button Bar */}
      <div className="p-3 bg-[#0c0c0f] border-t border-[#1f1f24] space-y-2">
        <button
          onClick={handleRunGauntlet}
          disabled={isRunning || !activeDomain || selectedSuiteIds.length === 0}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-3 bg-[#16161a] hover:bg-[#1e1e24] text-[#f4f4f6] border border-[#2c2c35] hover:border-[#10b981] rounded-[6px] text-xs font-semibold font-mono transition-all disabled:opacity-50 shadow-md group"
        >
          {isRunning ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#10b981]" />
              <span>
                {activeScenarioId
                  ? `Running Suite #${activeScenarioId}...`
                  : "Executing Combat Queue..."}
              </span>
            </>
          ) : (
            <>
              <Zap className="w-3.5 h-3.5 text-[#f59e0b] group-hover:text-[#10b981] transition-colors" />
              <span>Launch Selected Anti-Agents ({selectedSuiteIds.length})</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
