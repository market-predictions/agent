// Pinned integration shim for FreeLLMAPI v0.9.8.
//
// v0.9.8 creates a random unified API key on first migration but exposes no
// environment override for that setting. A remote headless deployment needs a
// stable key shared only with the Hermes client. Use FreeLLMAPI's exported DB
// API instead of editing SQLite directly. The caller suppresses stdout so the
// temporary migration-generated key never reaches logs.

import { initDb, setSetting } from '/app/server/dist/db/index.js';

initDb();

const key = process.env.FREELLMAPI_API_KEY;
if (!key || !key.startsWith('freellmapi-')) {
  throw new Error('FREELLMAPI_API_KEY must use the freellmapi- prefix');
}

setSetting('unified_api_key', key);
