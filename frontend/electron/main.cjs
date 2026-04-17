const { app, BrowserWindow, Tray, Menu, ipcMain, webContents, globalShortcut } = require('electron');
const path = require('path');
const url = require('url');
const http = require('http');

let mainWindow;
let quickWindow;
let bootWindow;
let tray;
let isQuitting = false;
let systemState = true;

// IPC Listeners for Performance Mode
ipcMain.on('change-performance-mode', (event, mode) => {
  console.log(`[Electron] Switching to ${mode} mode`);
  if (!mainWindow) return;
  switch (mode) {
    case 'eco':
      mainWindow.webContents.setFrameRate(30);
      break;
    case 'balanced':
      mainWindow.webContents.setFrameRate(60);
      break;
    case 'overdrive':
      mainWindow.webContents.setFrameRate(144);
      break;
  }
});

ipcMain.on('wake-word-detected', () => {
  console.log('[Electron] Wake word detected signal received');
  if (quickWindow) {
    quickWindow.show();
  }
});

ipcMain.on('quick-chat-hide', () => {
  console.log('[Electron] Quick chat hide signal received');
  if (quickWindow) {
    quickWindow.hide();
  }
});

ipcMain.on('quick-chat-minimize', () => {
  console.log('[Electron] Quick chat minimize signal received');
  if (quickWindow) {
    quickWindow.minimize();
  }
});

function createBootWindow() {
  bootWindow = new BrowserWindow({
    width: 500,
    height: 400,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  bootWindow.loadFile(path.join(__dirname, 'boot.html'));
  
  // Start monitoring services
  monitorServices();
}

function monitorServices() {
  const services = {
    frontend: { port: 5173, status: 'pending', ready: false },
    backend: { port: 8000, status: 'pending', ready: false },
    voice: { port: 8000, path: '/api/system/voice-status', status: 'pending', ready: false }
  };

  let checkCount = 0;
  const MAX_RETRIES = 60; // 2 minutes max (60 * 2 seconds)

  const checkInterval = setInterval(async () => {
    checkCount++;

    // Safety check: bootWindow must exist
    if (!bootWindow || bootWindow.isDestroyed()) {
      console.log('[Boot] Boot window closed, stopping monitor');
      clearInterval(checkInterval);
      return;
    }

    // Check all services concurrently and wait for results
    const [frontendOnline, backendOnline, voiceActive] = await Promise.all([
      checkFrontend(),
      checkPort(services.backend.port),
      services.backend.ready ? checkVoiceStatus() : Promise.resolve(false)
    ]);

    // Update Frontend status
    if (services.frontend.status !== (frontendOnline ? 'online' : 'pending')) {
      services.frontend.status = frontendOnline ? 'online' : 'pending';
      services.frontend.ready = frontendOnline;
      if (bootWindow && !bootWindow.isDestroyed()) {
        bootWindow.webContents.send('status-update', {
          service: 'frontend',
          status: services.frontend.status,
          log: frontendOnline ? 'Frontend service connected.' : `Waiting for Vite server... (check #${checkCount})`
        });
      }
    }

    // Update Backend status
    if (services.backend.status !== (backendOnline ? 'online' : 'pending')) {
      services.backend.status = backendOnline ? 'online' : 'pending';
      services.backend.ready = backendOnline;
      if (bootWindow && !bootWindow.isDestroyed()) {
        bootWindow.webContents.send('status-update', {
          service: 'backend',
          status: services.backend.status,
          log: backendOnline ? 'Backend API operational.' : `Starting FastAPI engine... (check #${checkCount})`
        });
      }
    }

    // Update Voice status (only check if backend is ready)
    if (backendOnline) {
      const voiceStatus = voiceActive ? 'online' : 'error';
      if (services.voice.status !== voiceStatus) {
        services.voice.status = voiceStatus;
        services.voice.ready = voiceActive;
        if (bootWindow && !bootWindow.isDestroyed()) {
          bootWindow.webContents.send('status-update', {
            service: 'voice',
            status: voiceStatus,
            log: voiceActive ? 'Voice protocol initialized.' : 'Voice system unavailable (optional).'
          });
        }
      }
    }

    // Log current status for debugging
    console.log(`[Boot] Check #${checkCount}: Frontend=${services.frontend.status}, Backend=${services.backend.status}, Voice=${services.voice.status}`);

    // Transition if all critical services are ready (voice is optional)
    if (services.frontend.ready && services.backend.ready) {
      console.log('[Boot] All critical services ready. Transitioning to main window...');
      clearInterval(checkInterval);

      // Show success state briefly
      if (bootWindow && !bootWindow.isDestroyed()) {
        bootWindow.webContents.send('status-update', {
          service: 'frontend',
          status: 'online',
          log: 'All systems operational. Launching dashboard...'
        });
      }

      setTimeout(() => {
        createMainWindow();
        createQuickWindow();
        registerGlobalHotkeys();
        if (bootWindow && !bootWindow.isDestroyed()) {
          bootWindow.close();
        }
      }, 1500);
      return;
    }

    // Max retries exceeded - show error but still proceed
    if (checkCount >= MAX_RETRIES) {
      console.log('[Boot] Max retries exceeded. Proceeding with available services...');
      clearInterval(checkInterval);

      if (bootWindow && !bootWindow.isDestroyed()) {
        bootWindow.webContents.send('status-update', {
          service: 'frontend',
          status: services.frontend.ready ? 'online' : 'error',
          log: 'Some services unavailable. Launching with limited functionality...'
        });
      }

      setTimeout(() => {
        createMainWindow();
        createQuickWindow();
        registerGlobalHotkeys();
        if (bootWindow && !bootWindow.isDestroyed()) {
          bootWindow.close();
        }
      }, 2000);
    }
  }, 2000);
}

function checkFrontend() {
  return new Promise((resolve) => {
    // Vite binds to localhost - use localhost (may resolve to ::1 or 127.0.0.1)
    const request = http.get(`http://localhost:5173/`, (res) => {
      resolve(res.statusCode < 500);
      res.resume();
    }).on('error', (err) => {
      resolve(false);
    });
    request.setTimeout(2000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

function checkPort(port) {
  return new Promise((resolve) => {
    // For backend (port 8000), use the status endpoint
    const path = port === 8000 ? '/api/status' : '/';
    // Use 127.0.0.1 explicitly to force IPv4 (avoid ::1 IPv6 issues)
    const request = http.get(`http://127.0.0.1:${port}${path}`, (res) => {
      // Any successful response (2xx, 3xx) or 404 means server is up
      const isOnline = res.statusCode < 500;
      resolve(isOnline);
      res.resume();
    }).on('error', (err) => {
      console.log(`[Boot] Port ${port} check failed: ${err.message}`);
      resolve(false);
    });
    request.setTimeout(2000, () => {
      request.destroy();
      console.log(`[Boot] Port ${port} check timed out`);
      resolve(false);
    });
  });
}

function checkVoiceStatus() {
  return new Promise((resolve) => {
    // Use 127.0.0.1 explicitly to force IPv4
    const request = http.get('http://127.0.0.1:8000/api/system/voice-status', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          resolve(res.statusCode === 200);
        } catch (e) {
          resolve(res.statusCode === 200);
        }
      });
    }).on('error', () => resolve(false));

    request.setTimeout(2000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

function createMainWindow() {
  // If window already exists, just focus it
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.focus();
    return;
  }

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173/');
  } else {
    mainWindow.loadURL(url.format({
      pathname: path.join(__dirname, '../dist/index.html'),
      protocol: 'file:',
      slashes: true
    }));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Aggressive memory cleanup: destroy on close instead of hide
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.destroy();
      mainWindow = null;
      console.log('[Electron] Main Dashboard destroyed to free RAM');
    }
    return false;
  });
}

function createQuickWindow() {
  quickWindow = new BrowserWindow({
    width: 320,
    height: 500,
    frame: false,
    resizable: false,
    transparent: true,
    alwaysOnTop: true,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      backgroundThrottling: true
    }
  });

  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  if (isDev) {
    quickWindow.loadURL('http://localhost:5173/quick');
  } else {
    quickWindow.loadURL(url.format({
      pathname: path.join(__dirname, '../dist/index.html'),
      protocol: 'file:',
      slashes: true,
      hash: 'quick'
    }));
  }

  quickWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      quickWindow.hide();
    }
    return false;
  });
}

