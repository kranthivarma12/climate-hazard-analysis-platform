import express from 'express';
import { createServer as createViteServer } from 'vite';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { spawn, execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import http from 'http';

const PORT = parseInt(process.env.PORT || '3000', 10);
const BACKEND_PORT = parseInt(process.env.BACKEND_PORT || '8001', 10);
const isProd = process.env.NODE_ENV === 'production';

// Ensure MongoDB is running locally
try {
  const isMongoRunning = execSync('pgrep -x mongod || true').toString().trim();
  if (!isMongoRunning) {
    console.log('[Server] Launching mongod daemon on 127.0.0.1:27017...');
    execSync('mkdir -p /data/db && mongod --fork --logpath /var/log/mongodb.log --dbpath /data/db --bind_ip 127.0.0.1 2>/dev/null || true');
  } else {
    console.log('[Server] mongod daemon is active.');
  }
} catch (err) {
  console.warn('[Server] Note on mongod daemon check:', (err as Error).message);
}

// Function to check if backend is listening
function isPortOpen(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const req = http.get(`http://127.0.0.1:${port}/api/v1/health`, (res) => {
      resolve(res.statusCode === 200 || res.statusCode === 502);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(500, () => {
      req.destroy();
      resolve(false);
    });
  });
}

// Ensure Python FastAPI backend is running
let pythonProcess: any = null;
async function startFastApiBackend() {
  const alreadyRunning = await isPortOpen(BACKEND_PORT);
  if (alreadyRunning) {
    console.log(`[Server] FastAPI backend is already running on port ${BACKEND_PORT}`);
    return;
  }

  const venvPython = fs.existsSync('/app/venv/bin/uvicorn')
    ? '/app/venv/bin/uvicorn'
    : 'uvicorn';

  console.log(`[Server] Starting FastAPI backend via ${venvPython} on port ${BACKEND_PORT}...`);
  pythonProcess = spawn(
    venvPython,
    ['backend.app.main:app', '--host', '127.0.0.1', '--port', String(BACKEND_PORT)],
    {
      cwd: process.cwd(),
      env: { ...process.env, PYTHONPATH: '.' },
      stdio: ['ignore', 'inherit', 'inherit'],
    }
  );

  pythonProcess.on('error', (err: any) => {
    console.error('[Server] Failed to spawn FastAPI backend:', err);
  });

  // Wait briefly for backend to initialize
  for (let i = 0; i < 20; i++) {
    await new Promise((r) => setTimeout(r, 250));
    if (await isPortOpen(BACKEND_PORT)) {
      console.log(`[Server] FastAPI backend successfully responding on port ${BACKEND_PORT}`);
      break;
    }
  }
}

async function startServer() {
  await startFastApiBackend();

  const app = express();

  // Proxy API requests to Python FastAPI backend
  app.use('/api', async (req, res) => {
    try {
      const targetUrl = `http://127.0.0.1:${BACKEND_PORT}${req.originalUrl}`;
      console.log(`[Proxy] Forwarding ${req.method} ${req.originalUrl} -> ${targetUrl}`);
      const headers: Record<string, string> = {};
      for (const [k, v] of Object.entries(req.headers)) {
        if (v && k !== 'host') {
          headers[k] = Array.isArray(v) ? v.join(',') : v;
        }
      }
      const hasBody = ['POST', 'PUT', 'PATCH'].includes(req.method);
      const backendRes = await fetch(targetUrl, {
        method: req.method,
        headers,
        body: hasBody ? (req as any) : undefined,
        duplex: hasBody ? 'half' : undefined,
      } as any);

      res.status(backendRes.status);
      backendRes.headers.forEach((val, key) => {
        res.setHeader(key, val);
      });
      const data = await backendRes.arrayBuffer();
      res.send(Buffer.from(data));
    } catch (err: any) {
      res.status(502).json({ detail: `FastAPI Gateway Error: ${err.message}` });
    }
  });

  if (!isProd) {
    // Development mode: attach Vite dev server middleware
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    // Production mode: serve built static files
    const distPath = path.resolve(__dirname, 'dist');
    app.use(express.static(distPath));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Server] Climate Hazard Platform listening on http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error('[Server] Fatal server startup error:', err);
  process.exit(1);
});

process.on('SIGTERM', () => {
  if (pythonProcess) pythonProcess.kill();
  process.exit(0);
});
