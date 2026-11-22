/**
 * Telegram WebApp helpers — init, theme, expand, start_param
 */
window.NOVA_TG = (function () {
  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

  function init() {
    if (!tg) return { ready: false, user: null, startParam: null };
    try {
      tg.ready();
      tg.expand();
      if (tg.setHeaderColor) tg.setHeaderColor("#0a0a0f");
      if (tg.setBackgroundColor) tg.setBackgroundColor("#0a0a0f");
    } catch (e) {
      console.warn("TG init", e);
    }
    const user = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user : null;
    const startParam = tg.initDataUnsafe && tg.initDataUnsafe.start_param
      ? tg.initDataUnsafe.start_param
      : null;
    return {
      ready: true,
      user,
      startParam,
      initData: tg.initData || "",
      platform: tg.platform || "unknown",
      close: () => { try { tg.close(); } catch (_) {} },
      sendData: (payload) => {
        try {
          if (typeof payload !== "string") payload = JSON.stringify(payload);
          tg.sendData(payload);
        } catch (e) {
          console.warn("sendData failed", e);
        }
      },
      haptic: (type) => {
        try {
          if (tg.HapticFeedback) {
            if (type === "success") tg.HapticFeedback.notificationOccurred("success");
            else if (type === "error") tg.HapticFeedback.notificationOccurred("error");
            else tg.HapticFeedback.impactOccurred("light");
          }
        } catch (_) {}
      },
    };
  }

  return { init };
})();
