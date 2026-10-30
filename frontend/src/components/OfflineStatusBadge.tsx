"use client";

import { useEffect, useState } from "react";

type BadgeState = "online" | "offline" | "syncing";

interface BadgeProps {
  /** Override className for positioning (default: empty). */
  className?: string;
}

export function OfflineStatusBadge({ className = "" }: BadgeProps) {
  const [state, setState] = useState<BadgeState>("online");
  const [pending, setPending] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") return;

    let connUnsub: (() => void) | null = null;
    let outboxUnsub: (() => void) | null = null;

    // Lazy-import to avoid SSR issues
    Promise.all([
      import("@/lib/offline/connectivity"),
      import("@/lib/offline/outbox"),
    ]).then(([conn, outbox]) => {
      // Start monitor (idempotent if already started)
      conn.startConnectivityMonitor();

      connUnsub = conn.subscribe((online) => {
        setState((prev) => {
          // If going offline, clear syncing state
          if (!online) return "offline";
          // If was offline and back online, let outbox subscriber drive
          return prev === "offline" ? "online" : prev;
        });
      });

      outboxUnsub = outbox.subscribe((items) => {
        const pendingItems = items.filter(
          (i) => i.status === "pending" || i.status === "failed"
        );
        const syncingItems = items.filter((i) => i.status === "syncing");
        setPending(pendingItems.length + syncingItems.length);

        setState((prev) => {
          if (prev === "offline") return "offline";
          if (syncingItems.length > 0) return "syncing";
          if (pendingItems.length > 0) return conn.isOnline() ? "syncing" : "offline";
          return conn.isOnline() ? "online" : "offline";
        });
      });
    });

    return () => {
      connUnsub?.();
      outboxUnsub?.();
    };
  }, []);

  const dot =
    state === "online"
      ? "bg-emerald-400"
      : state === "syncing"
      ? "bg-amber-400 animate-pulse"
      : "bg-[#9CA3AF]";

  const label =
    state === "online"
      ? "Online"
      : state === "syncing"
      ? `Syncing ${pending}`
      : "Offline";

  return (
    <div
      suppressHydrationWarning
      className={`hidden sm:flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-[#F7F8FA] border border-[#E9EBEF] text-[11px] font-medium text-[#34373D] select-none ${className}`}
      title={
        state === "syncing"
          ? `${pending} action(s) pending sync`
          : state === "offline"
          ? "App is offline — reads served from cache"
          : "All systems online"
      }
    >
      <span suppressHydrationWarning className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      <span suppressHydrationWarning>{label}</span>
    </div>
  );
}
