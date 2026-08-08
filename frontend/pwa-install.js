(() => {
  "use strict";

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("/service-worker.js")
        .then((registration) => {
          console.log("FarmLink PWA service worker registered:", registration.scope);
        })
        .catch((error) => {
          console.error("FarmLink PWA service worker registration failed:", error);
        });
    });
  }

  let deferredInstallPrompt = null;

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    document.documentElement.classList.add("pwa-install-available");
  });

  window.addEventListener("appinstalled", () => {
    deferredInstallPrompt = null;
    document.documentElement.classList.remove("pwa-install-available");
    console.log("FarmLink installed as an app.");
  });

  // Makes installation available to future UI buttons without altering current layout.
  window.FarmLinkPWA = {
    canInstall() {
      return Boolean(deferredInstallPrompt);
    },
    async install() {
      if (!deferredInstallPrompt) return { outcome: "unavailable" };
      deferredInstallPrompt.prompt();
      const choice = await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      return choice;
    }
  };
})();
