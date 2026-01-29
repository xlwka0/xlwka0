const puppeteer = require('puppeteer');

async function getStock() {
    console.log("🚀 Launching Browser...");
    const browser = await puppeteer.launch({
        headless: "new",
        args: [
            '--no-sandbox', 
            '--disable-setuid-sandbox', 
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    });

    const page = await browser.newPage();
    try {
        // Use a real browser user agent to avoid being blocked
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        console.log("🌐 Loading FruityBlox Stock...");
        // Wait until the network is mostly idle
        await page.goto('https://fruityblox.com/stock', { waitUntil: 'networkidle2', timeout: 60000 });

        // IMPORTANT: Wait for any div to appear so we know the page isn't blank
        await page.waitForSelector('div', { timeout: 15000 });

        console.log("📊 Extracting visual text...");
        const report = await page.evaluate(() => {
            let finalMsg = "🍎 **FRUITYBLOX LIVE STOCK** 🍎\n";
            
            // This grabs all elements that might be headers
            const sections = Array.from(document.querySelectorAll('h1, h2, h3, div'));
            
            // Look for "Normal Stock" or "Mirage Stock" in the text
            sections.forEach(el => {
                const text = el.innerText.toUpperCase();
                if ((text.includes('NORMAL') || text.includes('MIRAGE')) && text.includes('STOCK')) {
                    // Get the text from the box containing this stock
                    const parent = el.closest('div'); 
                    if (parent) {
                        finalMsg += `\n**--- ${text} ---**\n`;
                        // Extract fruit names (usually lines that don't have ":" in them)
                        const lines = parent.innerText.split('\n')
                            .filter(line => line.length > 3 && !line.includes('Stock') && !line.includes('Next Reset'));
                        
                        finalMsg += lines.join('\n') + '\n';
                    }
                }
            });
            return finalMsg;
        });

        // If the report is empty, the scraper failed to find the text
        if (report.length < 50) throw new Error("Could not find stock text on page.");
        return report;

    } catch (e) {
        console.error("❌ Scraper Error:", e.message);
        return `⚠️ **Scraper Error:** The site structure changed. (${e.message})`;
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
