# Hosting the ASTRA website

- **Website** (`kgrag-web`): hosted on **Vercel**, free, always on.
- **Live answers**: come from the API on **your laptop**, reachable through a
  free **ngrok** tunnel with a permanent address.

| Laptop API | What visitors get |
|---|---|
| Running | Any question answered live (10–30 s) |
| Off | Example questions answered instantly from recorded live answers; new questions show "live system offline" |

One-time setup takes about 20 minutes. Afterwards, going live is one command.

---

## 1. ngrok (tunnel to your laptop)

1. Create a free account at https://ngrok.com.
2. Install ngrok. In PowerShell:

   ```bash
   winget install ngrok.ngrok
   ```

   Close and reopen PowerShell afterwards.
3. In the ngrok dashboard, open **Your Authtoken** and run the command it shows
   (`ngrok config add-authtoken …`). Keep the token private.
4. In the ngrok dashboard, open **Domains** and claim your free static domain.
   It looks like `something-something.ngrok-free.app`. Note it down.

## 2. Vercel (the website)

1. Go to https://vercel.com and sign up with **Continue with GitHub**.
2. **Add New… → Project**, then import `nandana-das/isro-knowledge-graph-rag`.
3. Before deploying, set:
   - **Root Directory**: `kgrag-web` (click Edit next to it)
   - **Framework Preset**: Vite (detected automatically)
   - **Environment Variables**: name `VITE_API_URL`, value
     `https://<your ngrok domain>` (no trailing slash)
4. Click **Deploy**. When it finishes, copy the address, e.g.
   `https://isro-knowledge-graph-rag.vercel.app`.

Vercel rebuilds the site automatically on every push to `main`.

## 3. Connect the two

1. Copy `deploy/public.env.example` to `deploy/public.env`.
2. Fill in:
   - `NGROK_DOMAIN`: your ngrok domain (no `https://`)
   - `FRONTEND_ORIGIN`: your Vercel address (with `https://`)

`deploy/public.env` is git-ignored.

## 4. Go live

Ollama and the model must be installed, as for local live mode. From the
repository root:

```bash
powershell -ExecutionPolicy Bypass -File deploy\start-public.ps1
```

The script:
- starts Ollama if needed;
- opens one window for the API and one for ngrok.

After 2–3 minutes of warm-up, the website switches from "offline" to "live"
by itself. Check it at `https://<your ngrok domain>/api/health`.

To stop: close the API and ngrok windows. Keep the laptop awake and plugged
in while live; sleep cuts the connection.

## Updating the recorded answers

After changing the system, re-record the example answers (Ollama must be
running, ~15 minutes):

```bash
.venv\Scripts\python.exe -m src.api.export_recorded
```

Then commit and push `kgrag-web/public/recorded_answers.json`; Vercel
redeploys.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Site says "Live system offline" while the API runs | Check `https://<ngrok domain>/api/health` in a browser. If that fails, the ngrok window shows why. |
| Browser console shows a CORS error | `FRONTEND_ORIGIN` in `deploy/public.env` must exactly match the Vercel address (https, no trailing slash). Restart the script. |
| Health page shows an ngrok warning page | Normal in a browser tab; the website sends the header that skips it. |
| `ngrok` not found | Reopen PowerShell after installing, or reinstall (step 1.2). |

## Good to know

- While live, anyone with the website can send questions to your laptop. The
  API only answers questions, one at a time; it has no access to your files.
  Stop it when you don't need it.
- Everything here is free: Vercel Hobby plan and ngrok's free plan (one static
  domain, with monthly bandwidth limits that a demo won't reach).
