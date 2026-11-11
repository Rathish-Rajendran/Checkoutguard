import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'tests',workers:1,use:{baseURL:process.env.PLAYWRIGHT_BASE_URL||'http://127.0.0.1:5173',headless:true,launchOptions:{executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']},viewport:{width:1440,height:1000}},reporter:'list'});
