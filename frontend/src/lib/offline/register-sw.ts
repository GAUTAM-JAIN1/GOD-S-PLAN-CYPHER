/**
 * Registers the Voxera service worker.
 * Call once from a client component that mounts early in the tree.
 */
export async function registerServiceWorker(): Promise<void> {
  if (typeof window === "undefined") return;
  if (!("serviceWorker" in navigator)) return;

  try {
    const registration = await navigator.serviceWorker.register("/sw.js", {
      scope: "/",
    });
    console.log("[SW] Registered, scope:", registration.scope);

    registration.addEventListener("updatefound", () => {
      const newWorker = registration.installing;
      if (!newWorker) return;
      newWorker.addEventListener("statechange", () => {
        if (
          newWorker.state === "installed" &&
          navigator.serviceWorker.controller
        ) {
          // New content available — could show a toast here in the future
          console.log("[SW] New version available — reload to update.");
        }
      });
    });
  } catch (err) {
    console.warn("[SW] Registration failed:", err);
  }
}

