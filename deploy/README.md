# Hosting the ASTRA website

- **Website** (`kgrag-web`): hosted on **Vercel**, free, always on.
- **Live answers**: come from the API on **your laptop**, reachable through a
  free **Tailscale Funnel** with a permanent HTTPS address.

| Laptop API | What visitors get |
|---|---|
| Running | Any question answered live (10–30 s) |
| Off | Example questions answered instantly from recorded live answers; new questions show "live system offline" |

One-time setup takes about 20 minutes. Afterwards, going live is one command.

---

## 1. Tailscale (public address for your laptop)

1. Download the Windows installer from https://tailscale.com/download/windows
   and run it (Windows asks for permission to install).
2. Tailscale opens a sign-in page. Sign in with Google, GitHub or Microsoft.
   The free Personal plan is enough.
3. Optional, for a nicer address: in the admin console
   (https://login.tailscale.com/admin/machines), open your computer's **⋯**
   menu, choose **Edit machine name**, and set something like `astra`.
4. In a new PowerShell, run once:

   ```bash
   tailscale funnel 8000
   ```

   The first time, it prints a link to enable **HTTPS** and **Funnel** for your
   account. Open the link and approve. Then run the command again: it shows
   your public address, like `https://astra.tail1234.ts.net`. Note it down,
   then press `Ctrl+C` to stop it.

## 2. Vercel (the website)

1. Go to https://vercel.com and sign up with **Continue with GitHub**.
2. **Add New… → Project**, then import `nandana-das/isro-knowledge-graph-rag`.
3. Before deploying, set:
   - **Root Directory**: `kgrag-web` (click Edit next to it)
   - **Framework Preset**: Vite (detected automatically)
   - **Environment Variables**: name `VITE_API_URL`, value = your Tailscale
     address from step 1.4 (e.g. `https://astra.tail1234.ts.net`, no trailing slash).
     **No Tailscale yet?** Leave it out. The site then runs in offline mode
     (recorded example answers only); add the variable and redeploy later.
4. Click **Deploy**. When it finishes, copy the address, e.g.
   `https://isro-knowledge-graph-rag.vercel.app`.

Vercel rebuilds the site automatically on every push to `main`. If you change
`VITE_API_URL` later, redeploy from the Vercel dashboard so it takes effect.

## 3. Connect the two

1. Copy `deploy/public.env.example` to `deploy/public.env`.
2. Set `FRONTEND_ORIGIN` to your Vercel address (with `https://`).

`deploy/public.env` is git-ignored.

## 4. Go live

Ollama and the model must be installed, as for local live mode. From the
repository root:

```bash
powershell -ExecutionPolicy Bypass -File deploy\start-public.ps1
```

The script:
- starts Ollama if needed;
- opens one window for the API and one for the Funnel;
- prints your public API address.

After 2–3 minutes of warm-up, the website switches from "offline" to "live"
by itself. Check it at `https://<your tailscale address>/api/health`.

To stop: close the API and Funnel windows. Closing the Funnel window ends
public access. Keep the laptop awake and plugged in while live.

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
| Site says "Live system offline" while the API runs | Open `https://<tailscale address>/api/health` in a browser. If that fails, check the Funnel window for errors. |
| Browser console shows a CORS error | `FRONTEND_ORIGIN` in `deploy/public.env` must exactly match the Vercel address (https, no trailing slash). Restart the script. |
| Script says Tailscale isn't running | Open Tailscale from the Start menu and sign in. |
| Funnel says it isn't enabled | Repeat step 1.4 and approve the link it prints. |
| tailscale.com won't load (connection reset) | Your network blocks VPN/tunnel services, which is common on college and office networks. Set up and go live from a network that allows it (e.g. home). Don't try to work around the block. |
| The address changed | Renaming the machine changes it. Update `VITE_API_URL` in Vercel and redeploy. |

## Good to know

- While live, anyone with the website can send questions to your laptop. The
  API only answers questions, one at a time; it has no access to your files.
  Only port 8000 is exposed, and only while the Funnel window is open.
- Everything here is free: Vercel Hobby plan and Tailscale Personal plan.
