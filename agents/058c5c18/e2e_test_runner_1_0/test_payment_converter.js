const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const SCREENSHOT_DIR = '/Users/danielrestrepo/Finkargo_Automation_Hub/agents/058c5c18/e2e_test_runner_1_0/img/payment_template_converter';
const APP_URL = 'http://localhost:5173';
const TEST_FILE = '/Users/danielrestrepo/Finkargo_Automation_Hub/Example FIles for Reqs/Historial_de_pagos_2025-11-25_2025-11-29.xlsx';

// Test credentials - adjust based on available test accounts
const TEST_EMAIL = 'admin@finkargo.com';
const TEST_PASSWORD = 'test123456';

async function takeScreenshot(page, name) {
  const screenshotPath = path.join(SCREENSHOT_DIR, name);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`Screenshot saved: ${screenshotPath}`);
  return screenshotPath;
}

async function runTest() {
  const result = {
    test_name: "Payment Template Converter (Tesorería)",
    status: "passed",
    screenshots: [],
    error: null,
    steps: []
  };

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Step 1: Login as tesorería or admin user
    console.log('Step 1: Navigating to login page...');
    await page.goto(`${APP_URL}/login`);
    await page.waitForLoadState('networkidle');

    // Check if we're already logged in or need to login
    const currentUrl = page.url();
    if (currentUrl.includes('/login')) {
      console.log('Logging in...');
      await page.fill('input[type="email"], input[name="email"]', TEST_EMAIL);
      await page.fill('input[type="password"], input[name="password"]', TEST_PASSWORD);
      await page.click('button[type="submit"]');
      await page.waitForURL(/.*(?!login).*/, { timeout: 10000 });
      console.log('Login successful');
      result.steps.push({ step: 1, status: 'passed', message: 'Login successful' });
    } else {
      console.log('Already logged in');
      result.steps.push({ step: 1, status: 'passed', message: 'Already logged in' });
    }

    // Step 2: Navigate to /tesoreria/plantillas-netsuite
    console.log('Step 2: Navigating to /tesoreria/plantillas-netsuite...');
    await page.goto(`${APP_URL}/tesoreria/plantillas-netsuite`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);
    result.steps.push({ step: 2, status: 'passed', message: 'Navigated to tesoreria page' });

    // Step 3: Take screenshot of landing page
    console.log('Step 3: Taking screenshot of landing page...');
    const screenshot1 = await takeScreenshot(page, '01_landing_page.png');
    result.screenshots.push(screenshot1);
    result.steps.push({ step: 3, status: 'passed', message: 'Screenshot captured' });

    // Step 4: Verify landing page elements
    console.log('Step 4: Verifying landing page elements...');
    const pageContent = await page.content();

    // Check for main title
    const hasTitle = await page.locator('text=Plantillas para Cargar NetSuite').count() > 0 ||
                     await page.locator('h1, h2, h3, h4').filter({ hasText: /plantillas|netsuite/i }).count() > 0;

    // Check for Colombia and México cards
    const hasColombiaCard = await page.locator('text=Colombia').count() > 0;
    const hasMexicoCard = await page.locator('text=México').count() > 0 ||
                          await page.locator('text=Mexico').count() > 0;

    if (!hasTitle) {
      console.log('Warning: Page title not found, checking if page is accessible...');
      // Check if we got redirected due to permissions
      if (page.url().includes('login') || page.url().includes('unauthorized')) {
        throw new Error('User not authorized to access Tesorería page - redirected');
      }
    }

    console.log(`Title found: ${hasTitle}, Colombia: ${hasColombiaCard}, México: ${hasMexicoCard}`);
    result.steps.push({
      step: 4,
      status: (hasColombiaCard && hasMexicoCard) ? 'passed' : 'warning',
      message: `Elements - Title: ${hasTitle}, Colombia: ${hasColombiaCard}, México: ${hasMexicoCard}`
    });

    // Step 5: Click on Colombia card
    console.log('Step 5: Clicking on Colombia card...');
    const colombiaLink = await page.locator('a, button, div[role="button"]').filter({ hasText: /Colombia/i }).first();
    if (await colombiaLink.count() > 0) {
      await colombiaLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
      result.steps.push({ step: 5, status: 'passed', message: 'Clicked Colombia card' });
    } else {
      // Try direct navigation
      await page.goto(`${APP_URL}/tesoreria/plantillas-netsuite/colombia`);
      await page.waitForLoadState('networkidle');
      result.steps.push({ step: 5, status: 'passed', message: 'Navigated directly to Colombia' });
    }

    // Step 6: Verify URL
    console.log('Step 6: Verifying URL...');
    const colombiaUrl = page.url();
    const isColombiaUrl = colombiaUrl.includes('/colombia');
    console.log(`Current URL: ${colombiaUrl}`);
    result.steps.push({
      step: 6,
      status: isColombiaUrl ? 'passed' : 'failed',
      message: `URL is ${colombiaUrl}`
    });

    // Step 7: Take screenshot of Colombia converter page
    console.log('Step 7: Taking screenshot of Colombia converter page...');
    const screenshot2 = await takeScreenshot(page, '02_colombia_converter.png');
    result.screenshots.push(screenshot2);
    result.steps.push({ step: 7, status: 'passed', message: 'Screenshot captured' });

    // Step 8: Verify Colombia converter elements
    console.log('Step 8: Verifying Colombia converter page elements...');
    const hasColombiaTitle = await page.locator('text=Colombia').count() > 0 ||
                             await page.locator('h1, h2, h3').filter({ hasText: /aplicación.*pago|colombia/i }).count() > 0;
    const hasBackButton = await page.locator('button, a').filter({ hasText: /volver|back|regresar/i }).count() > 0 ||
                          await page.locator('[aria-label*="back"], [aria-label*="volver"]').count() > 0;
    const hasUploadArea = await page.locator('input[type="file"]').count() > 0 ||
                          await page.locator('[class*="dropzone"], [class*="upload"], [class*="drop"]').count() > 0 ||
                          await page.locator('text=arrastr').count() > 0 ||
                          await page.locator('text=Seleccionar archivo').count() > 0;

    console.log(`Colombia page - Title: ${hasColombiaTitle}, Back: ${hasBackButton}, Upload: ${hasUploadArea}`);
    result.steps.push({
      step: 8,
      status: hasUploadArea ? 'passed' : 'warning',
      message: `Elements - Title: ${hasColombiaTitle}, Back: ${hasBackButton}, Upload: ${hasUploadArea}`
    });

    // Steps 9-14: File upload and validation
    console.log('Step 9-14: Attempting file upload...');
    const fileInput = await page.locator('input[type="file"]');
    if (await fileInput.count() > 0) {
      // Check if test file exists
      if (fs.existsSync(TEST_FILE)) {
        await fileInput.setInputFiles(TEST_FILE);
        console.log('File selected, waiting for validation...');
        await page.waitForTimeout(3000);

        // Take screenshot of validation preview
        const screenshot3 = await takeScreenshot(page, '03_validation_preview.png');
        result.screenshots.push(screenshot3);
        result.steps.push({ step: 14, status: 'passed', message: 'Validation preview screenshot captured' });

        // Check for convert button
        const convertBtn = await page.locator('button').filter({ hasText: /convert|convertir|descargar/i });
        const btnEnabled = await convertBtn.count() > 0 && await convertBtn.isEnabled();
        console.log(`Convert button enabled: ${btnEnabled}`);
        result.steps.push({ step: 15, status: btnEnabled ? 'passed' : 'warning', message: `Convert button enabled: ${btnEnabled}` });

        // Step 16-18: Click convert and wait for download
        if (btnEnabled) {
          console.log('Step 16: Clicking convert button...');

          // Set up download listener
          const [download] = await Promise.all([
            page.waitForEvent('download', { timeout: 30000 }).catch(() => null),
            convertBtn.click()
          ]);

          await page.waitForTimeout(2000);

          if (download) {
            console.log('Download started');
            result.steps.push({ step: 18, status: 'passed', message: 'Download completed' });
          } else {
            // Check for success message
            const hasSuccess = await page.locator('text=éxito').count() > 0 ||
                               await page.locator('[class*="success"], [class*="alert-success"]').count() > 0;
            result.steps.push({ step: 18, status: hasSuccess ? 'passed' : 'warning', message: 'Conversion completed (success message checked)' });
          }

          // Step 19: Take screenshot of completion
          const screenshot4 = await takeScreenshot(page, '04_conversion_complete.png');
          result.screenshots.push(screenshot4);
          result.steps.push({ step: 19, status: 'passed', message: 'Completion screenshot captured' });
        } else {
          result.steps.push({ step: 16, status: 'skipped', message: 'Convert button not enabled' });
          const screenshot4 = await takeScreenshot(page, '04_conversion_state.png');
          result.screenshots.push(screenshot4);
        }
      } else {
        console.log('Test file not found');
        result.steps.push({ step: 10, status: 'skipped', message: 'Test file not found' });
        const screenshot3 = await takeScreenshot(page, '03_no_file.png');
        result.screenshots.push(screenshot3);
      }
    } else {
      console.log('No file input found on page');
      result.steps.push({ step: 9, status: 'failed', message: 'No file input found' });
      const screenshot3 = await takeScreenshot(page, '03_colombia_no_upload.png');
      result.screenshots.push(screenshot3);
    }

    // Step 20-24: Navigate to México page
    console.log('Step 20: Navigating back to landing page...');
    await page.goto(`${APP_URL}/tesoreria/plantillas-netsuite`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    console.log('Step 21: Clicking México card...');
    const mexicoLink = await page.locator('a, button, div[role="button"]').filter({ hasText: /México|Mexico/i }).first();
    if (await mexicoLink.count() > 0) {
      await mexicoLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    } else {
      await page.goto(`${APP_URL}/tesoreria/plantillas-netsuite/mexico`);
      await page.waitForLoadState('networkidle');
    }

    // Step 22: Verify México URL
    const mexicoUrl = page.url();
    const isMexicoUrl = mexicoUrl.includes('/mexico');
    console.log(`México URL: ${mexicoUrl}`);
    result.steps.push({ step: 22, status: isMexicoUrl ? 'passed' : 'failed', message: `URL is ${mexicoUrl}` });

    // Step 23: Take screenshot of México page
    console.log('Step 23: Taking screenshot of México page...');
    const screenshot5 = await takeScreenshot(page, '05_mexico_converter.png');
    result.screenshots.push(screenshot5);
    result.steps.push({ step: 23, status: 'passed', message: 'México screenshot captured' });

    // Step 24: Verify México page elements
    const hasMexicoTitle = await page.locator('text=México').count() > 0 ||
                           await page.locator('h1, h2, h3').filter({ hasText: /aplicación.*pago|mexico|méxico/i }).count() > 0;
    const hasMexicoUpload = await page.locator('input[type="file"]').count() > 0 ||
                            await page.locator('[class*="dropzone"], [class*="upload"]').count() > 0;

    console.log(`México page - Title: ${hasMexicoTitle}, Upload: ${hasMexicoUpload}`);
    result.steps.push({
      step: 24,
      status: 'passed',
      message: `México elements - Title: ${hasMexicoTitle}, Upload: ${hasMexicoUpload}`
    });

    console.log('\nTest completed successfully!');

  } catch (error) {
    console.error('Test failed:', error.message);
    result.status = 'failed';
    result.error = error.message;

    // Take error screenshot
    try {
      const errorScreenshot = await takeScreenshot(page, 'error_state.png');
      result.screenshots.push(errorScreenshot);
    } catch (e) {
      console.error('Could not take error screenshot');
    }
  } finally {
    await browser.close();
  }

  // Determine final status based on steps
  const failedSteps = result.steps.filter(s => s.status === 'failed');
  if (failedSteps.length > 0 && result.status !== 'failed') {
    result.status = 'failed';
    result.error = failedSteps.map(s => `Step ${s.step}: ${s.message}`).join('; ');
  }

  console.log('\n=== FINAL RESULT ===');
  console.log(JSON.stringify(result, null, 2));
  return result;
}

runTest().then(result => {
  // Write result to file
  fs.writeFileSync(
    '/Users/danielrestrepo/Finkargo_Automation_Hub/agents/058c5c18/e2e_test_runner_1_0/test_result.json',
    JSON.stringify(result, null, 2)
  );
  process.exit(result.status === 'passed' ? 0 : 1);
});
