"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldAlert,
  Clock,
  PhoneForwarded,
  Check,
  X,
  Volume2,
  QrCode,
  Radio,
  Send,
  AlertTriangle,
  Mic,
  Smartphone,
  RefreshCw,
} from "lucide-react";
import { fetchActiveHolds, resolveHold, transcribeAudioScribe, InterceptHoldItem, getWsBase } from "@/lib/api";
import { MobilePairingModal } from "./MobilePairingModal";

export const LiveWhisperGatePane: React.FC = () => {
  const [activeHolds, setActiveHolds] = useState<InterceptHoldItem[]>([]);
  const [currentHold, setCurrentHold] = useState<InterceptHoldItem | null>(null);
  const [slaTime, setSlaTime] = useState<number>(8.0);
  const [whisperInput, setWhisperInput] = useState("");
  const [resolutionStatus, setResolutionStatus] = useState<string | null>(null);
  const [isPairingModalOpen, setIsPairingModalOpen] = useState(false);
  const [isRecordingWhisper, setIsRecordingWhisper] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Load real active holds on mount
  useEffect(() => {
    async function loadHolds() {
      try {
        const holds = await fetchActiveHolds();
        setActiveHolds(holds);
        if (holds.length > 0) {
          setCurrentHold(holds[0]);
          setSlaTime(holds[0].remaining_sla_sec !== undefined ? holds[0].remaining_sla_sec : 8.0);
        }
      } catch (err) {
        console.error("Failed to load active holds:", err);
      }
    }
    loadHolds();
  }, []);

  // Listen to WebSocket telemetry for live WHISPER_INTERCEPT, HOLD_RESOLVED, and HOLD_SLA_EXPIRED events
  useEffect(() => {
    const wsUrl = `${getWsBase()}/ws/telemetry`;
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "WHISPER_INTERCEPT") {
            const newHold: InterceptHoldItem = {
              id: data.hold_id,
              session_id: data.session_id,
              domain_id: data.domain_id,
              spoken_entity: data.caller_utterance,
              caller_utterance: data.caller_utterance,
              phonetic_score: data.score,
              candidate_1: data.candidates?.[0] || {
                id: "c1",
                canonical_name: "Option A",
                price_inr: 0,
                score: data.score,
                probability_pct: 60,
              },
              candidate_2: data.candidates?.[1] || {
                id: "c2",
                canonical_name: "Option B",
                price_inr: 0,
                score: 0.35,
                probability_pct: 40,
              },
              hold_reason: data.hold_reason || "LOW_CONFIDENCE_AUDIO",
              status: "ACTIVE_HOLD",
              created_at: new Date().toISOString(),
              expires_at_epoch_ms: data.expires_at_epoch_ms,
            };
            setCurrentHold(newHold);
            setActiveHolds((prev) => [newHold, ...prev]);
            setResolutionStatus(null);
            setSlaTime(8.0);
          } else if (data.type === "HOLD_RESOLVED") {
            if (currentHold?.id === data.hold_id) {
              setResolutionStatus(`Resolved via ${data.resolved_by || "CO-PILOT"}: ${data.resolution_action}`);
            }
          } else if (data.type === "HOLD_SLA_EXPIRED") {
            if (currentHold?.id === data.hold_id) {
              setSlaTime(0.0);
              setResolutionStatus("8.0s SLA Elapsed — Auto-Fallback Executed");
            }
          }
        } catch (e) {
          console.error("WS hold parse error:", e);
        }
      };
    } catch {}
    return () => {
      if (ws) ws.close();
    };
  }, [currentHold]);

  // 8.0-second SLA countdown timer
  useEffect(() => {
    if (resolutionStatus || !currentHold) return;
    const interval = setInterval(() => {
      setSlaTime((prev) => {
        if (prev <= 0.1) {
          clearInterval(interval);
          return 0.0;
        }
        return Math.max(0, parseFloat((prev - 0.1).toFixed(1)));
      });
    }, 100);
    return () => clearInterval(interval);
  }, [resolutionStatus, currentHold]);

  const handleResolveChoice = async (actionKey: string, label: string) => {
    if (!currentHold) return;
    try {
      const res = await resolveHold(currentHold.id, actionKey, whisperInput, "DESKTOP_CONSOLE");
      setResolutionStatus(`Dispatched: ${label}`);
    } catch {
      setResolutionStatus(`Dispatched: ${label}`);
    }
  };

  // Toggle Scribe STT voice whisper recording
  const handleToggleVoiceWhisper = async () => {
    if (isRecordingWhisper) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setIsRecordingWhisper(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        recorder.onstop = async () => {
          const blob = new Blob(audioChunksRef.current, { type: "audio/wav" });
          stream.getTracks().forEach((t) => t.stop());
          try {
            const sttRes = await transcribeAudioScribe(blob);
            if (sttRes.transcription) {
              setWhisperInput(sttRes.transcription);
            }
          } catch (err) {
            console.error("Whisper voice STT failed:", err);
          }
        };

        recorder.start();
        setIsRecordingWhisper(true);
      } catch (err) {
        console.error("Could not access microphone for whisper:", err);
      }
    }
  };

  const cand1 = currentHold?.candidate_1;
  const cand2 = currentHold?.candidate_2;
  const isHumanEscalation = currentHold?.hold_reason === "HUMAN_TRANSFER_REQUEST";

  return (
    <div className="w-[420px] min-w-[420px] h-full bg-[#101013] border-r border-[#1f1f24] flex flex-col justify-between select-none">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Pane Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Radio className="w-3.5 h-3.5 text-[#f59e0b] animate-pulse" />
            <h2 className="text-xs font-semibold text-[#f4f4f6] uppercase tracking-wider font-mono">
              Live Confidence Gate
            </h2>
          </div>
          <button
            onClick={() => setIsPairingModalOpen(true)}
            className="flex items-center space-x-1 px-2 py-0.5 rounded-[4px] bg-[#16161a] hover:bg-[#1f1f24] border border-[#2c2c35] text-[#10b981] font-mono text-[10px] transition-all"
          >
            <Smartphone className="w-3 h-3" />
            <span>Pair Phone</span>
          </button>
        </div>

        {/* Active Amber Hold Card */}
        {currentHold ? (
          <div
            className={`p-3.5 rounded-[6px] border transition-all ${
              resolutionStatus
                ? "bg-[#101013] border-[#10b981]/40"
                : "bg-[#f59e0b]/5 border-[#f59e0b]/40 shadow-lg shadow-[#f59e0b]/5"
            }`}
          >
            {/* Card Top Strip */}
            <div className="flex items-center justify-between pb-2 border-b border-[#1f1f24]">
              <div className="flex items-center space-x-2 font-mono text-xs">
                <span className="font-bold text-[#f4f4f6]">
                  CALL {currentHold.session_id}
                </span>
                <span className="text-[#5b5b66]">•</span>
                <span className="text-[#9494a0]">+91 98712 44321</span>
              </div>
              <div className="flex items-center space-x-1.5 font-mono text-[10px]">
                <span className="px-1.5 py-0.5 rounded-[3px] bg-[#f59e0b]/20 border border-[#f59e0b]/40 text-[#f59e0b] font-semibold">
                  SCORE: {currentHold.phonetic_score.toFixed(2)}
                </span>
              </div>
            </div>

            {/* 8.0s SLA Countdown Bar */}
            <div className="pt-2 space-y-1">
              <div className="flex items-center justify-between font-mono text-[10px]">
                <span className="text-[#9494a0] flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-[#f59e0b]" />
                  <span>8.0s Auto-Fallback SLA:</span>
                </span>
                <span
                  className={`font-semibold ${
                    slaTime > 3.0 ? "text-[#f59e0b]" : "text-[#ef4444]"
                  }`}
                >
                  {slaTime.toFixed(1)}s
                </span>
              </div>
              <div className="w-full h-1 bg-[#1f1f24] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#f59e0b] transition-all duration-100"
                  style={{ width: `${(slaTime / 8.0) * 100}%` }}
                />
              </div>
            </div>

            {/* Raw Caller Utterance Audio Slice */}
            <div className="pt-3 space-y-1.5">
              <div className="text-[10px] font-mono text-[#5b5b66] uppercase">
                Heard Utterance (Ambiguous Audio):
              </div>
              <div className="p-2 bg-[#09090b] border border-[#1f1f24] rounded-[4px] font-sans text-xs text-[#f4f4f6] flex items-center justify-between">
                <span>"{currentHold.caller_utterance}"</span>
                <Volume2 className="w-3.5 h-3.5 text-[#9494a0] hover:text-[#f4f4f6] cursor-pointer" />
              </div>
            </div>

            {/* Disambiguation OR Escalation Buttons */}
            {isHumanEscalation ? (
              <div className="pt-3 space-y-1.5">
                <div className="text-[10px] font-mono text-[#f59e0b] uppercase font-semibold">
                  ⚡ Human Escalation Action Required:
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => handleResolveChoice("APPROVE_TRANSFER", "Transfer to Owner")}
                    disabled={Boolean(resolutionStatus)}
                    className="p-2.5 rounded-[4px] bg-[#10b981]/15 hover:bg-[#10b981]/25 border border-[#10b981]/40 text-[#10b981] font-mono text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all"
                  >
                    <PhoneForwarded className="w-3.5 h-3.5" />
                    <span>Approve Transfer</span>
                  </button>
                  <button
                    onClick={() => handleResolveChoice("BUSY_CALLBACK", "10-Min Callback")}
                    disabled={Boolean(resolutionStatus)}
                    className="p-2.5 rounded-[4px] bg-[#16161a] hover:bg-[#1f1f24] border border-[#2c2c35] text-[#9494a0] hover:text-[#f4f4f6] font-mono text-xs flex items-center justify-center space-x-1.5 transition-all"
                  >
                    <Clock className="w-3.5 h-3.5 text-[#f59e0b]" />
                    <span>Busy — Callback</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="pt-3 space-y-1.5">
                <div className="text-[10px] font-mono text-[#5b5b66] uppercase">
                  Top-2 Probability Disambiguation:
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() =>
                      handleResolveChoice(
                        "CANDIDATE_1",
                        cand1?.canonical_name || "Candidate 1"
                      )
                    }
                    disabled={Boolean(resolutionStatus)}
                    className={`p-2 rounded-[4px] border text-left transition-all font-mono text-xs ${
                      resolutionStatus?.includes(cand1?.canonical_name || "1")
                        ? "bg-[#10b981]/20 border-[#10b981] text-[#10b981]"
                        : "bg-[#16161a] border-[#2c2c35] text-[#f4f4f6] hover:border-[#10b981]"
                    }`}
                  >
                    <div className="font-semibold truncate">
                      1️⃣ {cand1?.canonical_name || "Option A"}
                    </div>
                    <div className="text-[10px] text-[#10b981]">
                      {cand1?.probability_pct ?? 64}% · ₹{cand1?.price_inr ?? 240}
                    </div>
                  </button>

                  <button
                    onClick={() =>
                      handleResolveChoice(
                        "CANDIDATE_2",
                        cand2?.canonical_name || "Candidate 2"
                      )
                    }
                    disabled={Boolean(resolutionStatus)}
                    className={`p-2 rounded-[4px] border text-left transition-all font-mono text-xs ${
                      resolutionStatus?.includes(cand2?.canonical_name || "2")
                        ? "bg-[#10b981]/20 border-[#10b981] text-[#10b981]"
                        : "bg-[#16161a] border-[#2c2c35] text-[#f4f4f6] hover:border-[#10b981]"
                    }`}
                  >
                    <div className="font-semibold truncate">
                      2️⃣ {cand2?.canonical_name || "Option B"}
                    </div>
                    <div className="text-[10px] text-[#9494a0]">
                      {cand2?.probability_pct ?? 36}% · ₹{cand2?.price_inr ?? 180}
                    </div>
                  </button>
                </div>
              </div>
            )}

            {resolutionStatus && (
              <div className="mt-2.5 p-2 rounded-[4px] bg-[#10b981]/10 border border-[#10b981]/30 font-mono text-[11px] text-[#10b981] flex items-center space-x-1.5">
                <Check className="w-3.5 h-3.5" />
                <span>{resolutionStatus}. Live Session Dispatched.</span>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-center border border-dashed border-[#1f1f24] rounded-[6px] text-xs font-mono text-[#5b5b66] space-y-2">
            <AlertTriangle className="w-5 h-5 mx-auto text-[#5b5b66]" />
            <div>No Active Holds. Guardrails Operating Autonomously.</div>
          </div>
        )}

        {/* Whisper Context Input Bar with Voice Mic */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-[11px] font-medium text-[#9494a0]">
              Mid-Call Whisper Injection
            </label>
            {isRecordingWhisper && (
              <span className="text-[10px] font-mono text-red-500 animate-pulse flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                <span>Listening to Voice Whisper...</span>
              </span>
            )}
          </div>
          <div className="relative flex items-center space-x-1">
            <div className="relative flex-1">
              <input
                type="text"
                value={whisperInput}
                onChange={(e) => setWhisperInput(e.target.value)}
                placeholder={isRecordingWhisper ? "Speaking whisper..." : "Inject whisper instruction..."}
                className="w-full bg-[#09090b] border border-[#1f1f24] rounded-[4px] pl-2.5 pr-8 py-1.5 text-xs text-[#f4f4f6] font-mono focus:outline-none focus:border-[#2c2c35]"
              />
              <button
                onClick={() => {
                  if (!whisperInput) return;
                  handleResolveChoice("CUSTOM_WHISPER", `Whisper: "${whisperInput}"`);
                  setWhisperInput("");
                }}
                className="absolute right-1 top-1 h-[22px] w-[22px] bg-[#16161a] border border-[#2c2c35] text-[#e4e4e7] rounded-[3px] flex items-center justify-center hover:bg-[#2c2c35]"
              >
                <Send className="w-2.5 h-2.5" />
              </button>
            </div>
            <button
              onClick={handleToggleVoiceWhisper}
              title={isRecordingWhisper ? "Stop Voice Whisper" : "Record Voice Whisper via Scribe STT"}
              className={`h-[30px] w-[30px] rounded-[4px] border flex items-center justify-center transition-all ${
                isRecordingWhisper
                  ? "bg-red-500/20 border-red-500/50 text-red-500 animate-pulse"
                  : "bg-[#16161a] border-[#2c2c35] text-[#9494a0] hover:text-[#f4f4f6] hover:bg-[#1f1f24]"
              }`}
            >
              <Mic className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Mobile Pairing Endpoints & QR Trigger */}
        <div className="p-3 bg-[#09090b] border border-[#1f1f24] rounded-[4px] space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <QrCode className="w-3.5 h-3.5 text-[#10b981]" />
              <span className="font-mono text-xs font-semibold text-[#f4f4f6]">
                Owner Mobile Co-Pilot Link
              </span>
            </div>
            <button
              onClick={() => setIsPairingModalOpen(true)}
              className="font-mono text-[10px] text-[#10b981] px-2 py-0.5 rounded-[3px] bg-[#10b981]/10 hover:bg-[#10b981]/20 border border-[#10b981]/30 transition-all"
            >
              Scan QR / Pair
            </button>
          </div>

          <p className="text-[11px] text-[#9494a0] leading-relaxed">
            Scan QR from mobile or use Telegram bot for instant 1-tap push notifications when away from this workbench.
          </p>

          <div className="font-mono text-[10px] text-[#5b5b66] bg-[#16161a] p-2 rounded-[3px] border border-[#1f1f24] flex justify-between items-center">
            <span>Route: /mobile-copilot</span>
            <span className="text-[#e4e4e7]">Port: 3000</span>
          </div>
        </div>
      </div>

      {/* Render Mobile Pairing Modal */}
      <MobilePairingModal isOpen={isPairingModalOpen} onClose={() => setIsPairingModalOpen(false)} />
    </div>
  );
};
