const puppeteer = require('puppeteer');

async function getStock() {
    console.log("🚀 Launching Browser...");
    const browser = await puppeteer.launch({
        headless: "new",
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    try {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36');
        
        console.log("🌐 Loading FruityBlox Stock...");
        await page.goto('https://fruityblox.com/stock', { waitUntil: 'networkidle2', timeout: 60000 });

        // Wait for the specific stock elements to load
        await page.waitForSelector('div', { timeout: 10000 });

        console.log("📊 Extracting visual data...");
        const report = await page.evaluate(() => {
            let finalMsg = "🍎 **FRUITYBLOX LIVE STOCK** 🍎\n";
            
            // Find all headings (Normal Stock, Mirage Stock)
            const headings = Array.from(document.querySelectorAll('h2, h1, .text-xl'));
            
            headings.forEach(h => {
                const title = h.innerText.toUpperCase();
                if (title.includes('STOCK')) {
                    finalMsg += `\n**--- ${title} ---**\n`;
                    
                    // Look for the next reset time near this heading
                    const container = h.parentElement;
                    const timer = container.innerText.match(/\d{1,2}:\d{2}:\d{2}/) || ["Unknown"];
                    finalMsg += `🕒 Reset: ${timer[0]}\n`;

                    // Get all fruits in this specific section
                    const fruits = Array.from(container.querySelectorAll('div'))
                        .map(d => d.innerText)
                        .filter(txt => txt.length > 2 && !txt.includes(':') && !txt.includes('Stock'));
                    
                    if (fruits.length > 0) {
                        finalMsg += fruits.map(f => `• ${f}`).join('\n') + '\n';
                    } else {
                        finalMsg += "_Data loading... check back soon._\n";
                    }
                }
            });
            return finalMsg;
        });

        return report;

    } catch (e) {
        return `⚠️ **Scraper Error:** Site might be loading slowly or structure changed. (${e.message})`;
    } finally {
        await browser.close();
    }
}

async function sendToDiscord(content) {
    const webhookUrl = process.env.DISCORD_WEBHOOK;
    if (!webhookUrl) return console.log("Missing Webhook Secret!");
    await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
}

getStock().then(sendToDiscord);
