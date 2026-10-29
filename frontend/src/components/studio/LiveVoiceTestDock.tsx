"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  PhoneCall,
  PhoneOff,
  Activity,
  Radio,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { ConversationProvider, useConversation } from "@elevenlabs/react";
import {
  DomainProfile,
  fetchConvaiSignedUrl,
  verifyCatalogItemTool,
  commitActionTool,
  requestHumanInterventionTool,
  GuardrailVerifyResult,
} from "@/lib/api";

export interface NodeStateTelemetry {
  activeNode: number;
  nodeSubState?: "SPEAKING_GREETING" | "LISTENING" | "VALIDATING" | "DECISION_GATE" | "IDLE";
  spokenEntity?: string;
  guardrailScore?: number;
  guardrailBranch?: "PASS" | "HOLD";
}

interface LiveVoiceTestDockProps {
  activeDomain: DomainProfile | null;
  onNodeStateChange: (state: NodeStateTelemetry) => void;
}

function LiveVoiceInner({
  activeDomain,
  onNodeStateChange,
}: LiveVoiceTestDockProps) {
  const [isConnecting, setIsConnecting] = useState(false);
  const [ttftMs, setTtftMs] = useState<number | null>(null);
  const [waveformBars, setWaveformBars] = useState<number[]>([
    15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15,
  ]);
  const [transcriptStream, setTranscriptStream] = useState<
    Array<{ sender: "agent" | "caller" | "tool"; text: string }>
  >([
    {
      sender: "agent",
      text: activeDomain?.first_message || "Namaste! Aaj aapke liye kya fresh order lagau?",
    },
  ]);
  const [sessionError, setSessionError] = useState<string | null>(null);

  // Turn Latency Stopwatch
  const userTurnEndTimestampRef = useRef<number | null>(null);
  const lastVerificationTokenRef = useRef<string | null>(null);

  // Initialize ElevenLabs useConversation hook
  const conversation = useConversation({
    onConnect: () => {
      setIsConnecting(false);
      setSessionError(null);
      onNodeStateChange({
        activeNode: 1,
        nodeSubState: "SPEAKING_GREETING",
      });
      setTranscriptStream((prev) => [
        ...prev,
        {
          sender: "agent",
          text: `[Call Connected] ${activeDomain?.first_message || "Namaste!"}`,
        },
      ]);
    },
    onDisconnect: () => {
      setIsConnecting(false);
      onNodeStateChange({ activeNode: 1, nodeSubState: "IDLE" });
      setTranscriptStream((prev) => [
        ...prev,
        { sender: "tool", text: "[Call Ended]" },
      ]);
    },
    onError: (err: any) => {
      setIsConnecting(false);
      const errMsg = typeof err === "string" ? err : err?.message || "Conversation error";
      setSessionError(errMsg);
    },
    onModeChange: ({ mode }: { mode: "speaking" | "listening" }) => {
      if (mode === "listening") {
        userTurnEndTimestampRef.current = Date.now();
        onNodeStateChange({ activeNode: 1, nodeSubState: "LISTENING" });
      } else if (mode === "speaking") {
        if (userTurnEndTimestampRef.current) {
          const latency = Date.now() - userTurnEndTimestampRef.current;
          setTtftMs(latency);
          userTurnEndTimestampRef.current = null;
        }
      }
    },
    onMessage: (message: { message: string; source: "user" | "ai" }) => {
      const sender = message.source === "user" ? "caller" : "agent";
      setTranscriptStream((prev) => [
        ...prev.slice(-6),
        { sender, text: message.message },
      ]);
    },
    clientTools: {
      // Real-time Tool Interception: verify_catalog_item
      verify_catalog_item: async (params: any) => {
        const spokenEntity = params?.spoken_entity || "unknown entity";
        const quantity = params?.quantity || 1;
        const modifiers = params?.modifiers || [];

        // 1. Illuminate Node 02 in real time
        onNodeStateChange({
          activeNode: 2,
          nodeSubState: "VALIDATING",
          spokenEntity,
        });

        setTranscriptStream((prev) => [
          ...prev,
          {
            sender: "tool",
            text: `-> tool:verify_catalog_item(spoken="${spokenEntity}", qty=${quantity})`,
          },
        ]);

        if (!activeDomain) return "Domain not loaded.";

        try {
          // 2. Call deterministic phonetic guardrail backend
          const result: GuardrailVerifyResult = await verifyCatalogItemTool({
            domain_id: activeDomain.id,
            spoken_entity: spokenEntity,
            quantity,
            modifiers,
            caller_utterance: params?.caller_utterance || "",
          });

          if (result.verification_token) {
            lastVerificationTokenRef.current = result.verification_token;
          }

          // 3. Illuminate Node 03 (Green Pass or Amber Hold branch)
          const isPass = result.match_type === "DETERMINISTIC_PASS";
          onNodeStateChange({
            activeNode: 3,
            nodeSubState: "DECISION_GATE",
            spokenEntity,
            guardrailScore: result.score,
            guardrailBranch: isPass ? "PASS" : "HOLD",
          });

          setTranscriptStream((prev) => [
            ...prev,
            {
              sender: "tool",
              text: `<- ${result.match_type} (Score: ${result.score.toFixed(2)}) ${
                isPass ? "✅ Mandatory Read-Back" : "⚠️ Whisper Hold Triggered"
              }`,
            },
          ]);

          return result.instruction;
        } catch (toolErr: any) {
          return `Error evaluating guardrail: ${toolErr.message}`;
        }
      },

      // Two-Phase Phase B: commit_verified_action
      commit_verified_action: async (params: any) => {
        if (!activeDomain) return "Domain not loaded.";
        const canonicalName = params?.canonical_name || "Item";
        const totalPrice = params?.total_price_inr || 0;

        setTranscriptStream((prev) => [
          ...prev,
          {
            sender: "tool",
            text: `-> tool:commit_verified_action(item="${canonicalName}", total=₹${totalPrice})`,
          },
        ]);

        try {
          const res = await commitActionTool({
            domain_id: activeDomain.id,
            token: lastVerificationTokenRef.current,
            canonical_name: canonicalName,
            quantity: params?.quantity || 1,
            total_price_inr: totalPrice,
            caller_phone: params?.caller_phone || "+91 98712 44321",
          });

          onNodeStateChange({
            activeNode: 3,
            nodeSubState: "IDLE",
            guardrailBranch: "PASS",
          });

          setTranscriptStream((prev) => [
            ...prev,
            {
              sender: "tool",
              text: `<- 🔒 ${res.status}: ${res.message}`,
            },
          ]);

          return `COMMIT_SUCCESS: ${res.message}. The order is locked in database. Inform the caller politely with confirmation and ready/delivery time.`;
        } catch (err: any) {
          return `COMMIT_FAILED: ${err.message}`;
        }
      },

      // Escalation Interception: request_human_intervention
      request_human_intervention: async (params: any) => {
        const reason = params?.reason || params?.caller_summary || "Caller requested human transfer";
        setTranscriptStream((prev) => [
          ...prev,
          {
            sender: "tool",
            text: `-> tool:request_human_intervention(reason="${reason}")`,
          },
        ]);

        onNodeStateChange({
          activeNode: 3,
          nodeSubState: "DECISION_GATE",
          guardrailBranch: "HOLD",
        });

        if (activeDomain) {
          try {
            await requestHumanInterventionTool({
              domain_id: activeDomain.id,
              reason,
              caller_utterance: params?.caller_utterance || params?.caller_summary || reason,
            });
          } catch (e) {
            console.error("Failed to persist human intervention hold:", e);
          }
        }

        return "ESCALATION_TRIGGERED: Owner phone alerted via push notification. Tell the caller you are checking with the manager on priority.";
      },
      "request human intervention": async (params: any) => {
        const reason = params?.reason || params?.caller_summary || "Caller requested human transfer";
        if (activeDomain) {
          try {
            await requestHumanInterventionTool({
              domain_id: activeDomain.id,
              reason,
              caller_utterance: params?.caller_utterance || params?.caller_summary || reason,
            });
          } catch (e) {
            console.error("Failed to persist human intervention hold:", e);
          }
        }
        return "ESCALATION_TRIGGERED: Owner phone alerted via push notification. Tell the caller you are checking with the manager on priority.";
      },
      human_intervention: async (params: any) => {
        const reason = params?.reason || params?.caller_summary || "Caller requested human transfer";
        if (activeDomain) {
          try {
            await requestHumanInterventionTool({
              domain_id: activeDomain.id,
              reason,
              caller_utterance: params?.caller_utterance || params?.caller_summary || reason,
            });
          } catch (e) {
            console.error("Failed to persist human intervention hold:", e);
          }
        }
        return "ESCALATION_TRIGGERED: Owner phone alerted via push notification. Tell the caller you are checking with the manager on priority.";
      },
    },
  });

  const isCallConnected = conversation.status === "connected";

  // Toggle Live Call
  const handleToggleCall = async () => {
    if (isCallConnected) {
      conversation.endSession();
    } else {
      if (!activeDomain) return;
      setIsConnecting(true);
      setSessionError(null);

      try {
        // Step 1: Request microphone permission
        await navigator.mediaDevices.getUserMedia({ audio: true });

        // Step 2: Fetch real signed WebSocket URL from backend
        const signedData = await fetchConvaiSignedUrl(activeDomain.id);

        // Step 3: Start live session with ElevenLabs
        await conversation.startSession({
          signedUrl: signedData.signed_url,
        });
      } catch (err: any) {
        setIsConnecting(false);
      }
    }
  };

  // Listen for real-time HOLD_RESOLVED and HOLD_SLA_EXPIRED events to bridge into live ElevenLabs session
  useEffect(() => {
    const wsUrl = "ws://127.0.0.1:8000/ws/telemetry";
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket(wsUrl);
      ws.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "HOLD_RESOLVED" || data.type === "HOLD_SLA_EXPIRED") {
            const instruction = data.agent_contextual_instruction;
            const resolvedBy = data.resolved_by || (data.type === "HOLD_SLA_EXPIRED" ? "8s SLA AUTO-FALLBACK" : "CO-PILOT");

            if (instruction) {
              if (data.verification_token) {
                lastVerificationTokenRef.current = data.verification_token;
              }

              setTranscriptStream((prev) => [
                ...prev,
                {
                  sender: "tool",
                  text: `⚡ [CO-PILOT INJECTED VIA ${resolvedBy}]: "${instruction.slice(0, 110)}..."`,
                },
              ]);

              if (isCallConnected && typeof (conversation as any).sendContextualUpdate === "function") {
                await (conversation as any).sendContextualUpdate(instruction);
              }
            }
          }
        } catch (e) {
          console.error("Telemetry bridge error:", e);
        }
      };
    } catch {}
    return () => {
      if (ws) ws.close();
    };
  }, [isCallConnected, conversation]);

  // Real 60fps Web Audio API AnalyserNode connected to caller microphone
  useEffect(() => {
    let animationFrameId: number;
    let audioContext: AudioContext | null = null;
    let analyser: AnalyserNode | null = null;
    let micStream: MediaStream | null = null;

    if (isCallConnected) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          micStream = stream;
          audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const source = audioContext.createMediaStreamSource(stream);
          analyser = audioContext.createAnalyser();
          analyser.fftSize = 32;
          source.connect(analyser);

          const bufferLength = analyser.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);

          const updateWaveform = () => {
            if (!analyser) return;
            analyser.getByteFrequencyData(dataArray);

            const bars: number[] = [];
            for (let i = 0; i < 12; i++) {
              const val = dataArray[i % bufferLength] || 0;
              // Map byte value (0-255) to 15% - 100% height
              const height = Math.max(15, Math.min(100, Math.round((val / 255) * 100)));
              bars.push(height);
            }
            setWaveformBars(bars);
            animationFrameId = requestAnimationFrame(updateWaveform);
          };
          updateWaveform();
        })
        .catch(() => {
          // If mic stream is already locked, use sdk audio frequency fallback
        });
    } else {
      setWaveformBars([15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]);
    }

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      if (micStream) micStream.getTracks().forEach((t) => t.stop());
      if (audioContext) audioContext.close();
    };
  }, [isCallConnected]);

  return (
    <div className="h-[125px] min-h-[125px] w-full bg-[#101013] border-t border-[#1f1f24] px-4 py-2 flex flex-col justify-between font-mono select-none">
      {/* Top Telemetry Row */}
      <div className="flex items-center justify-between text-[11px]">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-[3px] bg-[#16161a] border border-[#1f1f24]">
            <span
              className={`w-2 h-2 rounded-full ${
                isCallConnected
                  ? "bg-[#10b981] animate-ping"
                  : isConnecting
                  ? "bg-[#f59e0b] animate-pulse"
                  : "bg-[#5b5b66]"
              }`}
            />
            <span className="text-[#9494a0] uppercase tracking-wider text-[10px]">
              {isCallConnected
                ? `LIVE SESSION: ${conversation.isSpeaking ? "AGENT SPEAKING" : "LISTENING"}`
                : isConnecting
                ? "PROVISIONING CONVAI..."
                : "RUNTIME: IDLE"}
            </span>
          </div>

          {ttftMs !== null && (
            <div className="flex items-center space-x-1 px-2 py-0.5 rounded-[3px] bg-[#16161a] border border-[#1f1f24] text-[#10b981] text-[10px]">
              <Activity className="w-2.5 h-2.5" />
              <span>TTFT: {ttftMs}ms</span>
            </div>
          )}

          <div className="flex items-center space-x-1 text-[10px] text-[#5b5b66]">
            <span>Model:</span>
            <span className="text-[#9494a0]">eleven_flash_v2_5 (sub-350ms)</span>
          </div>
        </div>

        {/* Start / End Call Button */}
        <button
          onClick={handleToggleCall}
          disabled={isConnecting}
          className={`flex items-center space-x-1.5 px-3.5 py-1 rounded-[4px] text-xs font-semibold transition-all ${
            isCallConnected
              ? "bg-[#ef4444] hover:bg-[#dc2626] text-white shadow-md shadow-[#ef4444]/20"
              : isConnecting
              ? "bg-[#16161a] border border-[#2c2c35] text-[#9494a0]"
              : "bg-[#10b981] hover:bg-[#059669] text-black shadow-md shadow-[#10b981]/20"
          }`}
        >
          {isCallConnected ? (
            <>
              <PhoneOff className="w-3.5 h-3.5" />
              <span>End Call</span>
            </>
          ) : isConnecting ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#f59e0b]" />
              <span>Connecting...</span>
            </>
          ) : (
            <>
              <PhoneCall className="w-3.5 h-3.5" />
              <span>Start Browser Mic Test</span>
            </>
          )}
        </button>
      </div>

      {/* Error Banner if API key or Signed URL fails */}
      {sessionError && (
        <div className="px-2 py-1 bg-[#ef4444]/10 border border-[#ef4444]/30 rounded-[3px] text-[10px] text-[#ef4444] flex items-center justify-between">
          <div className="flex items-center space-x-1.5 truncate">
            <AlertCircle className="w-3 h-3 flex-shrink-0" />
            <span className="truncate">{sessionError}</span>
          </div>
          <button
            onClick={() => setSessionError(null)}
            className="text-[10px] underline ml-2"
          >
            dismiss
          </button>
        </div>
      )}

      {/* Middle & Bottom: Waveform Bars & Live Transcript Feed */}
      <div className="flex items-center space-x-3 h-12 bg-[#09090b] border border-[#1f1f24] rounded-[4px] px-3 py-1">
        {/* Real 60fps Waveform Visualizer */}
        <div className="flex items-center space-x-0.5 h-7 w-24 flex-shrink-0">
          {waveformBars.map((height, idx) => (
            <div
              key={idx}
              className={`w-1 rounded-full transition-all duration-75 ${
                isCallConnected
                  ? conversation.isSpeaking
                    ? "bg-[#38bdf8]"
                    : "bg-[#10b981]"
                  : "bg-[#2c2c35]"
              }`}
              style={{
                height: `${height}%`,
                minHeight: "4px",
              }}
            />
          ))}
        </div>

        <div className="h-6 w-[1px] bg-[#1f1f24]" />

        {/* Streaming Transcript & Tool Invocation Stream */}
        <div className="flex-1 overflow-x-auto whitespace-nowrap text-[11px] text-[#9494a0] flex items-center space-x-2">
          {transcriptStream.slice(-3).map((item, idx) => (
            <span
              key={idx}
              className={`px-2 py-0.5 rounded-[3px] ${
                item.sender === "tool"
                  ? "bg-[#16161a] text-[#10b981] border border-[#10b981]/30 font-semibold"
                  : item.sender === "agent"
                  ? "text-[#f4f4f6]"
                  : "text-[#e4e4e7] bg-[#16161a] border border-[#1f1f24]"
              }`}
            >
              {item.sender === "agent" && (
                <span className="text-[#5b5b66] mr-1">Agent:</span>
              )}
              {item.sender === "caller" && (
                <span className="text-[#5b5b66] mr-1">Caller:</span>
              )}
              {item.text}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

export const LiveVoiceTestDock: React.FC<LiveVoiceTestDockProps> = (props) => {
  return (
    <ConversationProvider>
      <LiveVoiceInner {...props} />
    </ConversationProvider>
  );
};
