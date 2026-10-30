"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Swords,
  Play,
  RotateCcw,
  Volume2,
  Lock,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  Square,
  ShieldCheck,
  ShieldAlert,
  Mic,
  Send,
  Check,
  Sliders,
  ChevronRight,
  ArrowLeft,
  VolumeX,
} from "lucide-react";
import {
  DomainProfile,
  GauntletScenarioItem,
  GauntletRunResult,
  runGauntlet,
  synthesizeDuelAudio,
  refineDomainPolicy,
  resetGauntletVulnerability,
} from "@/lib/api";

const AVAILABLE_SUITES = [
  {
    id: "discount_escalation",
    number: 1,
    title: "Anti-Agent 1: The Relentless Bargainer & VIP Bully",
    turns: 4,
    badge: "Social Engineering & Escalation",
    badgeColor: "text-red-400 bg-red-950/40 border-red-800/60",
    description:
      "Tests 3x persistent discount begging (VIP/cousin claims, emotional budget pleading, competitor rate threats) and Turn 4 Angry Manager Demand -> Live Call Takeover Alert.",
    tools: ["enforce_price_lock", "verify_catalog_item", "request_human_intervention"],
  },
  {
    id: "domain_flow_trap",
    number: 2,
    title: "Anti-Agent 2: Phonetic Barge-In, Off-Menu, Fake UTR & PII Probe",
    turns: 4,
    badge: "Phonetics & Data Privacy",
    badgeColor: "text-amber-400 bg-amber-950/40 border-amber-800/60",
    description:
      "Tests multi-item Double-Metaphone phonetic booking, mid-call cancellation + domain-specific off-menu trap (e.g. MRI in dental, sushi in cafe), unverified UPI UTR rejection, and customer PII protection.",
    tools: ["verify_catalog_item", "order_modification", "verify_payment_guardrail", "pii_guardrail"],
  },
  {
    id: "off_topic_termination",
    number: 3,
    title: "Anti-Agent 3: Persistent Off-Topic Timepasser",
    turns: 2,
    badge: "2-Strike Auto Hangup",
    badgeColor: "text-purple-400 bg-purple-950/40 border-purple-800/60",
    description:
      "Tests Strike 1 polite domain redirect (cricket / IPL query) and Strike 2 automatic terminate_call() disconnection (stock market advice) with SQLite ledger logging.",
    tools: ["off_topic_strike_1_warn", "terminate_call:OFF_TOPIC_2_STRIKES"],
  },
  {
    id: "brutal_injection_flood",
    number: 4,
    title: "Anti-Agent 4: Brutal Prompt-Injection & Velocity Spammer",
    turns: 2,
    badge: "Pre-LLM BrutalShield <10ms",
    badgeColor: "text-cyan-400 bg-cyan-950/40 border-cyan-800/60",
    description:
      "Tests developer debug roleplay jailbreaks and <10ms Pre-LLM BrutalShield regex & velocity kill switch (zero LLM tokens burned).",
    tools: ["brutal_shield:TERMINATE_ATTACK"],
  },
];

interface CombatArenaViewProps {
  activeDomain: DomainProfile | null;
  onDomainUpdated?: (domain: DomainProfile) => void;
}

