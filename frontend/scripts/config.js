/**
 * NOVA Movie Hub — frontend config
 * OWNER_IDS / ADMIN_IDS: Telegram user ids (numbers). Owner can manage; admin elevated; users view-only.
 */
window.NOVA_CONFIG = {
  API_BASE: "", // e.g. "https://api.yourdomain.com"
  APP_NAME: "NOVA Movie Hub",
  ADSGRAM_BLOCK_ID: "",
  // Owner: full Mini App manage permissions. Admins: elevated, no owner-only edit.
  // Regular users: discovery + reward unlock only.
  OWNER_IDS: [],   // e.g. [123456789]
  ADMIN_IDS: [],   // owner-approved admin Telegram ids
  FEATURES: {
    ai: true,
    watchlist: true,
    history: true,
    reward: true,
    ownerEdit: true,
  },
};
