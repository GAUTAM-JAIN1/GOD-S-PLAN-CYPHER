"use client";

import React, { useState, useRef } from "react";
import {
  Mic,
  MicOff,
  Upload,
  FileText,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Radio,
  Sliders,
  CloudUpload,
} from "lucide-react";
import {
  DomainProfile,
  compileDomain,
  uploadCatalogPdf,
  transcribeAudioScribe,
  liveRefineAgent,
  provisionElevenLabsAgent,
} from "@/lib/api";

interface AgentSpecPaneProps {
  domains: DomainProfile[];
  activeDomain: DomainProfile | null;
  onSelectDomain: (domain: DomainProfile) => void;
  onDomainUpdated: (updated: DomainProfile) => void;
}

export const AgentSpecPane: React.FC<AgentSpecPaneProps> = ({
  domains,
  activeDomain,
  onSelectDomain,
  onDomainUpdated,
}) => {
  const [ownerPrompt, setOwnerPrompt] = useState(
    activeDomain?.system_prompt || ""
  );
  const [businessName, setBusinessName] = useState(activeDomain?.name || "");
  const [domainType, setDomainType] = useState(
    activeDomain?.domain_type || "orders_reservations"
  );
  const [parsedPdfText, setParsedPdfText] = useState("");
  const [pdfMeta, setPdfMeta] = useState<{ filename: string; pages: number } | null>(
    null
  );

  // Scribe STT Voice Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [sttStatus, setSttStatus] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Compilation & Refine states
  const [isCompiling, setIsCompiling] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [isProvisioning, setIsProvisioning] = useState(false);
  const [refineInput, setRefineInput] = useState("");
  const [diffLogs, setDiffLogs] = useState<string[]>([]);
  const [notification, setNotification] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);

  // Sync state when active domain changes
  React.useEffect(() => {
    if (activeDomain) {
      setOwnerPrompt(activeDomain.system_prompt);
      setBusinessName(activeDomain.name);
      setDomainType(activeDomain.domain_type);
      setDiffLogs([]);
    }
  }, [activeDomain]);

  // Handle Voice Recording via Scribe STT
  const toggleRecording = async () => {
    if (isRecording) {
      // Stop recording
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunksRef.current = [];
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, {
            type: "audio/wav",
          });
          setSttStatus("Transcribing via ElevenLabs scribe_v1...");
          try {
            const res = await transcribeAudioScribe(audioBlob);
            if (res.success && res.transcription) {
              setOwnerPrompt((prev) =>
                prev ? `${prev}\n${res.transcription}` : res.transcription
              );
              setSttStatus(
                `Transcribed (${Math.round(res.confidence * 100)}% conf via ${res.engine})`
              );
              setTimeout(() => setSttStatus(null), 6000);
            } else {
              setSttStatus(`STT Notice: ${res.error || "No speech detected"}`);
            }
          } catch (err) {
            setSttStatus("Voice transcription failed to reach backend.");
          }
          // Stop mic tracks
          stream.getTracks().forEach((track) => track.stop());
        };

        mediaRecorder.start();
        setIsRecording(true);
        setSttStatus("Listening... Speak your business rules");
      } catch (err) {
        setNotification({
          type: "error",
          text: "Microphone access denied or not available.",
        });
      }
    }
  };

  // Handle PDF Catalog Upload
  const handlePdfUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setNotification({ type: "info", text: `Parsing ${file.name}...` });
    try {
      const res = await uploadCatalogPdf(file);
      if (res.success) {
        setParsedPdfText(res.extracted_text);
        setPdfMeta({ filename: res.filename, pages: res.page_count });
        setNotification({
          type: "success",
          text: `Extracted ${res.page_count} pages (~${res.preview_items_detected} catalog items detected).`,
        });
      } else {
        setNotification({
          type: "error",
          text: res.error || "Failed to extract PDF.",
        });
      }
    } catch {
      setNotification({ type: "error", text: "PDF upload network error." });
    }
  };

  // Compile Architecture via Groq Llama-3.3-70b
  const handleCompile = async () => {
    if (!businessName.trim()) {
      setNotification({
        type: "error",
        text: "Please provide a Business Name.",
      });
      return;
    }

    setIsCompiling(true);
    setNotification(null);
    try {
      const res = await compileDomain({
        domain_id: activeDomain?.id,
        business_name: businessName,
        domain_type: domainType,
        owner_instructions: ownerPrompt,
        parsed_catalog_text: parsedPdfText,
      });

      if (res.success) {
        const updatedDomain: DomainProfile = {
          id: res.domain_id,
          name: businessName,
          domain_type: domainType,
          tagline: `Compiled by Groq (${res.catalog_items.length} items)`,
          system_prompt: res.system_prompt,
          first_message: res.first_message,
          voice_id: activeDomain?.voice_id || "21m00Tcm4TlvDq8ikWAM",
          language_code: "hi-IN",
          turn_timeout_ms: 420,
          catalog_items: res.catalog_items,
          strict_policies: res.strict_policies,
          elevenlabs_agent_id: activeDomain?.elevenlabs_agent_id,
        };
        onDomainUpdated(updatedDomain);
        setOwnerPrompt(res.system_prompt);
        setNotification({
          type: "success",
          text: `Compiled! ${res.catalog_items.length} catalog items & ${res.strict_policies.length} strict guardrails locked.`,
        });
      } else {
        setNotification({
          type: "error",
          text: res.error || "Groq compilation failed.",
        });
      }
    } catch (err) {
      setNotification({
        type: "error",
        text: "Compilation error connecting to backend.",
      });
    } finally {
      setIsCompiling(false);
    }
  };

  // Handle Prompt-Based Live Refine
  const handleLiveRefine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refineInput.trim() || !activeDomain) return;

    setIsRefining(true);
    try {
      const res = await liveRefineAgent(activeDomain.id, refineInput);
      if (res.success) {
        setDiffLogs((prev) => [...res.diff_applied, ...prev]);
        setOwnerPrompt(res.updated_system_prompt);
        onDomainUpdated({
          ...activeDomain,
          system_prompt: res.updated_system_prompt,
          first_message: res.updated_first_message,
        });
        setRefineInput("");
      } else {
        setNotification({
          type: "error",
          text: res.error || "Failed to refine prompt.",
        });
      }
    } catch {
      setNotification({ type: "error", text: "Refine request failed." });
    } finally {
      setIsRefining(false);
    }
  };

  // Provision Agent to ElevenLabs
  const handleProvision = async () => {
    if (!activeDomain) return;
    setIsProvisioning(true);
    try {
      const res = await provisionElevenLabsAgent(activeDomain.id);
      if (res.success && res.agent_id) {
        onDomainUpdated({
          ...activeDomain,
          elevenlabs_agent_id: res.agent_id,
        });
        setNotification({
          type: "success",
          text: `Live ElevenLabs Agent Synced! ID: ${res.agent_id}`,
        });
      } else {
        setNotification({
          type: res.status === "API_KEY_REQUIRED" ? "info" : "error",
          text: res.message,
        });
      }
    } catch {
      setNotification({
        type: "error",
        text: "Provisioning network request failed.",
      });
    } finally {
      setIsProvisioning(false);
    }
  };

  return (
    <div className="w-[340px] min-w-[340px] h-full bg-[#101013] border-r border-[#1f1f24] flex flex-col justify-between select-none">
      {/* Top Section: Domain Pills & Configuration */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3.5 pb-28 space-y-3.5">
        {/* Pane Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sliders className="w-3.5 h-3.5 text-[#9494a0]" />
            <h2 className="text-xs font-semibold text-[#f4f4f6] uppercase tracking-wider font-mono">
              Agent Specification
            </h2>
          </div>
          <span className="font-mono text-[10px] text-[#5b5b66]">MOD-01</span>
        </div>

        {/* Domain Starter Pills */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-medium text-[#9494a0] block">
            Domain Starter Templates
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            {domains.map((dom) => {
              const isSelected = activeDomain?.id === dom.id;
              return (
                <button
                  key={dom.id}
                  onClick={() => onSelectDomain(dom)}
                  className={`text-left px-2.5 py-1.5 rounded-[4px] border transition-all text-xs ${
                    isSelected
                      ? "bg-[#16161a] border-[#2c2c35] text-[#f4f4f6] shadow-sm font-medium"
                      : "bg-[#09090b] border-[#1f1f24] text-[#9494a0] hover:border-[#2c2c35] hover:text-[#f4f4f6]"
                  }`}
                >
                  <div className="truncate font-medium">{dom.name}</div>
                  <div className="font-mono text-[9px] text-[#5b5b66] truncate uppercase">
                    {dom.domain_type.replace("_", " ")}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Business Name & Domain Type Input */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-medium text-[#9494a0] block">
            Active Business Entity
          </label>
          <input
            type="text"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
            className="w-full bg-[#09090b] border border-[#1f1f24] rounded-[4px] px-2.5 py-1.5 text-xs text-[#f4f4f6] focus:outline-none focus:border-[#2c2c35] font-medium"
            placeholder="e.g. Brew & Bite Cafe"
          />
        </div>

        {/* Natural Language / Voice Prompt Box */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-[11px] font-medium text-[#9494a0]">
              Business Rules & Conversational Laws
            </label>
            {/* Scribe STT Mic Button */}
            <button
              onClick={toggleRecording}
              className={`flex items-center space-x-1.5 px-2 py-0.5 rounded-[3px] border font-mono text-[10px] transition-all ${
                isRecording
                  ? "bg-[#ef4444]/20 border-[#ef4444] text-[#ef4444] animate-pulse"
                  : "bg-[#16161a] border-[#1f1f24] text-[#9494a0] hover:text-[#f4f4f6]"
              }`}
              title="Record voice rules with ElevenLabs Scribe STT"
            >
              {isRecording ? (
                <>
                  <MicOff className="w-3 h-3 text-[#ef4444]" />
                  <span>Recording</span>
                </>
              ) : (
                <>
                  <Mic className="w-3 h-3 text-[#9494a0]" />
                  <span>Scribe Mic</span>
                </>
              )}
            </button>
          </div>

          {/* Scribe STT Status Bar */}
          {sttStatus && (
            <div className="px-2 py-1 rounded-[3px] bg-[#16161a] border border-[#1f1f24] text-[10px] font-mono text-[#10b981] flex items-center space-x-1.5">
              <Sparkles className="w-2.5 h-2.5 flex-shrink-0" />
              <span className="truncate">{sttStatus}</span>
            </div>
          )}

          <textarea
            rows={5}
            value={ownerPrompt}
            onChange={(e) => setOwnerPrompt(e.target.value)}
            className="w-full bg-[#09090b] border border-[#1f1f24] rounded-[4px] p-2.5 text-[11px] text-[#f4f4f6] font-mono focus:outline-none focus:border-[#2c2c35] resize-none leading-relaxed"
            placeholder="Speak or type rules... (e.g. 'Speak Hinglish, read back all orders with total price, no verbal discounts allowed')"
          />
        </div>

        {/* PDF Catalog Upload */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-medium text-[#9494a0] flex items-center justify-between">
            <span>RAG Document / Menu Sheet</span>
            {pdfMeta && (
              <span className="text-[10px] text-[#10b981] font-mono">
                {pdfMeta.pages} pages extracted
              </span>
            )}
          </label>

          <label className="flex items-center justify-center space-x-2 w-full p-2 bg-[#09090b] border border-dashed border-[#1f1f24] hover:border-[#2c2c35] rounded-[4px] cursor-pointer transition-all">
            <Upload className="w-3.5 h-3.5 text-[#5b5b66]" />
            <span className="text-[11px] text-[#9494a0] truncate font-mono">
              {pdfMeta ? pdfMeta.filename : "Upload PDF (Menu / Rate Card)"}
            </span>
            <input
              type="file"
              accept=".pdf"
              onChange={handlePdfUpload}
              className="hidden"
            />
          </label>
        </div>

        {/* Voice Selection Dropdown */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-medium text-[#9494a0] flex justify-between items-center">
            <span>Conversational Voice Profile</span>
            <span className="text-[10px] text-[#10b981] font-mono">Flash v2.5 / Multi v2</span>
          </label>
          <select
            value={activeDomain?.voice_id || "21m00Tcm4TlvDq8ikWAM"}
            onChange={(e) => {
              if (activeDomain) {
                onDomainUpdated({ ...activeDomain, voice_id: e.target.value });
              }
            }}
            className="w-full bg-[#09090b] border border-[#1f1f24] rounded-[4px] px-2.5 py-1.5 text-xs text-[#f4f4f6] font-mono focus:outline-none focus:border-[#2c2c35] cursor-pointer"
          >
            <option value="21m00Tcm4TlvDq8ikWAM">Rachel — Calm & Professional Receptionist</option>
            <option value="AZnzlk1XvdvUeBnXmlld">Domi — Energetic Front Desk (Indian/Global)</option>
            <option value="EXAVITQu4vr4xnSDxMaL">Bella — Warm & Reassuring Host</option>
            <option value="ErXwobaYiN019PkySvjV">Antoni — Sharp Executive Advisor</option>
          </select>
        </div>

        {/* Configuration Summary Strip */}
        <div className="p-2 bg-[#09090b] border border-[#1f1f24] rounded-[4px] space-y-1 font-mono text-[10px] text-[#9494a0]">
          <div className="flex justify-between">
            <span className="text-[#5b5b66]">Language Code:</span>
            <span className="text-[#f4f4f6]">
              {activeDomain?.language_code || "hi-IN (Hinglish)"}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#5b5b66]">Barge-In Timeout:</span>
            <span className="text-[#10b981]">
              {activeDomain?.turn_timeout_ms || 420}ms
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#5b5b66]">Catalog Items:</span>
            <span className="text-[#f4f4f6]">
              {activeDomain?.catalog_items.length || 0} Canonical Entities
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-[#5b5b66]">ElevenLabs Status:</span>
            <span
              className={
                activeDomain?.elevenlabs_agent_id
                  ? "text-[#10b981]"
                  : "text-[#f59e0b]"
              }
            >
              {activeDomain?.elevenlabs_agent_id
                ? `Active (${activeDomain.elevenlabs_agent_id.slice(0, 8)}...)`
                : "Not Provisioned"}
            </span>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div
            className={`p-2 rounded-[4px] text-xs font-mono flex items-start space-x-2 ${
              notification.type === "success"
                ? "bg-[#10b981]/10 border border-[#10b981]/30 text-[#10b981]"
                : notification.type === "error"
                ? "bg-[#ef4444]/10 border border-[#ef4444]/30 text-[#ef4444]"
                : "bg-[#16161a] border border-[#1f1f24] text-[#9494a0]"
            }`}
          >
            {notification.type === "success" ? (
              <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            )}
            <span className="leading-tight">{notification.text}</span>
          </div>
        )}

        {/* Action Buttons: Compile & Provision */}
        <div className="grid grid-cols-2 gap-2 pt-1">
          <button
            onClick={handleCompile}
            disabled={isCompiling}
            className="flex items-center justify-center space-x-1.5 py-1.5 px-3 bg-[#e4e4e7] hover:bg-[#ffffff] text-[#09090b] rounded-[4px] text-xs font-semibold transition-all shadow-sm disabled:opacity-50"
          >
            {isCompiling ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Compiling...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Compile Architecture</span>
              </>
            )}
          </button>

          <button
            onClick={handleProvision}
            disabled={isProvisioning}
            className="flex items-center justify-center space-x-1.5 py-1.5 px-3 bg-[#16161a] hover:bg-[#1c1c21] text-[#f4f4f6] border border-[#2c2c35] rounded-[4px] text-xs font-medium transition-all disabled:opacity-50"
          >
            {isProvisioning ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <CloudUpload className="w-3.5 h-3.5 text-[#9494a0]" />
            )}
            <span>Sync ConvAI</span>
          </button>
        </div>
      </div>

      {/* Bottom Section: Prompt-Based Live Refine Dock */}
      <div className="shrink-0 p-3 bg-[#0c0c0f] border-t border-[#1f1f24] space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#10b981]" />
            <span className="text-[10px] font-mono font-medium text-[#9494a0] uppercase tracking-wider">
              Prompt-Based Live Refine
            </span>
          </div>
          <span className="text-[9px] font-mono text-[#5b5b66]">Instant Diff</span>
        </div>

        {/* Refine Diff Logs Display */}
        {diffLogs.length > 0 && (
          <div className="max-h-20 overflow-y-auto space-y-1 font-mono text-[10px] bg-[#09090b] p-1.5 rounded-[3px] border border-[#1f1f24]">
            {diffLogs.map((log, idx) => (
              <div key={idx} className="text-[#10b981] flex items-center space-x-1">
                <span>{log}</span>
              </div>
            ))}
          </div>
        )}

        {/* Refine Input Form */}
        <form onSubmit={handleLiveRefine} className="relative">
          <input
            type="text"
            value={refineInput}
            onChange={(e) => setRefineInput(e.target.value)}
            disabled={isRefining}
            placeholder="e.g. Keep greeting under 8 words and ask for pickup time..."
            className="w-full bg-[#16161a] border border-[#1f1f24] rounded-[4px] pl-2.5 pr-8 py-1.5 text-[11px] text-[#f4f4f6] font-mono focus:outline-none focus:border-[#2c2c35] placeholder:text-[#5b5b66]"
          />
          <button
            type="submit"
            disabled={isRefining || !refineInput.trim()}
            className="absolute right-1 top-1 h-[22px] w-[22px] bg-[#1f1f24] hover:bg-[#2c2c35] text-[#e4e4e7] rounded-[3px] flex items-center justify-center transition-all disabled:opacity-30"
          >
            {isRefining ? (
              <RefreshCw className="w-2.5 h-2.5 animate-spin" />
            ) : (
              <ArrowRight className="w-2.5 h-2.5" />
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
