const puppeteer = require('puppeteer');

async function getStock() {
    console.log("🚀 Starting scraper...");
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
        // Set a realistic user agent
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        
        console.log("🌐 Navigating to FruityBlox...");
        await page.goto('https://fruityblox.com/stock', { waitUntil: 'networkidle2', timeout: 60000 });

        console.log("🔍 Extracting data...");
        const stockData = await page.evaluate(() => {
            // FruityBlox stores its data in this global variable
            return window.__NEXT_DATA__?.props?.pageProps?.initialState?.stock;
        });

        if (!stockData) {
            throw new Error("Could not find stock data in __NEXT_DATA__");
        }

        let report = "🍎 **FRUITYBLOX LIVE STOCK** 🍎\n";

        ['normal', 'mirage'].forEach(type => {
            const title = type.toUpperCase();
            const reset = stockData[`${type}Status`] || "Unknown";
            const fruits = stockData[type] || [];

            report += `\n**--- ${title} STOCK ---**\n🕒 Next Reset: ${reset}\n`;

            if (fruits.length > 0) {
                const list = fruits.map(f => `• ${f.name} ($${f.price.toLocaleString()})`).join('\n');
                report += list;
            } else {
                report += "_No fruits currently in stock._";
            }
            report += "\n";
        });

        return report;

    } catch (error) {
        console.error("❌ Scraper Error:", error.message);
        return `⚠️ **Scraper Error:** ${error.message}`;
    } finally {
        await browser.close();
        console.log("🔒 Browser closed.");
    }
}

async function sendToDiscord(content) {
    const webhookUrl = process.env.DISCORD_WEBHOOK;
    if (!webhookUrl) {
        console.log("❌ Error: DISCORD_WEBHOOK environment variable is missing.");
        return;
    }

    try {
        const response = await fetch(webhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });
        if (response.ok) {
            console.log("✅ Message sent to Discord!");
        } else {
            console.log("❌ Discord returned an error:", response.status);
        }
    } catch (error) {
        console.error("❌ Webhook Error:", error.message);
    }
}

// Run the bot
getStock().then(sendToDiscord);
