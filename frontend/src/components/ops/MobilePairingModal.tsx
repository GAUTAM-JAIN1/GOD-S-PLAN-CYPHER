"use client";

import React, { useState, useEffect } from "react";
import QRCode from "qrcode";
import {
  X,
  QrCode,
  Copy,
  Check,
  Send,
  Smartphone,
  Radio,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  BellRing
} from "lucide-react";
import {
  fetchNetworkInfo,
  sendTelegramTestAlert,
  pairTelegramChat,
  sendTelegramTakeoverAlert,
  NetworkInfoResponse
} from "@/lib/api";

interface MobilePairingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MobilePairingModal: React.FC<MobilePairingModalProps> = ({ isOpen, onClose }) => {
  const [networkInfo, setNetworkInfo] = useState<NetworkInfoResponse | null>(null);
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string>("");
  const [copied, setCopied] = useState<boolean>(false);
  const [testAlertSending, setTestAlertSending] = useState<boolean>(false);
  const [takeoverAlertSending, setTakeoverAlertSending] = useState<boolean>(false);
  const [testAlertMessage, setTestAlertMessage] = useState<string | null>(null);
  const [manualChatId, setManualChatId] = useState<string>("");
  const [isPairing, setIsPairing] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    async function loadInfo() {
      try {
        setLoading(true);
        const data = await fetchNetworkInfo();
        if (!isMounted) return;
        setNetworkInfo(data);
        if (data.telegram?.paired_chat_id) {
          setManualChatId(data.telegram.paired_chat_id);
        }

        // Generate high-resolution scannable QR Code
        const qrUrl = await QRCode.toDataURL(data.mobile_copilot_url, {
          margin: 1,
          width: 220,
          color: {
            dark: "#09090b",
            light: "#ffffff",
          },
        });
        if (isMounted) setQrCodeDataUrl(qrUrl);
      } catch (err) {
        console.error("Failed to load network info for pairing:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadInfo();

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (networkInfo?.mobile_copilot_url) {
      navigator.clipboard.writeText(networkInfo.mobile_copilot_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSaveChatId = async () => {
    if (!manualChatId.trim()) return;
    try {
      setIsPairing(true);
      setTestAlertMessage(null);
      await pairTelegramChat(manualChatId.trim());
      const updated = await fetchNetworkInfo();
      setNetworkInfo(updated);
      setTestAlertMessage(`Chat ID ${manualChatId.trim()} saved & permanently paired in SQLite!`);
    } catch (err: any) {
      setTestAlertMessage(`Pairing failed: ${err.message}`);
    } finally {
      setIsPairing(false);
    }
  };

  const handleSendTestAlert = async () => {
    setTestAlertSending(true);
    setTestAlertMessage(null);
    try {
      const res = await sendTelegramTestAlert("⚡ Voxera Test Alert: Co-Pilot is active and connected to your mobile!");
      setTestAlertMessage(res.message);
    } catch (e: any) {
      setTestAlertMessage(e.message || "Failed to send alert.");
    } finally {
      setTestAlertSending(false);
    }
  };

  const handleSendRealTakeoverAlert = async () => {
    setTakeoverAlertSending(true);
    setTestAlertMessage(null);
    try {
      const res = await sendTelegramTakeoverAlert({
        domain_name: "VOXERA Diagnostic Studio",
        caller_info: "+91 98765-43210 (Caller)",
        utterance: "Manager ko phone do, urgent call takeover chahiye!",
        order_summary: "Live Diagnostic Takeover verification with inline interactive buttons",
      });
      setTestAlertMessage(res.message);
    } catch (e: any) {
      setTestAlertMessage(e.message || "Failed to send takeover alert.");
    } finally {
      setTakeoverAlertSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-xl bg-[#101013] border border-[#2c2c35] rounded-[8px] shadow-2xl overflow-hidden font-sans select-none flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1f1f24]">
          <div className="flex items-center space-x-2">
            <Smartphone className="w-4 h-4 text-[#10b981]" />
            <h3 className="text-sm font-semibold text-[#f4f4f6] font-mono tracking-wide uppercase">
              Pair Owner Companion (QR & Telegram)
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-[4px] text-[#9494a0] hover:text-[#f4f4f6] hover:bg-[#16161a] transition-all"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto max-h-[80vh]">
          {/* Method 1: Wi-Fi LAN QR Code */}
          <div className="p-4 rounded-[6px] bg-[#16161a] border border-[#1f1f24] space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 font-mono text-xs font-semibold text-[#f4f4f6]">
                <QrCode className="w-3.5 h-3.5 text-[#10b981]" />
                <span>1. SCAN WI-FI COMPANION QR CODE</span>
              </div>
              <span className="font-mono text-[10px] text-[#10b981] bg-[#10b981]/10 px-2 py-0.5 rounded-[3px] border border-[#10b981]/30">
                LAN IPv4
              </span>
            </div>

            <div className="flex flex-col sm:flex-row items-center sm:space-x-6 space-y-4 sm:space-y-0">
              {/* QR Code Container */}
              <div className="w-[140px] h-[140px] bg-white p-2 rounded-[6px] shadow-md flex items-center justify-center shrink-0">
                {qrCodeDataUrl ? (
                  <img src={qrCodeDataUrl} alt="Pairing QR Code" className="w-full h-full object-contain" />
                ) : (
                  <RefreshCw className="w-6 h-6 text-[#09090b] animate-spin" />
                )}
              </div>

              {/* Instructions & Link */}
              <div className="flex-1 space-y-2 text-xs">
                <p className="text-[#9494a0] leading-relaxed">
                  Connect your phone to the same Wi-Fi network and scan this QR code with your camera. It opens the touch-first <span className="text-[#f4f4f6] font-mono font-semibold">/mobile-copilot</span> PWA instantly.
                </p>

                <div className="pt-1">
                  <div className="text-[10px] font-mono text-[#5b5b66] uppercase mb-1">
                    Direct LAN IPv4 URL:
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      readOnly
                      value={networkInfo?.mobile_copilot_url || "Detecting LAN IP..."}
                      className="flex-1 bg-[#09090b] border border-[#2c2c35] rounded-[4px] px-2.5 py-1.5 font-mono text-[11px] text-[#f4f4f6] outline-none"
                    />
                    <button
                      onClick={handleCopy}
                      className="px-3 py-1.5 rounded-[4px] bg-[#1f1f24] hover:bg-[#2c2c35] text-[#f4f4f6] font-mono text-xs flex items-center space-x-1 transition-all border border-[#2c2c35]"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-[#10b981]" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? "Copied" : "Copy"}</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Method 2: Localhost Telegram Bot Service with Diagnostic Bar */}
          <div className="p-4 rounded-[6px] bg-[#16161a] border border-[#1f1f24] space-y-4 font-mono">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-xs font-semibold text-[#f4f4f6]">
                <Radio className="w-3.5 h-3.5 text-[#3b82f6] animate-pulse" />
                <span>2. TELEGRAM BOT PUSH & CALL TAKEOVER DISPATCHER</span>
              </div>
              <span
                className={`text-[10px] px-2 py-0.5 rounded-[3px] border ${
                  networkInfo?.telegram?.paired_chat_id
                    ? "bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30"
                    : networkInfo?.telegram?.configured
                    ? "bg-[#f59e0b]/10 text-[#f59e0b] border-[#f59e0b]/30"
                    : "bg-[#71717a]/10 text-[#71717a] border-[#71717a]/30"
                }`}
              >
                {networkInfo?.telegram?.paired_chat_id
                  ? "PAIRED & PERSISTED"
                  : networkInfo?.telegram?.configured
                  ? "AWAITING /START"
                  : "UNCONFIGURED"}
              </span>
            </div>

            {/* Live Diagnostic Bar */}
            <div className="p-3 bg-[#09090b] border border-[#2c2c35] rounded-[4px] text-[11px] space-y-1.5">
              <div className="flex items-center justify-between font-mono">
                <span className="text-[#9494a0]">Bot Status:</span>
                <span className={networkInfo?.telegram?.configured ? "text-[#10b981] font-semibold" : "text-[#ef4444]"}>
                  {networkInfo?.telegram?.configured
                    ? `Valid (@${networkInfo?.telegram?.bot_username || "voxera_bot"})`
                    : "Not Configured (.env missing token)"}
                </span>
              </div>
              <div className="flex items-center justify-between font-mono">
                <span className="text-[#9494a0]">Paired Chat ID:</span>
                <span className={networkInfo?.telegram?.paired_chat_id ? "text-[#10b981] font-bold" : "text-[#f59e0b]"}>
                  {networkInfo?.telegram?.paired_chat_id || "None (Send /start or enter below)"}
                </span>
              </div>
            </div>

            {/* Manual Chat ID Input */}
            <div className="space-y-1.5">
              <div className="text-[10px] font-mono text-[#5b5b66] uppercase">
                Manual Chat ID Configuration (Auto-Persists in SQLite):
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={manualChatId}
                  onChange={(e) => setManualChatId(e.target.value)}
                  placeholder="Enter Telegram Chat ID (e.g. 521876543)"
                  className="flex-1 bg-[#09090b] border border-[#2c2c35] rounded-[4px] px-2.5 py-1.5 font-mono text-xs text-[#f4f4f6] placeholder-[#5b5b66] outline-none focus:border-[#3b82f6]"
                />
                <button
                  onClick={handleSaveChatId}
                  disabled={isPairing || !manualChatId.trim()}
                  className="px-3 py-1.5 rounded-[4px] bg-[#10b981]/20 hover:bg-[#10b981]/30 text-[#10b981] font-mono text-xs border border-[#10b981]/40 disabled:opacity-40 transition-all"
                >
                  {isPairing ? "Saving..." : "Save Chat ID"}
                </button>
              </div>
            </div>

            {/* Test Action Buttons */}
            <div className="space-y-2 pt-1">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleSendRealTakeoverAlert}
                  disabled={takeoverAlertSending || !networkInfo?.telegram?.configured}
                  className="px-3.5 py-1.5 rounded-[4px] bg-[#ef4444]/20 border border-[#ef4444]/40 hover:bg-[#ef4444]/30 text-[#ef4444] text-xs font-mono flex items-center space-x-1.5 transition-all disabled:opacity-40"
                >
                  <BellRing className="w-3.5 h-3.5" />
                  <span>{takeoverAlertSending ? "Dispatching Takeover..." : "🚨 Send Real Test Takeover Alert"}</span>
                </button>

                <button
                  onClick={handleSendTestAlert}
                  disabled={testAlertSending || !networkInfo?.telegram?.configured}
                  className="px-3 py-1.5 rounded-[4px] bg-[#3b82f6]/20 border border-[#3b82f6]/40 hover:bg-[#3b82f6]/30 text-[#3b82f6] text-xs font-mono flex items-center space-x-1.5 transition-all disabled:opacity-40"
                >
                  <span>{testAlertSending ? "Sending..." : "Send Simple Ping Alert"}</span>
                </button>
              </div>

              {testAlertMessage && (
                <div className="p-2 rounded-[4px] bg-[#09090b] border border-[#2c2c35] text-[11px] font-mono text-[#10b981]">
                  {testAlertMessage}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 bg-[#09090b] border-t border-[#1f1f24] flex items-center justify-between font-mono text-[11px] text-[#5b5b66]">
          <span>Voxera Industrial Co-Pilot Runtime</span>
          <button
            onClick={onClose}
            className="px-3 py-1 rounded-[4px] bg-[#16161a] hover:bg-[#1f1f24] text-[#f4f4f6] text-xs transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
