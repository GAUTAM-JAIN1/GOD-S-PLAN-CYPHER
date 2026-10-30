"use client";

import { useEffect } from "react";
import { registerServiceWorker } from "@/lib/offline/register-sw";

/**
 * Mounts once in layout.tsx to register the service worker.
 * Renders nothing — purely a side-effect component.
 */
export function ServiceWorkerRegistrar() {
  useEffect(() => {
    registerServiceWorker();
  }, []);
  return null;
}