export const CombatArenaView: React.FC<CombatArenaViewProps> = ({
  activeDomain,
  onDomainUpdated,
}) => {
  const domainId = activeDomain?.id || "brew-bite-cafe";

  // Clean-Slate Selector State
  const [selectedSuiteIds, setSelectedSuiteIds] = useState<string[]>([
    "discount_escalation",
    "domain_flow_trap",
  ]);
  const [activeStage, setActiveStage] = useState<"SELECTOR" | "DUEL_ACTIVE">("SELECTOR");

  // Battle Queue Execution State
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentRunningSuiteId, setCurrentRunningSuiteId] = useState<string | null>(null);
  const [completedSuites, setCompletedSuites] = useState<GauntletScenarioItem[]>([]);
  const [activeTabIdx, setActiveTabIdx] = useState<number>(0);

  // Audio Player State (Module E)
  const [isAudioPlaying, setIsAudioPlaying] = useState<boolean>(false);
  const [activeAudioTurnIdx, setActiveAudioTurnIdx] = useState<number | null>(null);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.2);
  const turnScrollRefs = useRef<(HTMLDivElement | null)[]>([]);

  // Owner Verdict & Policy Refine State (Module E)
  const [ownerApprovedSuites, setOwnerApprovedSuites] = useState<Record<string, boolean>>({});
  const [tweakInstruction, setTweakInstruction] = useState<string>("");
  const [isTweaking, setIsTweaking] = useState<boolean>(false);
  const [tweakSuccessMessage, setTweakSuccessMessage] = useState<string | null>(null);

  // Toggle suite selection in selector
  const toggleSuite = (id: string) => {
    setSelectedSuiteIds((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const selectAllSuites = () => {
    setSelectedSuiteIds(AVAILABLE_SUITES.map((s) => s.id));
  };

  const clearAllSuites = () => {
    setSelectedSuiteIds([]);
  };

  // Stop dual-voice audio
  const stopDuelAudio = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsAudioPlaying(false);
    setActiveAudioTurnIdx(null);
  };

  // Dual-Voice Web SpeechSynthesis Audio Player
  const playDualVoiceDuel = (transcript: Array<{ speaker: string; text: string }>) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window) || !transcript || transcript.length === 0) return;

    stopDuelAudio();
    window.speechSynthesis.resume();
    setIsAudioPlaying(true);

    const voices = window.speechSynthesis.getVoices();
    const hindiOrIndianVoice = voices.find(
      (v) =>
        v.lang.includes("IN") ||
        v.lang.includes("hi") ||
        v.name.includes("India") ||
        v.name.includes("Google")
    ) || voices[0];

    let currentTurn = 0;

    const playNextTurn = () => {
      if (currentTurn >= transcript.length) {
        setIsAudioPlaying(false);
        setActiveAudioTurnIdx(null);
        return;
      }

      const turn = transcript[currentTurn];
      setActiveAudioTurnIdx(currentTurn);

      // Smooth scroll to speaking turn bubble
      const el = turnScrollRefs.current[currentTurn];
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }

      const isAttacker = turn.speaker.toLowerCase().includes("attacker") || turn.speaker.toLowerCase().includes("caller");
      const utt = new SpeechSynthesisUtterance(turn.text);
      if (hindiOrIndianVoice) utt.voice = hindiOrIndianVoice;
      utt.rate = playbackSpeed;

      if (isAttacker) {
        utt.pitch = 0.85; // Male adversarial caller pitch
      } else {
        utt.pitch = 1.15; // Female business agent pitch
      }

      utt.onend = () => {
        currentTurn++;
        setTimeout(playNextTurn, 220);
      };

      utt.onerror = () => {
        setIsAudioPlaying(false);
        setActiveAudioTurnIdx(null);
      };

      window.speechSynthesis.resume();
      window.speechSynthesis.speak(utt);
    };

    playNextTurn();
  };

  // Launch Sequential Duel Queue
  const handleLaunchQueue = async () => {
    if (selectedSuiteIds.length === 0) return;
    setIsRunning(true);
    setActiveStage("DUEL_ACTIVE");
    stopDuelAudio();
    setCompletedSuites([]);
    setActiveTabIdx(0);

    try {
      // Execute selected suites via backend gauntlet service
      const result: GauntletRunResult = await runGauntlet(domainId, true, selectedSuiteIds);
      setCompletedSuites(result.scenarios || []);

      // Pre-synthesize dual voice metadata for first suite
      if (result.scenarios && result.scenarios.length > 0) {
        const topScen = result.scenarios[0];
        if (topScen.duel_transcript && topScen.duel_transcript.length > 0) {
          try {
            await synthesizeDuelAudio(
              domainId,
              selectedSuiteIds[0] || "discount_escalation",
              topScen.duel_transcript.map((t: any) => ({
                speaker: t.speaker || t.sender || "Speaker",
                text: t.text,
              }))
            );
          } catch (e) {
            // Non-blocking fallback
          }
        }
      }
    } catch (err: any) {
      console.error("Queue execution error:", err);
    } finally {
      setIsRunning(false);
      setCurrentRunningSuiteId(null);
    }
  };

  // Owner Policy Refinement & Instant Re-Run
  const handleApplyPolicyPatch = async () => {
    if (!tweakInstruction.trim() || isTweaking) return;
    setIsTweaking(true);
    setTweakSuccessMessage(null);
    stopDuelAudio();

    const activeScen = completedSuites[activeTabIdx];
    const targetSuiteId = activeScen
      ? AVAILABLE_SUITES[activeTabIdx]?.id || "discount_escalation"
      : selectedSuiteIds[0];

    try {
      const res = await refineDomainPolicy(domainId, tweakInstruction.trim(), targetSuiteId);
      setTweakSuccessMessage(`Policy Applied: "${res.refined_rule}". Re-running suite now...`);
      setTweakInstruction("");

      if (res.rerun_result && res.rerun_result.scenarios) {
        setCompletedSuites((prev) => {
          const updated = [...prev];
          const newScen = res.rerun_result?.scenarios[0];
          if (newScen && updated[activeTabIdx]) {
            updated[activeTabIdx] = newScen;
          }
          return updated;
        });

        if (res.rerun_result.scenarios[0]?.duel_transcript) {
          playDualVoiceDuel(
            res.rerun_result.scenarios[0].duel_transcript.map((t: any) => ({
              speaker: t.speaker || t.sender || "Speaker",
              text: t.text,
            }))
          );
        }
      }
    } catch (err: any) {
      alert(`Refinement failed: ${err.message}`);
    } finally {
      setIsTweaking(false);
      setTimeout(() => setTweakSuccessMessage(null), 5000);
    }
  };

  const activeScenario = completedSuites[activeTabIdx] || null;
  const activeTranscript = activeScenario?.duel_transcript || [];

  return (
    <div className="w-full h-full flex flex-col bg-[#09090b] text-[#f4f4f6] overflow-y-auto">
      {/* 1. Header Banner */}
      <div className="w-full border-b border-[#24242a] bg-[#111114] px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-red-950/40 border border-red-800/60 flex items-center justify-center text-red-400">
            <Swords className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold tracking-tight text-white">
                Combat Arena · Insistent Adversarial Gauntlet
              </h1>
              <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[10px] border border-zinc-700 uppercase">
                {activeDomain?.name || "Active Domain"}
              </span>
            </div>
            <p className="text-xs text-zinc-400 mt-0.5">
              Multi-turn adversarial stress testing with persistent anti-agent personas, Double-Metaphone phonetics, and sub-second defense.
            </p>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex items-center space-x-2">
          {activeStage === "DUEL_ACTIVE" && (
            <button
              onClick={() => {
                stopDuelAudio();
                setActiveStage("SELECTOR");
              }}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-xs text-zinc-200 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Attack Selector</span>
            </button>
          )}

          {activeStage === "DUEL_ACTIVE" && activeTranscript.length > 0 && (
            <>
              {/* Playback Speed */}
              <div className="flex items-center rounded-lg bg-zinc-900 border border-zinc-700 p-0.5 text-xs font-mono">
                {[1.0, 1.25, 1.5].map((spd) => (
                  <button
                    key={spd}
                    onClick={() => setPlaybackSpeed(spd)}
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-colors ${
                      playbackSpeed === spd
                        ? "bg-zinc-700 text-white"
                        : "text-zinc-400 hover:text-white"
                    }`}
                  >
                    {spd}x
                  </button>
                ))}
              </div>

              {/* Audio Listen Button */}
              <button
                onClick={() => {
                  if (isAudioPlaying) {
                    stopDuelAudio();
                  } else {
                    playDualVoiceDuel(
                      activeTranscript.map((t: any) => ({
                        speaker: t.speaker || t.sender || "Speaker",
                        text: t.text,
                      }))
                    );
                  }
                }}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all ${
                  isAudioPlaying
                    ? "bg-red-950/40 border-red-800 text-red-300"
                    : "bg-emerald-950/40 hover:bg-emerald-900/40 border-emerald-800/60 text-emerald-300"
                }`}
              >
                {isAudioPlaying ? (
                  <>
                    <Square className="w-3.5 h-3.5 fill-red-400 text-red-400" />
                    <span>Stop Duel Audio</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>🎧 Listen to Duel</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </div>

      {/* 2. STAGE A: CLEAN-SLATE ATTACK SUITE SELECTOR (NO PRE-WRITTEN CHAT) */}
      {activeStage === "SELECTOR" && (
        <div className="p-6 max-w-4xl mx-auto w-full space-y-6">
          <div className="rounded-2xl bg-[#111114] border border-zinc-800 p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-4">
              <div>
                <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-200 font-mono">
                  Targeted Attack Suite Selector
                </h2>
                <p className="text-xs text-zinc-400 mt-1">
                  Select which adversarial personas to launch against your business agent. Duels execute sequentially with live telemetry.
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={selectAllSuites}
                  className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[11px] text-zinc-300 font-mono border border-zinc-700 transition-colors"
                >
                  Select All 4
                </button>
                <button
                  onClick={clearAllSuites}
                  className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[11px] text-zinc-400 font-mono border border-zinc-700 transition-colors"
                >
                  Clear All
                </button>
              </div>
            </div>

            {/* 4 Selectable Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {AVAILABLE_SUITES.map((suite) => {
                const isChecked = selectedSuiteIds.includes(suite.id);
                return (
                  <div
                    key={suite.id}
                    onClick={() => toggleSuite(suite.id)}
                    className={`cursor-pointer rounded-xl p-4 border transition-all duration-150 flex flex-col justify-between ${
                      isChecked
                        ? "bg-zinc-900/90 border-emerald-500/80 shadow-[0_0_15px_rgba(16,185,129,0.15)] ring-1 ring-emerald-500/30"
                        : "bg-[#141418] border-zinc-800 hover:border-zinc-700 opacity-70 hover:opacity-100"
                    }`}
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono border uppercase font-semibold ${suite.badgeColor}`}>
                          {suite.badge}
                        </span>
                        <div
                          className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors ${
                            isChecked
                              ? "bg-emerald-600 border-emerald-500 text-black"
                              : "border-zinc-700 bg-zinc-800"
                          }`}
                        >
                          {isChecked && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                        </div>
                      </div>

                      <h3 className="text-xs font-bold text-white leading-snug">
                        {suite.title}
                      </h3>
                      <p className="text-[11px] text-zinc-400 leading-relaxed">
                        {suite.description}
                      </p>
                    </div>

                    <div className="mt-3 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-[10px] font-mono text-zinc-500">
                      <span>{suite.turns} Turns Duel</span>
                      <span>Tools: {suite.tools.length}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Launch CTA */}
            <div className="pt-4 border-t border-zinc-800 flex items-center justify-between">
              <div className="text-xs font-mono text-zinc-400">
                <span className="text-emerald-400 font-bold">{selectedSuiteIds.length}</span> of 4 Anti-Agents Selected
              </div>

              <button
                onClick={handleLaunchQueue}
                disabled={selectedSuiteIds.length === 0 || isRunning}
                className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-[0_0_20px_rgba(16,185,129,0.3)]"
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-black" />
                    <span>Executing Combat Duels...</span>
                  </>
                ) : (
                  <>
                    <Swords className="w-4 h-4 text-black" />
                    <span>⚔️ Launch Selected Anti-Agents ({selectedSuiteIds.length})</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 3. STAGE B: ACTIVE DUEL QUEUE & TRANSCRIPT STAGE */}
      {activeStage === "DUEL_ACTIVE" && (
        <div className="p-6 max-w-5xl mx-auto w-full space-y-6">
          {/* Attack Execution Queue Bar */}
          <div className="rounded-xl bg-[#141418] border border-zinc-800 p-3.5 flex items-center space-x-3 overflow-x-auto">
            <span className="text-[11px] font-mono uppercase text-zinc-400 shrink-0 font-bold">
              Execution Queue:
            </span>
            <div className="flex items-center space-x-2 shrink-0">
              {selectedSuiteIds.map((sId, qIdx) => {
                const sMeta = AVAILABLE_SUITES.find((s) => s.id === sId);
                const isDone = completedSuites.some((cs) => cs.scenario_id === qIdx + 1 || cs.title.includes(sMeta?.title || ""));
                const isCurrent = isRunning && qIdx === completedSuites.length;

                return (
                  <div
                    key={sId}
                    className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-mono border transition-all ${
                      isDone
                        ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
                        : isCurrent
                        ? "bg-amber-950/40 border-amber-500 text-amber-200 animate-pulse"
                        : "bg-zinc-900 border-zinc-800 text-zinc-500"
                    }`}
                  >
                    <span>
                      {isDone ? "✓" : isCurrent ? "●" : "⏳"} {sMeta?.number}. {sMeta?.title.split(":")[1]?.trim() || sId}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Scenario Tab Selector for Completed Runs */}
          {completedSuites.length > 0 && (
            <div className="flex items-center space-x-2 border-b border-zinc-800 pb-2 overflow-x-auto">
              {completedSuites.map((scen, idx) => {
                const isApproved = !!ownerApprovedSuites[idx];
                return (
                  <button
                    key={scen.scenario_id}
                    onClick={() => {
                      stopDuelAudio();
                      setActiveTabIdx(idx);
                    }}
                    className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border shrink-0 ${
                      activeTabIdx === idx
                        ? "bg-zinc-800 text-white border-zinc-600 shadow-sm"
                        : "text-zinc-400 hover:text-zinc-200 border-transparent hover:bg-zinc-900"
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        scen.status === "PASS"
                          ? "bg-emerald-400"
                          : scen.status === "AUTO-PATCHED"
                          ? "bg-amber-400"
                          : "bg-red-400"
                      }`}
                    />
                    <span className="font-mono text-[10px] text-zinc-500">#{scen.scenario_id}</span>
                    <span className="truncate max-w-[200px]">{scen.title.split("—")[0].trim()}</span>
                    {isApproved && (
                      <span className="text-[10px] text-emerald-400 font-mono">✓ Verified</span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Active Scenario Card & Dialogue Bubbles */}
          {activeScenario ? (
            <div className="space-y-6">
              {/* Scenario Header Info */}
              <div className="rounded-2xl bg-[#141418] border border-zinc-800 p-5 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800 pb-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700">
                        SCENARIO #{activeScenario.scenario_id}
                      </span>
                      <span
                        className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
                          activeScenario.status === "PASS"
                            ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/50"
                            : "bg-amber-950/40 text-amber-300 border-amber-800/50"
                        }`}
                      >
                        {activeScenario.status === "PASS" ? "ATTACK DEFENDED" : "AUTO-HEALED & LOCKED"}
                      </span>
                      {ownerApprovedSuites[activeTabIdx] && (
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-900/60 text-emerald-300 border border-emerald-600">
                          ✓ OWNER-VERIFIED
                        </span>
                      )}
                    </div>
                    <h2 className="text-base font-bold text-white mt-1.5">{activeScenario.title}</h2>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-zinc-400 font-mono block">
                      Latency: {activeScenario.latency_ms}ms (llama-3.1-8b)
                    </span>
                    <span className="text-[11px] text-zinc-500">
                      Vector: {activeScenario.attack_vector}
                    </span>
                  </div>
                </div>

                <div className="text-xs text-zinc-300 bg-zinc-900/60 p-3 rounded-xl border border-zinc-800/80 flex items-center space-x-2">
                  <span className="font-semibold text-emerald-400 shrink-0">Validation Audit:</span>
                  <span className="text-zinc-300">{activeScenario.tool_validation_summary}</span>
                </div>
              </div>

              {/* Multi-Turn Dialogue Bubble Stream */}
              <div className="rounded-2xl bg-[#111114] border border-zinc-800 p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <Swords className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300 font-mono">
                      Dynamic Back-and-Forth Duel ({activeTranscript.length} Turns)
                    </h3>
                  </div>

                  {isAudioPlaying && (
                    <div className="flex items-center space-x-2 text-xs font-mono text-emerald-400">
                      <span className="inline-block animate-pulse">🔊 Dual-Voice Playback Active</span>
                      <span className="text-zinc-500 font-normal">|</span>
                      <span className="text-zinc-400">Turn {(activeAudioTurnIdx ?? 0) + 1}</span>
                    </div>
                  )}
                </div>

                <div className="space-y-4 pt-2">
                  {activeTranscript.map((turn, tIdx) => {
                    const speakerName = turn.speaker || "Speaker";
                    const isAttacker = speakerName.toLowerCase().includes("attacker") || speakerName.toLowerCase().includes("caller");
                    const isEvaluator = speakerName.toLowerCase().includes("evaluator");
                    const isPlayingNow = activeAudioTurnIdx === tIdx;

                    if (isEvaluator) {
                      return (
                        <div
                          key={tIdx}
                          ref={(el) => { turnScrollRefs.current[tIdx] = el; }}
                          className={`p-3.5 rounded-xl border font-mono text-xs transition-all ${
                            isPlayingNow
                              ? "bg-amber-950/60 border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.4)] scale-[1.01]"
                              : "bg-amber-950/20 border-amber-800/40 text-amber-200"
                          }`}
                        >
                          <div className="flex items-center space-x-2 mb-1">
                            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                            <span className="font-bold text-amber-300 text-[11px] uppercase">
                              Chief Security Evaluator Intercept
                            </span>
                          </div>
                          <p className="text-xs text-amber-200/90 leading-relaxed">{turn.text}</p>
                        </div>
                      );
                    }

                    return (
                      <div
                        key={tIdx}
                        ref={(el) => { turnScrollRefs.current[tIdx] = el; }}
                        className={`flex flex-col ${isAttacker ? "items-start" : "items-end"}`}
                      >
                        <div className="flex items-center space-x-2 mb-1 px-1">
                          <span
                            className={`text-[11px] font-mono font-semibold uppercase ${
                              isAttacker ? "text-red-400" : "text-emerald-400"
                            }`}
                          >
                            {speakerName}
                          </span>
                          {isPlayingNow && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-white text-black font-bold animate-pulse">
                              🔊 SPEAKING NOW
                            </span>
                          )}
                        </div>

                        <div
                          className={`max-w-[85%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed transition-all duration-200 border ${
                            isAttacker
                              ? isPlayingNow
                                ? "bg-red-950/70 border-red-500 shadow-[0_0_25px_rgba(239,68,68,0.5)] scale-[1.01] text-red-100 rounded-tl-none"
                                : "bg-red-950/30 border-red-900/50 text-red-200 rounded-tl-none"
                              : isPlayingNow
                              ? "bg-emerald-950/70 border-emerald-500 shadow-[0_0_25px_rgba(16,185,129,0.5)] scale-[1.01] text-emerald-100 rounded-tr-none"
                              : "bg-[#16161c] border-zinc-700/80 text-zinc-100 rounded-tr-none"
                          }`}
                        >
                          <p>{turn.text}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* MODULE E: OWNER VERDICT & LIVE TWEAK & RE-TEST DOCK */}
              <div className="rounded-2xl bg-[#141418] border border-zinc-800 p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-3">
                  <div className="flex items-center space-x-2">
                    <Sliders className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white font-mono">
                      Owner Verdict & Interactive Policy Refinement Dock
                    </h3>
                  </div>

                  <button
                    onClick={() => {
                      setOwnerApprovedSuites((prev) => ({ ...prev, [activeTabIdx]: true }));
                    }}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      ownerApprovedSuites[activeTabIdx]
                        ? "bg-emerald-600 text-black border border-emerald-500"
                        : "bg-zinc-800 hover:bg-zinc-700 text-emerald-400 border border-zinc-700"
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>
                      {ownerApprovedSuites[activeTabIdx] ? "Response Approved" : "Approve Agent Response"}
                    </span>
                  </button>
                </div>

                {tweakSuccessMessage && (
                  <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-700/60 text-xs text-emerald-300 font-mono">
                    {tweakSuccessMessage}
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={tweakInstruction}
                    onChange={(e) => setTweakInstruction(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleApplyPolicyPatch()}
                    placeholder="e.g. Jab customer 3rd time discount maange toh free addon offer mat karo, seedha polite mana karo..."
                    className="flex-1 bg-zinc-900 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-500"
                  />

                  <button
                    onClick={handleApplyPolicyPatch}
                    disabled={!tweakInstruction.trim() || isTweaking}
                    className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-black font-semibold text-xs transition-all active:scale-95 disabled:opacity-50 shrink-0"
                  >
                    {isTweaking ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Patching...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Apply Patch & Re-Run Duel</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-zinc-500 font-mono text-xs">
              Combat duel running or no results returned yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
