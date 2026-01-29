const puppeteer = require('puppeteer');

async function getStock() {
    const browser = await puppeteer.launch({ headless: "new" });
    const page = await browser.newPage();
    
    try {
        await page.goto('https://fruityblox.com/stock', { waitUntil: 'networkidle2' });

        // This extracts the stock data directly from the browser's memory
        const stockData = await page.evaluate(() => {
            return window.__NEXT_DATA__?.props?.pageProps?.initialState?.stock;
        });

        if (!stockData) return "❌ Error: Could not find stock data.";

        let report = "🍎 **FRUITYBLOX LIVE STOCK** 🍎\n";
        ['normal', 'mirage'].forEach(type => {
            const fruits = stockData[type] || [];
            const reset = stockData[`${type}Status`] || "Unknown";
            report += `\n**--- ${type.toUpperCase()} STOCK ---**\n🕒 Reset: ${reset}\n`;
            report += fruits.length ? fruits.map(f => `• ${f.name} ($${f.price.toLocaleString()})`).join('\n') : "No fruits listed.";
            report += "\n";
        });

        return report;
    } catch (e) {
        return `⚠️ Script Error: ${e.message}`;
    } finally {
        await browser.close();
    }
}

async function sendToDiscord(content) {
    const webhookUrl = process.env.DISCORD_WEBHOOK;
    if (!webhookUrl) return console.log("Webhook missing!");
    
    await fetch(webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content })
    });
}

getStock().then(sendToDiscord);
