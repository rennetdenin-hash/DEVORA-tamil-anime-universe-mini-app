/**
 * NOVA API client — all calls go through backend; never trust client-only auth.
 */
window.NOVA_API = (function () {
  const cfg = () => window.NOVA_CONFIG || {};
  let authHeader = null; // set after /auth/telegram

  function base() {
    return (cfg().API_BASE || "").replace(/\/$/, "");
  }

  async function request(path, options = {}) {
    const url = base() + path;
    const headers = Object.assign(
      { "Content-Type": "application/json", Accept: "application/json" },
      options.headers || {}
    );
    if (authHeader) headers["Authorization"] = authHeader;
    if (options.initData) headers["X-Telegram-Init-Data"] = options.initData;

    const res = await fetch(url, {
      method: options.method || "GET",
      headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const text = await res.text();
    let data = null;
    try { data = text ? JSON.parse(text) : null; } catch (_) { data = { raw: text }; }
    if (!res.ok) {
      const err = new Error((data && data.detail) || res.statusText || "Request failed");
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  async function authenticate(initData) {
    const data = await request("/auth/telegram", {
      method: "POST",
      body: { init_data: initData },
    });
    if (data && data.token) {
      authHeader = "Bearer " + data.token;
    }
    return data;
  }

  // Catalog (stubs return empty until backend is live)
  const catalog = {
    trending: () => request("/catalog/trending").catch(() => ({ results: [] })),
    search: (q, params = {}) => {
      const qs = new URLSearchParams({ q: q || "", ...params }).toString();
      return request("/catalog/search?" + qs).catch(() => ({ results: [] }));
    },
    details: (id) => request("/catalog/" + encodeURIComponent(id)).catch(() => null),
    similar: (id) => request("/catalog/" + encodeURIComponent(id) + "/similar").catch(() => ({ results: [] })),
  };

  const watchlist = {
    list: () => request("/watchlist").catch(() => ({ items: [] })),
    add: (catalogId, type) => request("/watchlist", { method: "POST", body: { catalog_id: catalogId, content_type: type || "movie" } }),
    remove: (id) => request("/watchlist/" + encodeURIComponent(id), { method: "DELETE" }),
  };

  const operations = {
    markVerified: async (sessionId) => {
      const base = (window.NOVA_CONFIG && window.NOVA_CONFIG.API_BASE) || "";
      const r = await fetch(base + "/operations/" + encodeURIComponent(sessionId) + "/mark_verified?public=1", { method: "POST" });
      if (!r.ok) throw new Error("mark_verified failed");
      return r.json();
    },
    get: (sessionId) => request("/operations/" + encodeURIComponent(sessionId)),
    // Client never claims reward done — only polls status after provider verification
  };

  const ai = {
    discover: (prompt) => request("/ai/discover", { method: "POST", body: { prompt } }).catch(() => ({ results: [], message: "AI temporarily unavailable." })),
  };

  return { request, authenticate, catalog, watchlist, operations, ai, setToken: (t) => { authHeader = t ? "Bearer " + t : null; } };
})();
