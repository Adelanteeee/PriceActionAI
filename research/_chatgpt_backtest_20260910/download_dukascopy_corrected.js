const fs = require('fs');
const path = require('path');
const { getHistoricalRates } = require('dukascopy-node');

const OUT = path.resolve(process.argv[2] || 'market_data');
fs.mkdirSync(OUT, { recursive: true });

function csv(rows) {
  const head = 'timestamp,open,high,low,close,volume\n';
  return head + rows.map(r => [r.timestamp, r.open, r.high, r.low, r.close, r.volume ?? ''].join(',')).join('\n') + '\n';
}

async function fetchSide(side) {
  const data = await getHistoricalRates({
    instrument: 'xauusd',
    dates: { from: new Date('2024-12-01T00:00:00Z'), to: new Date('2026-01-01T00:00:00Z') },
    timeframe: 'm1',
    priceType: side,
    format: 'json',
    utcOffset: 0,
    volumes: true,
    ignoreFlats: true,
    batchSize: 20,
    pauseBetweenBatchesMs: 250,
    retries: 3,
    pauseBetweenRetriesMs: 1000
  });
  if (!Array.isArray(data) || data.length < 100000) throw new Error(`${side}: unexpectedly small dataset ${data?.length}`);
  for (const r of data) {
    if (!(r.timestamp && Number.isFinite(r.open) && Number.isFinite(r.high) && Number.isFinite(r.low) && Number.isFinite(r.close))) {
      throw new Error(`${side}: invalid row`);
    }
    if (r.volume !== undefined && !(r.volume > 0)) throw new Error(`${side}: zero-volume flat leaked at ${r.timestamp}`);
  }
  const file = path.join(OUT, `xauusd_${side}_m1.csv`);
  fs.writeFileSync(file, csv(data));
  console.log(side, 'rows', data.length, 'first', new Date(data[0].timestamp).toISOString(), 'last', new Date(data[data.length-1].timestamp).toISOString());
}

(async () => {
  await fetchSide('bid');
  await fetchSide('ask');
})().catch(err => { console.error(err); process.exit(1); });
