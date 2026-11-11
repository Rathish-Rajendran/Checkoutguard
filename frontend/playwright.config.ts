import { existsSync } from 'node:fs';
import { defineConfig } from '@playwright/test';

const systemChromium = '/usr/bin/chromium';
const executablePath = process.env.CHROMIUM_PATH
  || (existsSync(systemChromium) ? systemChromium : undefined);

export default defineConfig({
  testDir: 'tests',
  workers: 1,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://127.0.0.1:5173',
    headless: true,
    launchOptions: { executablePath },
    viewport: { width: 1440, height: 1000 },
  },
  reporter: 'list',
});
