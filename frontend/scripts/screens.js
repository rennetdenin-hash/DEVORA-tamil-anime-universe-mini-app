/**
 * Screen templates and render helpers for NOVA Movie Hub
 */
window.NOVA_SCREENS = (function () {
  function el(html) {
    const d = document.createElement("div");
    d.innerHTML = html.trim();
    return d.firstChild;
  }

  function skeletonRow(n = 5) {
    return `<div class="h-scroll">${Array.from({ length: n }).map(() => `<div class="skeleton skel-poster"></div>`).join("")}</div>`;
  }

  function movieCard(m) {
    const title = (m.title || m.name || "Untitled").replace(/</g, "");
    const year = m.year || (m.release_date || "").slice(0, 4) || "";
    const poster = m.poster_url || m.poster || "";
    const id = m.id || m.catalog_id || "";
    return `
      <article class="movie-card" data-id="${id}" role="button" tabindex="0">
        ${poster ? `<img class="poster" src="${poster}" alt="" loading="lazy" />` : `<div class="poster skeleton"></div>`}
        <div class="meta">
          <div class="title">${title}</div>
          <div class="year">${year}</div>
        </div>
      </article>`;
  }

  function home() {
    return `
      <section class="screen active" data-screen="home" id="screen-home">
        <div class="search-bar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9b93b8" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3-3"/></svg>
          <input type="search" id="home-search" placeholder="Search movies, series or describe a story" autocomplete="off" />
        </div>

        <div class="ai-prompt-card">
          <h3>Describe what you want to watch</h3>
          <p>AI finds matches from the catalog — no invented titles or dates.</p>
          <div class="ai-input-row">
            <input type="text" id="home-ai-input" placeholder="e.g. Tamil mystery with a twist" />
            <button type="button" id="home-ai-go">Ask</button>
          </div>
        </div>

        <div class="section-title">Trending</div>
        <div id="home-trending">${skeletonRow()}</div>

        <div class="section-title">New &amp; upcoming</div>
        <div id="home-new">${skeletonRow()}</div>

        <div class="section-title">Genres &amp; moods</div>
        <div class="chips" id="home-genres">
          <button type="button" class="chip" data-genre="Action">Action</button>
          <button type="button" class="chip" data-genre="Drama">Drama</button>
          <button type="button" class="chip" data-genre="Comedy">Comedy</button>
          <button type="button" class="chip" data-genre="Thriller">Thriller</button>
          <button type="button" class="chip" data-genre="Romance">Romance</button>
          <button type="button" class="chip" data-genre="Animation">Animation</button>
          <button type="button" class="chip" data-genre="Sci-Fi">Sci-Fi</button>
        </div>

        <div class="section-title">Regional</div>
        <div class="chips" id="home-langs">
          <button type="button" class="chip" data-lang="ta">Tamil</button>
          <button type="button" class="chip" data-lang="hi">Hindi</button>
          <button type="button" class="chip" data-lang="te">Telugu</button>
          <button type="button" class="chip" data-lang="ml">Malayalam</button>
          <button type="button" class="chip" data-lang="kn">Kannada</button>
          <button type="button" class="chip" data-lang="en">English</button>
          <button type="button" class="chip" data-lang="ko">Korean</button>
          <button type="button" class="chip" data-lang="ja">Japanese</button>
        </div>
      </section>`;
  }

  function discover() {
    return `
      <section class="screen" data-screen="discover" id="screen-discover">
        <div class="search-bar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#9b93b8" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3-3"/></svg>
          <input type="search" id="discover-search" placeholder="Title, actor, director…" autocomplete="off" />
        </div>
        <div class="section-title">Filters</div>
        <div class="chips">
          <button type="button" class="chip active" data-type="all">All</button>
          <button type="button" class="chip" data-type="movie">Movies</button>
          <button type="button" class="chip" data-type="tv">TV</button>
        </div>
        <div class="section-title">Results</div>
        <div id="discover-results">
          <div class="empty-state"><strong>Search or pick a filter</strong>Results appear here from the catalog.</div>
        </div>
      </section>`;
  }

  function ai() {
    return `
      <section class="screen" data-screen="ai" id="screen-ai">
        <div class="ai-prompt-card">
          <h3>AI Movie Assistant</h3>
          <p>Describe a mood, plot, or pick constraints. Answers are grounded in catalog data.</p>
          <div class="ai-input-row">
            <input type="text" id="ai-input" placeholder="Find something under 2 hours in Tamil…" />
            <button type="button" id="ai-send">Send</button>
          </div>
        </div>
        <div class="section-title">Suggested</div>
        <div class="chips" id="ai-suggestions">
          <button type="button" class="chip" data-prompt="Find a movie">Find a movie</button>
          <button type="button" class="chip" data-prompt="Pick something in Tamil">Tamil pick</button>
          <button type="button" class="chip" data-prompt="Similar to Inception">Similar to…</button>
          <button type="button" class="chip" data-prompt="Help identify a movie">Identify</button>
          <button type="button" class="chip" data-prompt="Compare two titles">Compare</button>
        </div>
        <div id="ai-thread" style="margin-top:14px"></div>
      </section>`;
  }

  function saved() {
    return `
      <section class="screen" data-screen="saved" id="screen-saved">
        <div class="section-title">Watchlist</div>
        <div id="saved-list">
          <div class="empty-state"><strong>No saved titles yet</strong>Save from movie details when browsing.</div>
        </div>
        <div class="section-title">History</div>
        <div id="history-list">
          <div class="empty-state"><strong>History is private</strong>Clear or disable anytime in Settings.</div>
        </div>
      </section>`;
  }

  function profile() {
    return `
      <section class="screen" data-screen="profile" id="screen-profile">
        <div class="section-title">Profile</div>
        <ul class="panel-list">
          <li>Telegram user <span id="profile-name">—</span></li>
          <li>Language <span>English</span></li>
          <li>Theme <span>AMOLED dark</span></li>
        </ul>
        <div class="section-title">Privacy</div>
        <ul class="panel-list">
          <li>Clear history <span id="btn-clear-history" style="color:var(--accent-soft);cursor:pointer">Clear</span></li>
          <li>Help &amp; support <span>FAQ</span></li>
        </ul>
        <p style="font-size:12px;color:var(--text-muted);margin-top:16px;line-height:1.4">
          Movie browsing does not require ads. Reward steps only apply to eligible bot operations and are verified server-side.
        </p>
      </section>`;
  }

  function renderRow(containerId, items) {
    const node = document.getElementById(containerId);
    if (!node) return;
    if (!items || !items.length) {
      node.innerHTML = `<div class="empty-state" style="padding:16px 0"><strong>Nothing here yet</strong>Catalog data loads when the API is connected.</div>`;
      return;
    }
    node.innerHTML = `<div class="h-scroll">${items.map(movieCard).join("")}</div>`;
  }

  return { home, discover, ai, saved, profile, renderRow, movieCard, skeletonRow };
})();
