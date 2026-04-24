import os
import asyncio
import re
from playwright.async_api import async_playwright
import datetime

class MeetingBot:
    def __init__(self, meeting_url, bot_name="Roman-Scribe Assistant (Recording)", log_callback=None):
        self.meeting_url = meeting_url
        self.bot_name = bot_name
        self.log_callback = log_callback
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False
        self.video_path = None
        # Use E: drive for storage
        self.storage_dir = os.path.join("E:/notetaking", "recordings")
        os.makedirs(self.storage_dir, exist_ok=True)

    def log(self, msg):
        print(f"[BOT]: {msg}")
        if self.log_callback:
            self.log_callback(msg)

    async def start(self):
        try:
            self.log(f"Starting browser for {self.bot_name}...")
            self.playwright = await async_playwright().start()
            
            # Ensure Playwright finds its browsers on E: drive
            browser_path = os.getenv("PLAYWRIGHT_BROWSERS_PATH", "E:/notetaking/.cache/playwright")
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_path
            
            # Record video+audio to E: drive
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.video_save_path = os.path.join(self.storage_dir, f"meeting_{timestamp}")
            os.makedirs(self.video_save_path, exist_ok=True)

            user_data_dir = "E:/notetaking/.cache/scribe_profile"
            os.makedirs(user_data_dir, exist_ok=True)
            
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                record_video_dir=self.video_save_path,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--use-fake-ui-for-media-stream',
                    '--use-fake-device-for-media-stream',
                    '--start-maximized',
                    '--disable-infobars',
                    '--disable-gpu',
                    '--disable-dev-shm-usage',
                    '--blink-settings=imagesEnabled=true'
                ],
                no_viewport=True
            )
            
            self.page = self.context.pages[0]
            
            # Manual High-Fidelity Stealth Engine (Level 7)
            await self.page.add_init_script("""
                // 1. Hide WebDriver
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                
                // 2. Mock Hardware
                Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
                Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                
                // 3. Mock Chrome Runtime
                window.chrome = {
                    runtime: {
                        OnInstalledReason: { INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update' },
                        OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
                        PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
                        PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
                        PlatformNaclArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
                        RequestUpdateCheckStatus: { THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available' }
                    }
                };
                
                // 4. Mock Plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
                    ]
                });
                
                // 5. Mock Languages
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                
                // 6. Mock Permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
                );
            """)
            
            self.log(f"Bot started with Professional Chrome Profile (Profile 7)")
            self.log(f"Navigating to {self.meeting_url}...")
            await self.page.goto(self.meeting_url, wait_until="networkidle", timeout=60000)

            # Check for "You can't join this video call" block
            for entry_attempt in range(2):
                if await self.page.locator('text="You can\'t join this video call"').is_visible(timeout=5000):
                    self.log(f"REJECTED by Google (Attempt {entry_attempt+1}). Refreshing for a clean handshake...")
                    await asyncio.sleep(2)
                    await self.page.reload(wait_until="networkidle")
                    await asyncio.sleep(5)
                else: break

            self.log("Page loaded. Waiting for room to stabilize...")
            await asyncio.sleep(5)
            
            # Smart Joining Loop (Handles manual Google Logins gracefully)
            self.log("IMPORTANT: If you want to use your Google Account, click 'Sign in' NOW! The bot will wait for you to finish.")
            self.log("Starting Smart Join/Login Detection (Waiting up to 4 minutes)...")
            success = False
            
            for attempt in range(120): # 4 minutes total (allows ample time for 2FA login)
                try:
                    current_url = self.page.url
                    # If user is logging into Google, just wait and don't interfere
                    if "accounts.google.com" in current_url:
                        if attempt % 5 == 0:
                            self.log("User is logging in. Waiting patiently...")
                        await asyncio.sleep(2)
                        continue
                        
                    # Dismiss overlays (Got it / Dismiss / etc)
                    popups = self.page.locator('button:has-text("Got it"), button:has-text("Dismiss"), button:has-text("Continue without"), button[aria-label="Got it"]')
                    count = await popups.count()
                    for i in range(count):
                        try: await popups.nth(i).click(timeout=200)
                        except: pass

                    # If not logged in, there might be a name input
                    try:
                        name_inputs = await self.page.locator('input[aria-label="Your name"], input[placeholder="Your name"], input:not([type="hidden"])').count()
                        if name_inputs > 0:
                            name_input = self.page.locator('input[aria-label="Your name"], input[placeholder="Your name"], input:not([type="hidden"])').first
                            if await name_input.is_visible(timeout=500):
                                val = await name_input.input_value()
                                if self.bot_name not in val:
                                    await name_input.fill(self.bot_name)
                                    await self.page.keyboard.press("Enter")
                                    self.log("Name entered.")
                    except: pass

                    # Check for direct block text (Fast fail if rejected immediately)
                    try:
                        if await self.page.locator('text="You can\'t join"').is_visible(timeout=200):
                            self.log("Google blocked immediate entry. Attempting to refresh...")
                            await self.page.reload()
                            await asyncio.sleep(5)
                    except: pass

                    # Advanced JOIN button clicker
                    js_clicker = """
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button, [role="button"], span'));
                        const joinBtn = buttons.find(b => {
                            const t = (b.innerText || b.textContent || '').toLowerCase();
                            return (t.includes('join') || t.includes('ask') || t.includes('request')) && !t.includes('already');
                        });
                        if (joinBtn) { joinBtn.click(); return true; }
                        return false;
                    }"""
                    if await self.page.evaluate(js_clicker):
                        self.log(f"SUCCESS: Clicked JOIN (Attempt {attempt+1})")
                        success = True
                        break
                        
                except Exception as e:
                    # Ignore context destroyed errors during navigation (like coming back from login page)
                    pass
                    
                await asyncio.sleep(2)
                
            # Verification
            if success:
                self.log("Waiting for Host Admission...")
                try:
                    await self.page.wait_for_selector('video, button[aria-label*="microphone"]', timeout=40000)
                    self.log("JOINED: Bot is now active.")
                    self.is_running = True
                except:
                    self.log("Pending admission or verification failed. If you see the meeting, it worked!")
                    self.is_running = True
        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            # Don't stop immediately, let the user see the error in the window

    async def stop(self):
        self.log("Cleaning up and stopping bot...")
        try:
            if self.page: await self.page.close()
            if self.context: await self.context.close()
            if self.browser: await self.browser.close()
            if hasattr(self, 'playwright') and self.playwright:
                await asyncio.wait_for(self.playwright.stop(), timeout=3.0)
        except: pass
        self.is_running = False
        
        # Determine the video file path
        if os.path.exists(self.video_save_path):
            files = os.listdir(self.video_save_path)
            if files:
                self.video_path = os.path.join(self.video_save_path, files[0])
                self.log(f"Recording saved: {os.path.basename(self.video_path)}")
                return self.video_path
        return None
