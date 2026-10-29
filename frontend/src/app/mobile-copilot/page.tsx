"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Radio,
  PhoneForwarded,
  CheckCircle2,
  Clock,
  Volume2,
  ShieldAlert,
  Mic,
  MicOff,
  Send,
  Sparkles,
  PhoneCall,
  UserCheck,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import {
  InterceptHoldItem,
  fetchActiveHolds,
  resolveHold,
  getWsBase,
  transcribeAudioScribe,
} from "@/lib/api";

interface LocalHold extends InterceptHoldItem {
  resolvedAction?: string;
  resolvedAt?: number;
}

export default function MobileCopilotPage() {
  const [holds, setHolds] = useState<LocalHold[]>([]);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [now, setNow] = useState<number>(0);
  const [customWhispers, setCustomWhispers] = useState<Record<string, string>>({});
  const [isRecording, setIsRecording] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // SLA ticker every 100ms
  useEffect(() => {
    setNow(Date.now());
    const timer = setInterval(() => {
      setNow(Date.now());
    }, 100);
    return () => clearInterval(timer);
  }, []);

  // Fetch active holds on mount
  useEffect(() => {
    fetchActiveHolds()
      .then((data) => {
        setHolds(data);
      })
      .catch((err) => {
        console.error("Failed to fetch initial active holds:", err);
      });
  }, []);

  // Connect to live WebSocket telemetry
  useEffect(() => {
    let reconnectTimeout: any = null;

    function connectWs() {
      const wsUrl = `${getWsBase()}/ws/telemetry`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsConnected(true);
      };

      ws.onclose = () => {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWs, 2000);
      };

      ws.onerror = () => {
        setWsConnected(false);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === "WHISPER_INTERCEPT") {
            const newHold: LocalHold = {
              id: msg.data.hold_id,
              session_id: msg.data.session_id,
              domain_id: msg.data.domain_id || "brew-bite-cafe",
              spoken_entity: msg.data.spoken_entity || "",
              caller_utterance: msg.data.caller_utterance || "",
              phonetic_score: msg.data.phonetic_score || 0,
              candidate_1: msg.data.candidate_1,
              candidate_2: msg.data.candidate_2,
              hold_reason: msg.data.hold_reason || "AMBIGUOUS_MATCH",
              status: "ACTIVE_HOLD",
              created_at: new Date().toISOString(),
              remaining_sla_sec: msg.data.remaining_sla_sec || 8.0,
              expires_at_epoch_ms: msg.data.expires_at_epoch_ms || (Date.now() + 8000),
            };
            setHolds((prev) => {
              const filtered = prev.filter((h) => h.id !== newHold.id);
              return [newHold, ...filtered];
            });
          } else if (msg.event === "HOLD_RESOLVED") {
            setHolds((prev) =>
              prev.map((h) =>
                h.id === msg.data.hold_id
                  ? {
                      ...h,
                      status: "RESOLVED",
                      resolvedAction: msg.data.resolution_action,
                      resolvedAt: Date.now(),
                    }
                  : h
              )
            );
          } else if (msg.event === "HOLD_SLA_EXPIRED") {
            setHolds((prev) =>
              prev.map((h) =>
                h.id === msg.data.hold_id
                  ? {
                      ...h,
                      status: "SLA_AUTO_FALLBACK",
                      resolvedAction: "SLA_FALLBACK",
                      resolvedAt: Date.now(),
                    }
                  : h
              )
            );
          }
        } catch (e) {
          console.error("Mobile telemetry parse error:", e);
        }
      };
    }

    connectWs();
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  // Action dispatcher
  const handleResolve = async (
    holdId: string,
    action: string,
    customText?: string
  ) => {
    setResolvingId(holdId);
    try {
      await resolveHold(holdId, action, customText || "", "MOBILE_COMPANION");
      setHolds((prev) =>
        prev.map((h) =>
          h.id === holdId
            ? {
                ...h,
                status: "RESOLVED",
                resolvedAction: action,
                resolvedAt: Date.now(),
              }
            : h
        )
      );
    } catch (err) {
      console.error("Failed to resolve hold from mobile:", err);
    } finally {
      setResolvingId(null);
    }
  };

  // Voice whisper recording via Scribe STT
  const handleToggleVoiceWhisper = async (holdId: string) => {
    if (isRecording === holdId) {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(null);
    } else {
      // Start recording
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        audioChunksRef.current = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        recorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
          try {
            const sttRes = await transcribeAudioScribe(audioBlob);
            if (sttRes && sttRes.transcription) {
              setCustomWhispers((prev) => ({
                ...prev,
                [holdId]: sttRes.transcription,
              }));
            }
          } catch (sttErr) {
            console.error("Voice whisper STT failed:", sttErr);
          }
          // Stop all mic tracks
          stream.getTracks().forEach((track) => track.stop());
        };

        recorder.start();
        setIsRecording(holdId);
      } catch (micErr) {
        alert("Microphone access denied or unavailable.");
      }
    }
  };

  // Filter active holds (or recently resolved within 8 seconds)
  const displayHolds = holds.filter((h) => {
    if (h.status === "ACTIVE_HOLD") return true;
    if (h.resolvedAt && now - h.resolvedAt < 8000) return true;
    return false;
  });

  return (
    <div className="min-h-screen bg-[#09090b] text-[#f4f4f6] font-sans p-4 flex flex-col justify-between max-w-md mx-auto selection:bg-[#10b981]/30">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#1f1f24]">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 bg-[#16161a] border border-[#2c2c35] rounded-[4px] flex items-center justify-center font-mono text-[11px] font-bold text-[#10b981] shadow-inner">
            VF
          </div>
          <div>
            <span className="font-mono text-sm font-semibold tracking-tight text-[#f4f4f6] block leading-none">
              Voxera Mobile
            </span>
            <span className="text-[10px] text-[#71717a] font-mono">Owner Live Co-Pilot</span>
          </div>
        </div>
        <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-[4px] bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981] font-mono text-[10px]">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              wsConnected ? "bg-[#10b981] animate-pulse" : "bg-[#ef4444]"
            }`}
          />
          <span>{wsConnected ? "LIVE PAIRED" : "RECONNECTING"}</span>
        </div>
      </div>

      {/* Main Container */}
      <div className="my-auto py-4 space-y-4">
        {displayHolds.length === 0 ? (
          /* Radar Pulse Empty State */
          <div className="text-center py-12 px-4 space-y-4">
            <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border border-[#10b981]/20 animate-ping" />
              <div className="absolute inset-2 rounded-full border border-[#10b981]/40 animate-pulse" />
              <div className="w-10 h-10 rounded-full bg-[#10b981]/10 border border-[#10b981] flex items-center justify-center text-[#10b981]">
                <Radio className="w-5 h-5 animate-pulse" />
              </div>
            </div>

            <div className="space-y-1">
              <h3 className="font-mono text-sm font-bold text-[#f4f4f6]">
                Co-Pilot Standing By
              </h3>
              <p className="text-xs text-[#71717a] leading-relaxed max-w-xs mx-auto">
                Listening for ambiguous orders (&lt;0.85) and manager transfer calls in real time. 8.0s auto-fallback active.
              </p>
            </div>

            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-[#16161a] border border-[#27272a] rounded-full text-[10px] font-mono text-[#a1a1aa]">
              <Clock className="w-3 h-3 text-[#10b981]" />
              <span>SLA Clock: 8.0s Fallback</span>
            </div>
          </div>
        ) : (
          /* Active / Intercept Holds */
          displayHolds.map((hold) => {
            const isHumanTransfer = hold.hold_reason === "HUMAN_TRANSFER_REQUEST";
            const expiresAt = hold.expires_at_epoch_ms || Date.now() + 8000;
            const remainingMs = Math.max(0, expiresAt - now);
            const remainingSec = (remainingMs / 1000).toFixed(1);
            const progressPct = Math.min(100, Math.max(0, (remainingMs / 8000) * 100));
            const isResolved = hold.status === "RESOLVED";
            const isExpired = hold.status === "SLA_AUTO_FALLBACK";

            return (
              <div
                key={hold.id}
                className={`p-4 rounded-[8px] bg-[#121216] border transition-all shadow-xl space-y-3 ${
                  isResolved
                    ? "border-[#10b981]/50 bg-[#10b981]/5"
                    : isExpired
                    ? "border-[#ef4444]/50 bg-[#ef4444]/5"
                    : isHumanTransfer
                    ? "border-[#8b5cf6]/60 bg-[#8b5cf6]/5 animate-pulse"
                    : "border-[#f59e0b]/50 bg-[#f59e0b]/5"
                }`}
              >
                {/* Hold Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {isHumanTransfer ? (
                      <span className="font-mono text-xs font-bold text-[#c084fc] flex items-center space-x-1">
                        <PhoneCall className="w-3.5 h-3.5" />
                        <span>TRANSFER REQUEST</span>
                      </span>
                    ) : (
                      <span className="font-mono text-xs font-bold text-[#f4f4f6]">
                        CALL HOLD #{hold.id.slice(-6)}
                      </span>
                    )}
                  </div>

                  {!isResolved && !isExpired ? (
                    <span
                      className={`font-mono text-[10px] px-2 py-0.5 rounded-[4px] font-bold ${
                        Number(remainingSec) <= 3
                          ? "bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/40 animate-ping"
                          : "bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30"
                      }`}
                    >
                      ⏱️ {remainingSec}s SLA
                    </span>
                  ) : (
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded-[4px] bg-[#10b981]/20 text-[#10b981] font-bold">
                      {isResolved ? "RESOLVED" : "SLA EXPIRED"}
                    </span>
                  )}
                </div>

                {/* SLA Progress Bar */}
                {!isResolved && !isExpired && (
                  <div className="w-full bg-[#1e1e24] h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-100 ease-linear ${
                        progressPct < 35
                          ? "bg-[#ef4444]"
                          : progressPct < 65
                          ? "bg-[#f59e0b]"
                          : "bg-[#10b981]"
                      }`}
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                )}

                {/* Caller Utterance Box */}
                <div className="p-2.5 bg-[#09090b]/80 border border-[#27272a] rounded-[6px] text-xs space-y-1">
                  <div className="flex justify-between items-center text-[10px] font-mono text-[#71717a]">
                    <span>Spoken Input:</span>
                    <span className="text-[#a1a1aa] font-semibold">
                      Score: {hold.phonetic_score.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-[#f4f4f6] italic font-serif">
                    &ldquo;{hold.caller_utterance || hold.spoken_entity}&rdquo;
                  </p>
                </div>

                {/* Resolution Options */}
                {isResolved ? (
                  <div className="p-3 bg-[#10b981]/10 border border-[#10b981]/30 rounded-[6px] text-xs font-mono text-[#10b981] flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Injected: {hold.resolvedAction}</span>
                    </div>
                    <span className="text-[10px] text-[#71717a]">Live Agent Speaking</span>
                  </div>
                ) : isExpired ? (
                  <div className="p-3 bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-[6px] text-xs font-mono text-[#ef4444] flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span>8.0s Elapsed — Executed Graceful Clarification</span>
                  </div>
                ) : isHumanTransfer ? (
                  /* Transfer Specific Actions */
                  <div className="space-y-2 pt-1">
                    <div className="text-[10px] font-mono text-[#a1a1aa] uppercase tracking-wider">
                      Owner 1-Tap Action:
                    </div>
                    <button
                      onClick={() =>
                        handleResolve(hold.id, "APPROVE_TRANSFER")
                      }
                      disabled={Boolean(resolvingId)}
                      className="w-full p-3 rounded-[6px] bg-[#10b981] hover:bg-[#059669] text-black font-semibold text-xs transition-all flex items-center justify-center space-x-2 shadow-lg"
                    >
                      <PhoneForwarded className="w-4 h-4" />
                      <span>Approve Live Call Transfer</span>
                    </button>
                    <button
                      onClick={() =>
                        handleResolve(hold.id, "BUSY_CALLBACK")
                      }
                      disabled={Boolean(resolvingId)}
                      className="w-full p-2.5 rounded-[6px] bg-[#1f1f24] hover:bg-[#2c2c35] border border-[#3f3f46] text-[#e4e4e7] font-mono text-xs transition-all flex items-center justify-center space-x-2"
                    >
                      <Clock className="w-3.5 h-3.5 text-[#f59e0b]" />
                      <span>Busy — Lock 10-Min Priority Callback</span>
                    </button>
                  </div>
                ) : (
                  /* Phonetic Ambiguity Candidate Options */
                  <div className="space-y-2 pt-1">
                    <div className="text-[10px] font-mono text-[#a1a1aa] uppercase tracking-wider flex justify-between">
                      <span>1-Tap Disambiguate:</span>
                      <span className="text-[#10b981]">Instant Lock</span>
                    </div>
                    {hold.candidate_1 && (
                      <button
                        onClick={() =>
                          handleResolve(hold.id, "CANDIDATE_1")
                        }
                        disabled={Boolean(resolvingId)}
                        className="w-full p-2.5 rounded-[6px] bg-[#16161a] border border-[#27272a] hover:border-[#10b981] text-left font-mono text-xs transition-all flex justify-between items-center group"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="text-emerald-400 font-bold">1️⃣</span>
                          <span className="font-semibold text-[#f4f4f6] group-hover:text-[#10b981]">
                            {hold.candidate_1.canonical_name}
                          </span>
                        </div>
                        <span className="text-[#10b981] text-[11px] font-bold">
                          {Math.round(hold.candidate_1.probability_pct || (hold.candidate_1.score * 100))}% · ₹
                          {hold.candidate_1.price_inr}
                        </span>
                      </button>
                    )}
                    {hold.candidate_2 && (
                      <button
                        onClick={() =>
                          handleResolve(hold.id, "CANDIDATE_2")
                        }
                        disabled={Boolean(resolvingId)}
                        className="w-full p-2.5 rounded-[6px] bg-[#16161a] border border-[#27272a] hover:border-[#10b981] text-left font-mono text-xs transition-all flex justify-between items-center group"
                      >
                        <div className="flex items-center space-x-2">
                          <span className="text-amber-400 font-bold">2️⃣</span>
                          <span className="font-semibold text-[#f4f4f6] group-hover:text-[#10b981]">
                            {hold.candidate_2.canonical_name}
                          </span>
                        </div>
                        <span className="text-[#a1a1aa] text-[11px]">
                          {Math.round(hold.candidate_2.probability_pct || (hold.candidate_2.score * 100))}% · ₹
                          {hold.candidate_2.price_inr}
                        </span>
                      </button>
                    )}
                  </div>
                )}

                {/* Custom Whisper Input (Only if active) */}
                {!isResolved && !isExpired && (
                  <div className="pt-2 border-t border-[#1f1f24] space-y-2">
                    <div className="flex items-center space-x-1.5">
                      <input
                        type="text"
                        placeholder="Or type custom whisper..."
                        value={customWhispers[hold.id] || ""}
                        onChange={(e) =>
                          setCustomWhispers((prev) => ({
                            ...prev,
                            [hold.id]: e.target.value,
                          }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && customWhispers[hold.id]) {
                            handleResolve(
                              hold.id,
                              "CUSTOM_WHISPER",
                              customWhispers[hold.id]
                            );
                          }
                        }}
                        className="flex-1 bg-[#09090b] border border-[#27272a] rounded-[4px] px-2.5 py-1.5 text-xs text-[#f4f4f6] placeholder-[#52525b] focus:outline-none focus:border-[#10b981]"
                      />
                      <button
                        onClick={() => handleToggleVoiceWhisper(hold.id)}
                        className={`p-2 rounded-[4px] border transition-all ${
                          isRecording === hold.id
                            ? "bg-[#ef4444] border-[#ef4444] text-white animate-pulse"
                            : "bg-[#18181b] border-[#27272a] text-[#a1a1aa] hover:text-[#f4f4f6]"
                        }`}
                        title="Voice Whisper (Scribe STT)"
                      >
                        {isRecording === hold.id ? (
                          <MicOff className="w-3.5 h-3.5" />
                        ) : (
                          <Mic className="w-3.5 h-3.5" />
                        )}
                      </button>
                      <button
                        onClick={() => {
                          if (customWhispers[hold.id]) {
                            handleResolve(
                              hold.id,
                              "CUSTOM_WHISPER",
                              customWhispers[hold.id]
                            );
                          }
                        }}
                        disabled={!customWhispers[hold.id]}
                        className="p-2 bg-[#10b981] hover:bg-[#059669] disabled:opacity-40 text-black rounded-[4px] transition-all"
                      >
                        <Send className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="text-center font-mono text-[10px] text-[#52525b] pt-3 border-t border-[#1f1f24] space-y-1">
        <div>VOXERA MOBILE RUNTIME · DUAL WEBSOCKET SYNC</div>
        <div className="text-[#3f3f46]">Auto-refreshed with real ElevenLabs Active Session</div>
      </div>
    </div>
  );
}
