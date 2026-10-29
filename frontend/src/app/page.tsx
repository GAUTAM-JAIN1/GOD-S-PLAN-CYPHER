"use client";

import React, { useState, useEffect } from "react";
import { TopTelemetryBar, ViewTabMode } from "@/components/TopTelemetryBar";
import { BusinessDemoView } from "@/components/views/BusinessDemoView";
import { DeveloperWorkbenchView } from "@/components/views/DeveloperWorkbenchView";
import { fetchDomains, fetchHealth, DomainProfile, HealthResponse } from "@/lib/api";

export default function WorkbenchPage() {
  const [activeTab, setActiveTab] = useState<ViewTabMode>("main");
  const [domains, setDomains] = useState<DomainProfile[]>([]);
  const [activeDomain, setActiveDomain] = useState<DomainProfile | null>(null);
  const [activeHoldCount, setActiveHoldCount] = useState<number>(0);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);

  // Sync with URL query parameter (?mode=dev, ?mode=main)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const searchParams = new URLSearchParams(window.location.search);
      const mode = searchParams.get("mode") as ViewTabMode;
      if (mode && ["main", "dev"].includes(mode)) {
        setActiveTab(mode);
      }
    }
  }, []);

  const handleTabChange = (newTab: ViewTabMode) => {
    setActiveTab(newTab);
    if (typeof window !== "undefined") {
      const url = new URL(window.location.href);
      url.searchParams.set("mode", newTab);
      window.history.replaceState({}, "", url.toString());
    }
  };

  // Load domains & health check on startup
  useEffect(() => {
    async function loadInitialData() {
      try {
        const [loadedDomains, health] = await Promise.all([
          fetchDomains(),
          fetchHealth().catch(() => null),
        ]);
        setDomains(loadedDomains);
        if (loadedDomains.length > 0) {
          setActiveDomain(loadedDomains[0]);
        }
        if (health) setHealthData(health);
      } catch (err) {
        console.error("Failed to fetch initial workbench data:", err);
      }
    }
    loadInitialData();
  }, []);

  // Connect to live WebSocket telemetry
  useEffect(() => {
    const wsUrl = "ws://127.0.0.1:8000/ws/telemetry";
    let socket: WebSocket | null = null;
    let pingInterval: NodeJS.Timeout | null = null;

    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        setWsConnected(true);
        pingInterval = setInterval(() => {
          if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "PING", timestamp: Date.now() }));
          }
        }, 15000);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "WHISPER_INTERCEPT") {
            setActiveHoldCount((prev) => prev + 1);
          } else if (data.type === "HOLD_RESOLVED") {
            setActiveHoldCount((prev) => Math.max(0, prev - 1));
          }
        } catch (e) {
          console.error("WS message parse error:", e);
        }
      };

      socket.onclose = () => {
        setWsConnected(false);
        if (pingInterval) clearInterval(pingInterval);
      };

      socket.onerror = () => {
        setWsConnected(false);
      };
    } catch {
      setWsConnected(false);
    }

    return () => {
      if (pingInterval) clearInterval(pingInterval);
      if (socket) socket.close();
    };
  }, []);

  const handleDomainUpdated = (updated: DomainProfile) => {
    setActiveDomain(updated);
    setDomains((prev) =>
      prev.map((d) => (d.id === updated.id ? updated : d))
    );
  };

  const handleDomainCreated = (newDomain: DomainProfile) => {
    setDomains((prev) => [newDomain, ...prev.filter((d) => d.id !== newDomain.id)]);
    setActiveDomain(newDomain);
  };

  const handleCreateAgentFocus = () => {
    setActiveTab("main");
    const promptInput = document.querySelector('input[placeholder*="Describe business"]') as HTMLInputElement;
    if (promptInput) {
      promptInput.focus();
      promptInput.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col apple-glass-canvas text-[#151619] overflow-hidden select-none">
      {/* Top Floating Glass Header */}
      <TopTelemetryBar
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        activeDomainSlug={activeDomain?.id || "brew-bite-cafe"}
        activeHoldCount={activeHoldCount}
        wsConnected={wsConnected}
        groqReady={healthData?.keys.groq_configured ?? true}
        elevenlabsReady={healthData?.keys.elevenlabs_configured ?? true}
        liveTtsLatencyMs={348}
        onCreateAgentClick={handleCreateAgentFocus}
      />

      {/* Main Workspace Body with Subtle Monochrome Architectural Lighting */}
      <main className="flex-1 w-full overflow-hidden flex relative">
        {/* Soft daylight monochrome glow diffusions */}
        <div className="pointer-events-none absolute -top-40 -left-40 w-96 h-96 bg-white/60 rounded-full blur-3xl" />
        <div className="pointer-events-none absolute top-1/2 -right-40 w-96 h-96 bg-white/50 rounded-full blur-3xl" />

        {/* MAIN VIEW: Unified 3-Step Journey (Build, Call, Arena Duel) */}
        {activeTab === "main" && (
          <BusinessDemoView
            domains={domains}
            activeDomain={activeDomain}
            onSelectDomain={setActiveDomain}
            onDomainCreated={handleDomainCreated}
          />
        )}

        {/* DEVELOPER VIEW: Structured Deep Inspector */}
        {activeTab === "dev" && (
          <DeveloperWorkbenchView
            domains={domains}
            activeDomain={activeDomain}
            onSelectDomain={setActiveDomain}
            onDomainUpdated={handleDomainUpdated}
          />
        )}
      </main>
    </div>
  );
}
