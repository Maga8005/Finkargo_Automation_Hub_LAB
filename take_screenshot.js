const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// Connect to local backend and use production Supabase URL
const FRONTEND_URL = 'http://192.168.0.198:5175';
const SCREENSHOT_DIR = 'C:/Users/guill/danke_apps/fkhub/lab-automation-hub-amplify/agents/2f90db93/reviewer/review_img';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function takeScreenshots() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  try {
    // 1. Navigate to login page
    console.log('Navigating to login page...');
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 2000));

    // Screenshot 1: Login page
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_login_page.png'), fullPage: false });
    console.log('Screenshot 1 saved: 01_login_page.png');

    // 2. Login
    console.log('Logging in...');
    await page.waitForSelector('input[type="email"]', { timeout: 10000 });
    await page.type('input[type="email"]', 'admin@finkargo.com');
    await page.type('input[type="password"]', 'Automation2025*_2026');

    // Click login button
    const buttons = await page.$$('button');
    for (const button of buttons) {
      const text = await page.evaluate(el => el.innerText, button);
      if (text.toLowerCase().includes('iniciar') || text.toLowerCase().includes('login')) {
        await button.click();
        break;
      }
    }

    await new Promise(r => setTimeout(r, 4000));

    // 3. Navigate to risk dashboard
    console.log('Navigating to risk dashboard...');
    await page.goto(FRONTEND_URL + '/risk/dashboard', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 3000));

    // Screenshot 2: Risk dashboard
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_risk_dashboard.png'), fullPage: false });
    console.log('Screenshot 2 saved: 02_risk_dashboard.png');

    // 4. Create a new evaluation first
    console.log('Creating new evaluation...');
    const allButtons = await page.$$('button');
    for (const button of allButtons) {
      const text = await page.evaluate(el => el.innerText, button);
      if (text && text.toLowerCase().includes('nueva')) {
        console.log('Clicking new evaluation button:', text);
        await button.click();
        await new Promise(r => setTimeout(r, 2000));
        break;
      }
    }

    // Screenshot 3: New evaluation dialog
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_new_evaluation_dialog.png'), fullPage: false });
    console.log('Screenshot 3 saved: 03_new_evaluation_dialog.png');

    console.log('All screenshots captured!');

  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'error_state.png'), fullPage: false });
  } finally {
    await browser.close();
  }
}

takeScreenshots().catch(console.error);
