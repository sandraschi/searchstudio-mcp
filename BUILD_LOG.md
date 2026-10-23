# BUILD_LOG - SearchStudio Tauri/NSIS builds

Running record for installer builds (fleet NSIS gate: fix gaps before building,
log failures and fixes here).

## 2026-10-23 - v0.2.0 first NSIS build - SUCCESS

- Toolchain: cargo/rustc 1.99.0, tauri-cli 2.12.4 (cargo install), NSIS 3.x
  (C:\Program Files (x86)\NSIS), WiX not needed (nsis target only).
- Scaffold: webapp/src-tauri (Cargo.toml, tauri.conf.json, build.rs,
  src/main.rs, capabilities/default.json). installMode currentUser (no admin),
  embedBootstrapper WebView2, targets ["nsis"] only.
- Icons: `cargo tauri icon` from mcpb/assets/icon.png (256px source, upscaled -
  acceptable v1, refresh with a 1024px master when one exists).
- Failures hit:
  1. `import.meta.env` TS error - missing webapp/src/vite-env.d.ts. Fixed by
     adding the standard `/// <reference types="vite/client" />` file.
- Production API base: webapp built with VITE_API_BASE=http://127.0.0.1:11226
  (verified baked into dist JS); backend CORS-allows tauri://localhost +
  tauri.localhost (both schemes). Dev flow unchanged (Vite proxy, no env).
- External links: opener plugin + `opener:default` capability so target=_blank
  opens in the system browser instead of hijacking the webview.
- Output: SearchStudio_0.2.0_x64-setup.exe, 3.65 MiB.
- Smoke test: silent install (/S) to %LOCALAPPDATA%\SearchStudio, launched
  (window "SearchStudio" up), silent uninstall clean. Backend was down during
  the test - the shell showed its backend-down state, as designed.
- Repro: `just tauri-build` (recipe added to justfile).
