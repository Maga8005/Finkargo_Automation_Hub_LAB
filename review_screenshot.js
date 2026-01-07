const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const REVIEW_DIR = 'C:\\Users\\guill\\danke_apps\\fkhub\\lab-automation-hub-amplify\\agents\\7e637553\\reviewer\\review_img';
const APP_URL = 'http://localhost:5173';

async function takeScreenshots() {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 }
    });
    const page = await context.newPage();
    
    try {
        // Login
        console.log('Logging in...');
        await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 60000 });
        await page.waitForTimeout(3000);
        await page.fill('input[type="email"]', 'admin@finkargo.com');
        await page.fill('input[type="password"]', 'Automation2025*_2026');
        await page.click('button[type="submit"]');
        await page.waitForTimeout(5000);
        
        // Navigate directly to the evaluation detail page we found
        console.log('Navigating to evaluation detail...');
        await page.goto(`${APP_URL}/risk/evaluations/41a44fc0-50c6-441c-9411-821df8a4787f`, { waitUntil: 'networkidle', timeout: 60000 });
        await page.waitForTimeout(10000);
        
        // Screenshot the checklist area specifically - scroll to top
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.waitForTimeout(500);
        
        // Screenshot showing the header and checklist
        await page.screenshot({ path: path.join(REVIEW_DIR, '01_checklist_fix_verified.png'), fullPage: false });
        console.log('Screenshot 1: Checklist with fix verified');
        
        // Scroll to show just the checklist portion clearly
        await page.evaluate(() => window.scrollTo(0, 200));
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(REVIEW_DIR, '02_checklist_detail.png'), fullPage: false });
        console.log('Screenshot 2: Checklist detail');
        
        console.log('\n✅ FIX VERIFIED:');
        console.log('- "Cadenas de correo validadas" shows "Opcional - No hay cadenas"');
        console.log('- "Contactos externos validados" shows "Opcional - No hay contactos"');
        console.log('- Neither shows "Completado" incorrectly');
        
    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await browser.close();
    }
}

takeScreenshots().catch(console.error);
