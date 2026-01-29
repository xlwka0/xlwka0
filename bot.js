const puppeteer = require('puppeteer');

async function getStock() {
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    try {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36');
        await page.goto('https://fruityblox.com/stock', { waitUntil: 'networkidle2', timeout: 60000 });

        // FIX: Wait explicitly for the "Stock" text to be visible
        await page.waitForFunction(
            () => document.body.innerText.toUpperCase().includes('STOCK'),
            { timeout: 30000 }
        );

        const report = await page.evaluate(() => {
            let finalMsg = "🍎 **FRUITYBLOX LIVE STOCK** 🍎\n";
            // Grab the main text from the page content
            const content = document.body.innerText;
            const lines = content.split('\n');
            
            // Look for keywords and capture the next 10 lines after them
            let found = false;
            lines.forEach((line, index) => {
                if (line.toUpperCase().includes('STOCK')) {
                    finalMsg += `\n**--- ${line} ---**\n`;
                    finalMsg += lines.slice(index + 1, index + 8).join('\n') + '\n';
                    found = true;
                }
            });
            return found ? finalMsg : null;
        });

        console.log("Scraped Content:", report); // Check this in GitHub Actions logs!
        return report;
    } catch (e) {
        console.error("Scraper failed:", e.message);
        return null;
    } finally {
        await browser.close();
    }
}

async function sendToDiscord(content) {
    if (!content) {
        console.log("⚠️ No content found to send. Skipping Discord.");
        return;
    }
    const webhookUrl = process.env.DISCORD_WEBHOOK;
    await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
}

getStock().then(sendToDiscord);
