/**
 * Reward / unlock overlay
 * - required_ads = 1 for single file, 3 for Send All / selected multi
 * - Each completed ad calls server mark_verified (or AdsGram Reward URL)
 * - Client is never sole proof; server tracks ads_completed
 */
window.NOVA_REWARD = (function () {
  let sessionId = null;
  let pollTimer = null;
  let adController = null;
  let requiredAds = 1;
  let adsCompleted = 0;

  function overlay() {
    return document.getElementById("reward-overlay");
  }
  function statusEl() {
    return document.getElementById("reward-status");
  }

  function setStatus(text, cls) {
    const el = statusEl();
    if (!el) return;
    el.textContent = text;
    el.className = "reward-status" + (cls ? " " + cls : "");
  }

  function progressLabel() {
    return `Ad ${Math.min(adsCompleted + 1, requiredAds)} of ${requiredAds}`;
  }

  function show(session) {
    sessionId = session && (session.session_id || session.id) ? (session.session_id || session.id) : null;
    requiredAds = Math.max(1, parseInt((session && session.required_ads) || 1, 10) || 1);
    adsCompleted = Math.max(0, parseInt((session && session.ads_completed) || 0, 10) || 0);
    const title = document.getElementById("reward-title");
    const desc = document.getElementById("reward-desc");
    if (title) title.textContent = (session && session.title) || "Unlock required";
    if (desc) {
      desc.textContent = (session && session.description) ||
        (requiredAds > 1
          ? `Complete ${requiredAds} reward ads. Each is verified on the server before files are released.`
          : "Complete 1 reward ad. Completion is verified on the server.");
    }
    setStatus((session && session.status_label) || (session && session.status) || progressLabel());
    const ov = overlay();
    if (ov) {
      ov.classList.remove("hidden");
      ov.setAttribute("aria-hidden", "false");
    }
  }

  function hide() {
    stopPoll();
    const ov = overlay();
    if (ov) {
      ov.classList.add("hidden");
      ov.setAttribute("aria-hidden", "true");
    }
  }

  function stopPoll() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function startPoll() {
    stopPoll();
    if (!sessionId) return;
    pollTimer = setInterval(async () => {
      try {
        const data = await window.NOVA_API.operations.get(sessionId);
        if (!data) return;
        requiredAds = Math.max(1, parseInt(data.required_ads || requiredAds, 10));
        adsCompleted = Math.max(0, parseInt(data.ads_completed || 0, 10));
        const st = (data.status || "").toLowerCase();
        if (st === "verified" || st === "delivered" || st === "operation_queued") {
          setStatus(data.status_label || "Verified — return to the bot for your file(s).", "verified");
          stopPoll();
          if (window.NOVA_TG_CTX && window.NOVA_TG_CTX.sendData) {
            window.NOVA_TG_CTX.sendData({ type: "reward_status", session_id: sessionId, status: st });
          }
          setTimeout(() => {
            if (window.NOVA_TG_CTX && window.NOVA_TG_CTX.close) window.NOVA_TG_CTX.close();
          }, 1400);
        } else if (st === "failed" || st === "expired") {
          setStatus(data.status_label || data.status, "failed");
          stopPoll();
        } else {
          setStatus(data.status_label || progressLabel());
        }
      } catch (e) {
        console.warn("poll", e);
      }
    }, 2500);
  }

  function loadAdsGram(blockId) {
    return new Promise((resolve, reject) => {
      if (window.Adsgram) {
        resolve(window.Adsgram);
        return;
      }
      const s = document.createElement("script");
      s.src = "https://sad.adsgram.ai/js/sad.min.js";
      s.async = true;
      s.onload = () => resolve(window.Adsgram);
      s.onerror = () => reject(new Error("AdsGram SDK failed to load"));
      document.head.appendChild(s);
    });
  }

  async function reportAdDone() {
    if (!sessionId || !window.NOVA_API || !window.NOVA_API.operations) return null;
    try {
      if (window.NOVA_API.operations.markVerified) {
        return await window.NOVA_API.operations.markVerified(sessionId);
      }
    } catch (e) {
      console.warn("markVerified", e);
    }
    return null;
  }

  async function showAd() {
    const blockId = (window.NOVA_CONFIG && window.NOVA_CONFIG.ADSGRAM_BLOCK_ID) || "";
    setStatus(progressLabel() + " — loading…");
    if (!blockId) {
      // Dev / test path: each click counts as one verified ad step on the server
      setStatus(progressLabel() + " — test verify…");
      const res = await reportAdDone();
      if (res && res.complete) {
        setStatus("Verified — return to the bot.", "verified");
        startPoll();
      } else if (res) {
        adsCompleted = res.ads_completed || adsCompleted + 1;
        requiredAds = res.required_ads || requiredAds;
        setStatus(`Ad ${adsCompleted}/${requiredAds} recorded. Tap again for the next.`);
      } else {
        setStatus("Ad provider not configured. Set ADSGRAM_BLOCK_ID or enable server test mark.", "failed");
      }
      return;
    }
    try {
      const Adsgram = await loadAdsGram(blockId);
      adController = Adsgram.init({ blockId: String(blockId) });
      adController.show().then(async () => {
        setStatus("Checking server…");
        // Prefer AdsGram Reward URL → mark_verified; also try client notify + poll
        await reportAdDone();
        startPoll();
      }).catch(() => {
        setStatus("Ad closed or unavailable. You can retry.", "failed");
      });
    } catch (e) {
      console.error(e);
      setStatus("Could not load ad provider.", "failed");
    }
  }

  function bindUI() {
    const btn = document.getElementById("btn-watch-ad");
    const close = document.getElementById("btn-reward-close");
    if (btn) {
      btn.addEventListener("click", () => showAd());
      const label = btn.querySelector("span") || btn;
      // keep original label; progress is in status
    }
    if (close) close.addEventListener("click", () => hide());
  }

  async function maybeOpenFromStartParam(startParam) {
    if (!startParam) return false;
    const m = String(startParam).match(/^(?:op|reward|session)[_-](.+)$/i);
    if (!m) return false;
    const sid = m[1];
    try {
      const data = await window.NOVA_API.operations.get(sid);
      show(data || { session_id: sid, title: "Unlock required", status: "Pending", required_ads: 1 });
      if (data && ["verified", "delivered"].includes((data.status || "").toLowerCase())) {
        setStatus(data.status, "verified");
      }
      return true;
    } catch (e) {
      show({ session_id: sid, title: "Unlock required", status: "Pending", required_ads: 1 });
      return true;
    }
  }

  return { show, hide, bindUI, maybeOpenFromStartParam, startPoll, showAd };
})();