function createTray() {
  const iconPath = path.join(__dirname, 'icon.png');
  try {
    tray = new Tray(iconPath);
    const contextMenu = Menu.buildFromTemplate([
      { 
        label: 'Open Quick Chat', 
        click: () => {
          if (quickWindow) quickWindow.show();
        } 
      },
      { 
        label: 'Open Dashboard', 
        click: () => {
          createMainWindow();
        } 
      },
      { type: 'separator' },
      { 
        label: 'System: ON / OFF', 
        type: 'checkbox',
        checked: systemState,
        click: (menuItem) => {
          systemState = menuItem.checked;
          console.log(`[Tray] System state toggled: ${systemState ? 'ON' : 'OFF'}`);
        }
      },
      { type: 'separator' },
      { 
        label: 'Quit Krystal', 
        click: () => { 
          isQuitting = true; 
          if (mainWindow) mainWindow.destroy();
          if (quickWindow) quickWindow.destroy();
          app.quit(); 
        } 
      }
    ]);
    tray.setToolTip('Krystal AI Interface');
    tray.setContextMenu(contextMenu);
    tray.on('double-click', () => {
      if (quickWindow) quickWindow.show();
    });
  } catch (e) {
    console.error('Tray icon error:', e.message);
  }
}

app.whenReady().then(() => {
  createBootWindow();
  createTray();
});

function registerGlobalHotkeys() {
  // Alt+Space: Toggle Quick Window with Focus logic
  const ret = globalShortcut.register('Alt+Space', () => {
    console.log('[Electron] Alt+Space pressed - toggling Quick Window');
    if (quickWindow) {
      if (quickWindow.isVisible() && quickWindow.isFocused()) {
        quickWindow.hide();
      } else {
        quickWindow.show();
        quickWindow.focus();
      }
    }
  });

  if (!ret) {
    console.error('[Electron] Failed to register Alt+Space hotkey');
  } else {
    console.log('[Electron] Alt+Space hotkey registered successfully');
  }
}

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => { isQuitting = true; });
