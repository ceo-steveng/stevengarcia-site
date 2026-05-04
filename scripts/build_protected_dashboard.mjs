import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { randomBytes, pbkdf2Sync, createCipheriv } from 'node:crypto';

const repoRoot = new URL('..', import.meta.url).pathname;
const srcDir = process.env.DASHBOARD_SRC || '/Users/aiden/Library/CloudStorage/OneDrive-AnciraEnterprises,Inc/ANCIRA KIA DEALER DASHBOARD';
const outDir = join(repoRoot, 'ancira-dashboard');
const password = process.env.ANCIRA_DASHBOARD_PASSWORD;

if (!password || password.length < 12) {
  console.error('Set ANCIRA_DASHBOARD_PASSWORD to a 12+ character password before building.');
  process.exit(1);
}

let html = readFileSync(join(srcDir, 'dashboard.html'), 'utf8');
const data = readFileSync(join(srcDir, 'data.js'), 'utf8');
html = html.replace(/<script\s+src=["']data\.js["']><\/script>/i, `<script>\n${data}\n</script>`);

const salt = randomBytes(16);
const iv = randomBytes(12);
const iterations = 310000;
const key = pbkdf2Sync(password, salt, iterations, 32, 'sha256');
const cipher = createCipheriv('aes-256-gcm', key, iv);
const ciphertext = Buffer.concat([cipher.update(html, 'utf8'), cipher.final()]);
const tag = cipher.getAuthTag();
const payload = {
  v: 1,
  kdf: 'PBKDF2-SHA256',
  cipher: 'AES-256-GCM',
  iterations,
  salt: salt.toString('base64'),
  iv: iv.toString('base64'),
  tag: tag.toString('base64'),
  data: ciphertext.toString('base64'),
  updated: new Date().toISOString()
};

const page = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <title>Ancira Dashboard</title>
  <style>
    :root { color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin:0; min-height:100vh; display:grid; place-items:center; background:#0f172a; color:#e5e7eb; }
    main { width:min(420px, calc(100vw - 32px)); background:rgba(15,23,42,.94); border:1px solid rgba(148,163,184,.28); border-radius:20px; box-shadow:0 24px 80px rgba(0,0,0,.38); padding:28px; }
    h1 { margin:0 0 8px; font-size:24px; }
    p { margin:0 0 22px; color:#94a3b8; line-height:1.45; }
    label { display:block; font-size:13px; color:#cbd5e1; margin-bottom:8px; }
    input { box-sizing:border-box; width:100%; padding:13px 14px; border-radius:12px; border:1px solid #334155; background:#020617; color:#f8fafc; font-size:16px; }
    button { width:100%; margin-top:14px; padding:13px 14px; border:0; border-radius:12px; background:#2563eb; color:white; font-weight:700; font-size:15px; cursor:pointer; }
    button:disabled { opacity:.65; cursor:not-allowed; }
    .error { min-height:20px; margin-top:12px; color:#fca5a5; font-size:13px; }
    iframe { position:fixed; inset:0; width:100%; height:100%; border:0; background:white; }
  </style>
</head>
<body>
  <main id="gate">
    <h1>Ancira Dashboard</h1>
    <p>Password required. This page is encrypted before it reaches the browser.</p>
    <form id="form">
      <label for="password">Password</label>
      <input id="password" type="password" autocomplete="current-password" autofocus required>
      <button id="button" type="submit">Unlock dashboard</button>
      <div class="error" id="error" role="alert"></div>
    </form>
  </main>
  <script>
    const encryptedPayload = ${JSON.stringify(payload)};
    const decoder = new TextDecoder();
    const b64 = (s) => Uint8Array.from(atob(s), c => c.charCodeAt(0));
    async function unlock(password) {
      const pw = new TextEncoder().encode(password);
      const keyMaterial = await crypto.subtle.importKey('raw', pw, 'PBKDF2', false, ['deriveKey']);
      const key = await crypto.subtle.deriveKey(
        { name: 'PBKDF2', salt: b64(encryptedPayload.salt), iterations: encryptedPayload.iterations, hash: 'SHA-256' },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['decrypt']
      );
      const sealed = new Uint8Array([...b64(encryptedPayload.data), ...b64(encryptedPayload.tag)]);
      const plain = await crypto.subtle.decrypt({ name:'AES-GCM', iv:b64(encryptedPayload.iv), tagLength:128 }, key, sealed);
      return decoder.decode(plain);
    }
    document.getElementById('form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const button = document.getElementById('button');
      const error = document.getElementById('error');
      button.disabled = true;
      button.textContent = 'Unlocking...';
      error.textContent = '';
      try {
        const html = await unlock(document.getElementById('password').value);
        const frame = document.createElement('iframe');
        frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
        document.body.innerHTML = '';
        document.body.appendChild(frame);
        frame.srcdoc = html;
      } catch (e) {
        error.textContent = 'Wrong password.';
        button.disabled = false;
        button.textContent = 'Unlock dashboard';
      }
    });
  </script>
</body>
</html>`;

mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'index.html'), page);
console.log(`Wrote ${join(outDir, 'index.html')}`);
