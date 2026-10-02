"""Headless browser agent: owns Edge/Chromium and executes commands sent by console.py."""
import asyncio
import base64
import json
import logging
import os
import secrets
import sys
from urllib.parse import urlparse

from playwright.async_api import async_playwright

import common

logging.basicConfig(
    filename=common.LOG_FILE, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger("agent")


class Agent:
    """Each cmd_<name> method is a console command; it returns (text, png_bytes_or_None)."""

    def __init__(self, ctx, stop):
        self.ctx = ctx
        self.stop = stop
        self.page = ctx.pages[0] if ctx.pages else None

    async def handle(self, cmd, args):
        fn = getattr(self, "cmd_" + cmd, None)
        if fn is None:
            raise ValueError(f"unknown command: {cmd}")
        if self.page is None or self.page.is_closed():
            self.page = await self.ctx.new_page()
        return await fn(*args)

    async def _summary(self):
        return f"{self.page.url} | {await self.page.title()}", None

    async def cmd_ping(self):
        return "pong", None

    async def cmd_open(self, url):
        if "://" not in url:
            url = "https://" + url
        if urlparse(url).scheme not in ("http", "https"):
            raise ValueError("only http/https URLs are allowed")
        await self.page.goto(url, wait_until="load")
        return await self._summary()

    async def cmd_screenshot(self, mode=""):
        png = await self.page.screenshot(full_page=(mode == "full"))
        return f"{len(png)} bytes", png

    async def cmd_click(self, selector):
        await self.page.click(selector, timeout=10_000)
        return await self._summary()

    async def cmd_type(self, selector, *words):
        await self.page.fill(selector, " ".join(words), timeout=10_000)
        return "ok", None

    async def cmd_press(self, key):
        await self.page.keyboard.press(key)
        return "ok", None

    async def cmd_login(self, url, user_selector, pass_selector, submit_selector):
        user, password = os.getenv("APP_USER"), os.getenv("APP_PASS")
        if not user or not password:
            raise ValueError("APP_USER / APP_PASS must be set in the agent's environment")
        await self.cmd_open(url)
        await self.page.fill(user_selector, user, timeout=10_000)
        await self.page.fill(pass_selector, password, timeout=10_000)
        await self.page.click(submit_selector, timeout=10_000)
        await self.page.wait_for_load_state("load")
        return await self._summary()

    async def cmd_text(self, selector="body"):
        text = await self.page.inner_text(selector, timeout=10_000)
        return text[:20_000], None

    async def cmd_url(self):
        return self.page.url, None

    async def cmd_title(self):
        return await self.page.title(), None

    async def cmd_wait(self, target):
        if target.isdigit():
            await self.page.wait_for_timeout(int(target))
        else:
            await self.page.wait_for_selector(target, timeout=30_000)
        return "ok", None

    async def cmd_back(self):
        await self.page.go_back()
        return await self._summary()

    async def cmd_reload(self):
        await self.page.reload()
        return await self._summary()

    async def cmd_quit(self):
        self.stop.set()
        return "bye", None


async def main():
    token = secrets.token_urlsafe(24)
    stop = asyncio.Event()
    lock = asyncio.Lock()
    agent = None

    async def serve(reader, writer):
        try:
            while line := await reader.readline():
                try:
                    req = json.loads(line)
                    if not secrets.compare_digest(str(req.get("token", "")), token):
                        raise PermissionError("bad token")
                    args = [str(a) for a in req.get("args", [])]
                    async with lock:
                        text, png = await agent.handle(str(req["cmd"]), args)
                    reply = {"ok": True, "result": text}
                    if png:
                        reply["image_b64"] = base64.b64encode(png).decode()
                except Exception as e:  # keep the agent alive whatever a command does
                    log.info("command failed: %s", e)
                    reply = {"ok": False, "error": f"{type(e).__name__}: {e}"[:500]}
                writer.write((json.dumps(reply) + "\n").encode())
                await writer.drain()
        finally:
            writer.close()

    # Bind first so a second agent fails fast instead of launching another browser.
    server = await asyncio.start_server(serve, common.HOST, common.PORT, limit=1 << 20)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(common.PROFILE_DIR),
            channel=common.CHANNEL or None,
            headless=True,
            viewport={"width": 1280, "height": 800},
        )
        agent = Agent(ctx, stop)
        common.TOKEN_FILE.write_text(token)
        if sys.platform != "win32":
            common.TOKEN_FILE.chmod(0o600)
        log.info("agent ready on %s:%s (channel=%r)", common.HOST, common.PORT, common.CHANNEL)
        try:
            await stop.wait()
        finally:
            server.close()
            common.TOKEN_FILE.unlink(missing_ok=True)
            await ctx.close()
    log.info("agent stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        log.exception("agent crashed")
        sys.exit(1)
