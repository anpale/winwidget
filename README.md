# Browser Agent

A hidden (headless) Edge/Chromium browser you control from a small command console.

- `agent.py` – background process that owns the browser and listens on `127.0.0.1:8765` (token-protected).
- `console.py` – command prompt that sends commands to the agent; screenshots are saved to `%LOCALAPPDATA%\BrowserAgent\shots`.

## Use the installer (Windows 11)
Run `BrowserAgentSetup.exe`, then open **Browser Agent Console** from the Start Menu.

    agent> open https://example.com
    agent> title
    agent> screenshot --show
    agent> quit

The browser defaults to the Edge that ships with Windows 11 (`BROWSER_CHANNEL=msedge`).
Set `BROWSER_CHANNEL=` (empty) to use Playwright's Chromium instead (`playwright install chromium`).

## Commands
See `help` in the console. Login: set `APP_USER` / `APP_PASS` in the agent's environment, then
`login <url> <user-selector> <pass-selector> <submit-selector>`. The profile (cookies) persists in `%LOCALAPPDATA%\BrowserAgent\profile`.

## Run from source
    pip install -r requirements.txt
    python console.py            # starts the agent if needed

## Build the installer yourself
Windows with Python 3.12+ and Inno Setup 6: `./build.ps1` -> `installer\BrowserAgentSetup.exe`.
Or push this folder to GitHub: the workflow in `.github/workflows/build.yml` builds it and publishes the installer as a downloadable artifact.

Only automate sites you own or are permitted to automate. The installer is unsigned, so SmartScreen will warn.
