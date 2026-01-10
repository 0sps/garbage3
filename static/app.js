const API_URL = '/api/trades';
const feedElement = document.getElementById('trade-feed');
const statsCount = document.getElementById('stats-count');
const statsValue = document.getElementById('stats-value');
const statsInsiders = document.getElementById('stats-insiders');

let lastTimestamp = 0;

async function fetchTrades() {
    try {
        const response = await fetch(API_URL);
        const trades = await response.json();

        updateStats(trades);
        renderFeed(trades);
    } catch (error) {
        console.error('Error fetching trades:', error);
    }
}

function updateStats(trades) {
    statsCount.textContent = trades.length;

    const totalValue = trades.reduce((acc, trade) => acc + parseFloat(trade.value), 0);
    statsValue.textContent = '$' + totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 });

    const insiderCount = trades.filter(t => t.flag && t.flag.includes('INSIDER')).length;
    statsInsiders.textContent = insiderCount;
}

function renderFeed(trades) {
    const insiderFeed = document.getElementById('insider-feed');
    const alertContainer = document.getElementById('alert-container');
    const normalFeed = document.getElementById('trade-feed');

    if (!insiderFeed || !normalFeed) return;

    // Split trades
    const insiders = trades.filter(t => t.flag && t.flag.includes('INSIDER'));
    const normal = trades.filter(t => !t.flag || !t.flag.includes('INSIDER'));

    // Render Insiders
    if (insiders.length > 0) {
        alertContainer.style.display = 'block';
        insiderFeed.innerHTML = renderItems(insiders);
    } else {
        // Keep section visible but show empty state or hide? 
        // User wants explicit sections. Let's keep it visible if that's the request, or hide if empty.
        // Re-reading request: "split... into two sections". 
        // Let's hide if empty to save space, OR show "No active alerts" to be explicit.
        // Let's go with showing it if we want to be very clear, but standard is hide.
        // However, user said "it doesn't split". If I hide it, they might think it's not there.
        // Let's show it with a message if empty.
        alertContainer.style.display = 'block';
        insiderFeed.innerHTML = '<div class="no-data">No active insider alerts</div>';
    }

    // Render Normal Feed
    if (normal.length === 0) {
        normalFeed.innerHTML = '<div class="loading-state">Waiting for trades...</div>';
    } else {
        normalFeed.innerHTML = renderItems(normal);
    }
}

function renderItems(items) {
    return items.map(trade => {
        const isInsider = trade.flag && trade.flag.includes('INSIDER');
        const date = new Date(parseFloat(trade.timestamp) * 1000);
        const timeStr = date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        const historyVal = trade.user_trade_count !== undefined ? trade.user_trade_count : '-';

        return `
            <div class="trade-item ${isInsider ? 'insider' : ''}">
                <div class="col-time">${timeStr}</div>
                <div class="col-prob">${(parseFloat(trade.price) * 100).toFixed(0)}%</div>
                <div class="col-market">
                    ${trade.market}
                    <span class="outcome-badge">${trade.outcome}</span>
                </div>
                <div class="col-value">$${parseFloat(trade.value).toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                <div class="col-history">${historyVal}</div>
                <div class="col-user" title="${trade.user}">${trade.user}</div>
            </div>
        `;
    }).join('');
}

// Removed shortenAddress function as it is no longer used

// Poll every 2 seconds
setInterval(fetchTrades, 2000);
fetchTrades();
