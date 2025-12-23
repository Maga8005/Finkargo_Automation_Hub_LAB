const { chromium } = require('@playwright/test');
const path = require('path');

const REVIEW_IMG_DIR = './agents/443ac6db/reviewer/review_img';
const SCREENSHOT_WIDTH = 1600;
const SCREENSHOT_HEIGHT = 1000;

async function takeScreenshots() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: SCREENSHOT_WIDTH, height: SCREENSHOT_HEIGHT }
  });
  const page = await context.newPage();
  
  console.log('Navigating to login page...');
  await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  // Login with test credentials
  console.log('Logging in...');
  await page.fill('input[name="email"]', 'test-risk@finkargo.com');
  await page.fill('input[name="password"]', 'Test123!');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(3000);
  
  // Navigate to risk dashboard
  console.log('Navigating to risk dashboard...');
  await page.goto('http://localhost:5173/risk/dashboard', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);
  
  // Try to find an evaluation to click on
  const evaluationLink = await page.locator('table tbody tr').first();
  if (await evaluationLink.isVisible()) {
    console.log('Clicking on first evaluation...');
    await evaluationLink.click();
    await page.waitForTimeout(3000);
    
    // Take screenshot of detail page
    await page.screenshot({ path: path.join(REVIEW_IMG_DIR, '01_evaluation_detail_page.png'), fullPage: false });
    console.log('Screenshot 1: Evaluation detail page');
    
    // Click on Contacto Externo tab (4th tab, index 3)
    console.log('Looking for Contacto Externo tab...');
    const contactoTab = await page.locator('button[role="tab"]:has-text("Contacto Externo")');
    if (await contactoTab.isVisible()) {
      await contactoTab.click();
      await page.waitForTimeout(2000);
      
      // Take screenshot of External Contact tab
      await page.screenshot({ path: path.join(REVIEW_IMG_DIR, '02_external_contact_tab.png'), fullPage: false });
      console.log('Screenshot 2: External Contact tab');
      
      // Try to add a contact
      console.log('Adding a contact...');
      await page.fill('input[placeholder="contacto@empresa.com"]', 'test@azelis.com.co');
      await page.fill('input[placeholder="Juan Pérez"]', 'Juan Perez');
      await page.fill('input[placeholder="Información adicional..."]', 'Recibido via WhatsApp');
      
      // Take screenshot after filling form
      await page.screenshot({ path: path.join(REVIEW_IMG_DIR, '03_contact_form_filled.png'), fullPage: false });
      console.log('Screenshot 3: Contact form filled');
      
      // Click add button
      const addButton = await page.locator('button:has-text("Agregar Contacto")');
      if (await addButton.isVisible()) {
        await addButton.click();
        await page.waitForTimeout(3000);
        
        // Take screenshot after contact added
        await page.screenshot({ path: path.join(REVIEW_IMG_DIR, '04_contact_added.png'), fullPage: false });
        console.log('Screenshot 4: Contact added');
      }
    } else {
      console.log('Contacto Externo tab not found');
    }
  } else {
    console.log('No evaluations found in dashboard');
  }
  
  await browser.close();
  console.log('Screenshots complete!');
}

takeScreenshots().catch(console.error);
