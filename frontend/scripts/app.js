/**
 * NOVA Movie Hub — main app bootstrap
 */
(function () {
  const main = document.getElementById("app-main");
  const S = window.NOVA_SCREENS;

  function mountScreens() {
    main.innerHTML = S.home() + S.discover() + S.ai() + S.saved() + S.profile();
  }

  function switchScreen(name) {
    document.querySelectorAll(".screen").forEach((n) => n.classList.remove("active"));
    const target = document.getElementById("screen-" + name) || document.querySelector(`[data-screen="${name}"]`);
    if (target) target.classList.add("active");
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-screen") === name);
    });
    const nav = document.getElementById("bottom-nav");
    if (nav) nav.style.display = name === "profile" ? "flex" : "flex";
  }

  function bindNav() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => {
        const screen = btn.getAttribute("data-screen");
        switchScreen(screen);
        if (window.NOVA_TG_CTX) window.NOVA_TG_CTX.haptic("light");
      });
    });
    const profileBtn = document.getElementById("btn-profile");
    if (profileBtn) {
      profileBtn.addEventListener("click", () => switchScreen("profile"));
    }
  }

  function bindHome() {
    const search = document.getElementById("home-search");
    if (search) {
      search.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          switchScreen("discover");
          const d = document.getElementById("discover-search");
          if (d) {
            d.value = search.value;
            runSearch(search.value);
          }
        }
      });
    }
    const aiGo = document.getElementById("home-ai-go");
    const aiIn = document.getElementById("home-ai-input");
    if (aiGo && aiIn) {
      aiGo.addEventListener("click", () => {
        switchScreen("ai");
        const a = document.getElementById("ai-input");
        if (a) {
          a.value = aiIn.value;
          runAi(aiIn.value);
        }
      });
    }
    document.querySelectorAll("#home-genres .chip, #home-langs .chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        chip.classList.toggle("active");
        switchScreen("discover");
      });
    });
  }

  function bindAi() {
    const send = document.getElementById("ai-send");
    const input = document.getElementById("ai-input");
    if (send && input) {
      send.addEventListener("click", () => runAi(input.value));
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") runAi(input.value);
      });
    }
    document.querySelectorAll("#ai-suggestions .chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const p = chip.getAttribute("data-prompt") || chip.textContent;
        if (input) input.value = p;
        runAi(p);
      });
    });
  }

  async function runSearch(q) {
    const box = document.getElementById("discover-results");
    if (!box) return;
    box.innerHTML = S.skeletonRow(6);
    try {
      const data = await window.NOVA_API.catalog.search(q);
      const results = (data && data.results) || [];
      if (!results.length) {
        box.innerHTML = `<div class="empty-state"><strong>No results</strong>Try another title or filter. Catalog needs a live API key.</div>`;
        return;
      }
      box.innerHTML = `<div class="h-scroll" style="flex-wrap:wrap">${results.map(S.movieCard).join("")}</div>`;
    } catch (e) {
      box.innerHTML = `<div class="error-state"><strong>Search unavailable</strong>Connect the backend catalog API.</div>`;
    }
  }

  async function runAi(prompt) {
    const thread = document.getElementById("ai-thread");
    if (!thread || !prompt || !prompt.trim()) return;
    thread.innerHTML = `<div class="empty-state"><strong>Thinking…</strong>Grounding in catalog data.</div>`;
    try {
      const data = await window.NOVA_API.ai.discover(prompt.trim());
      const results = (data && data.results) || [];
      const msg = (data && data.message) || "";
      let html = msg ? `<p style="font-size:13px;color:var(--text-muted);margin-bottom:10px">${msg}</p>` : "";
      if (results.length) {
        html += `<div class="h-scroll">${results.map(S.movieCard).join("")}</div>`;
      } else {
        html += `<div class="empty-state"><strong>No grounded matches yet</strong>Connect TMDB/catalog + AI service on the backend.</div>`;
      }
      thread.innerHTML = html;
    } catch (e) {
      thread.innerHTML = `<div class="error-state"><strong>AI unavailable</strong>Backend /ai/discover is not connected.</div>`;
    }
  }

  async function loadHomeCatalog() {
    try {
      const trend = await window.NOVA_API.catalog.trending();
      S.renderRow("home-trending", (trend && trend.results) || []);
      S.renderRow("home-new", (trend && trend.results) || []);
    } catch (_) {
      S.renderRow("home-trending", []);
      S.renderRow("home-new", []);
    }
  }

  async function boot() {
    mountScreens();
    bindNav();
    bindHome();
    bindAi();
    window.NOVA_REWARD.bindUI();

    window.NOVA_TG_CTX = window.NOVA_TG.init();
    const ctx = window.NOVA_TG_CTX;

    if (ctx.user) {
      const nameEl = document.getElementById("profile-name");
      if (nameEl) {
        nameEl.textContent = [ctx.user.first_name, ctx.user.last_name].filter(Boolean).join(" ") || ("@" + (ctx.user.username || ctx.user.id));
      }
    }

    // Authenticate with backend when initData is present
    if (ctx.initData) {
      try {
        await window.NOVA_API.authenticate(ctx.initData);
      } catch (e) {
        console.warn("Auth deferred (backend may be offline):", e.message || e);
      }
    }

    // Reward / operation deep link from bot
    if (ctx.startParam) {
      await window.NOVA_REWARD.maybeOpenFromStartParam(ctx.startParam);
    }

    await loadHomeCatalog();
    switchScreen("home");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
