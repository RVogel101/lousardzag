# Nayiri Dictionary Scraping Guide

**Status**: Updated March 4, 2026  
**Contact**: Serouj (serouj@nayiri.com)

## Quick Start

To scrape the Nayiri dictionary responsibly:

```bash
python -m wa_corpus.nayiri_scraper \
  --delay-min 3.0 \
  --delay-max 6.0 \
  --cooldown-every 50 \
  --cooldown-seconds 30
```

## Why You Got Banned (and How to Avoid It)

The previous implementation used **search-based scraping with 2-letter prefixes**, which:
- ❌ Generated thousands of "word not found" errors
- ❌ Created excessive server load with non-existent query patterns
- ❌ Looked suspicious (automated searches for non-words)
- ❌ Violated rate-limiting expectations

## Current Approach: Page-Based Browsing

The updated scraper uses **sequential page browsing** (`imagepage.php`), which:
- ✅ Follows the site's natural pagination structure
- ✅ Reduces server load and suspicion
- ✅ Respects the intended user navigation pattern
- ✅ Allows graceful resumption if interrupted

## IP Whitelisting (CRITICAL)

You **must be whitelisted** to scrape Nayiri. This prevents over-aggressive banning:

1. **Get your IP address** (especially if using VPN):
   - Browser: https://whatismyipaddress.com
   - PowerShell: `(Invoke-WebRequest -Uri 'https://api.ipify.org').Content`
   - Windows: `ipconfig /all` for local IP

2. **Email Serouj**:
   ```
   To: serouj@nayiri.com
   Subject: IP Whitelist Request for Research Scraper
   
   Dear Serouj,
   
   I'm building a Western Armenian language learning system and would like 
   to scrape dictionary entries from Nayiri. I have implemented respectful 
   rate-limiting and will follow these practices:
   
   - Delays: 3-6 seconds between requests
   - Cooldown: 30 seconds every 50 requests
   - User-Agent: Identifies my application and includes contact info
   - Browsing: Page-based navigation only, no excessive search queries
   
   My IP address(es) to whitelist: [YOUR_IP]
   
   Thank you,
   [Your Name]
   ```

3. **Wait for confirmation** before running the scraper

## Rate-Limiting Best Practices

### Time Delays
- **Minimum**: 3 seconds between requests (previously 2.5)
- **Maximum**: 6 seconds between requests (previously 4.5)
- **Variation**: Random within range to look natural
- **Why**: Humans typically take 2-10 seconds per page

### Cooldown Periods
- **Every**: 50 requests (previously 60)
- **Duration**: 30 seconds (previously 20)
- **Why**: Simulates user breaks while browsing

### User-Agent
```
ArmenianLearningCorpus/2.0 (+https://github.com/ar-lousardzag; respect rate-limiting)
```
- Identifies your bot professionally
- Shows you're respectful
- Includes contact/reference info

### Retry Strategy
- **Max retries**: 3 attempts per page
- **Backoff**: Exponential (2^attempt) before retry
- **Never hammer**: Give up and move on, don't retry endlessly

## Recovery from Ban

If you get blocked again:

1. **Note the time** when the ban occurred
2. **Wait 24-48 hours** before retrying
3. **If on VPN**: Switch VPN server or use different IP
4. **Email Serouj** explaining the situation
5. **Request re-whitelisting** if your IP changed

## VPN / IP Change Best Practices

- Treat your VPN exit IP as your identity for Nayiri access.
- Before each scrape session, verify your current public IP.
- If the IP changed from your previously approved IP, do not run full scraping until re-confirmed.
- Prefer stable VPN server locations for repeat scraping sessions.
- Keep a small local record of:
  - last whitelisted IP
  - date confirmed with Serouj
  - last successful scrape run

### Public IP lookup fallback order

1. Browser check (recommended): `https://whatismyipaddress.com`
2. Terminal check: `(Invoke-WebRequest -Uri 'https://api.ipify.org').Content`
3. If terminal lookup fails (DNS/network policy), use browser result and continue whitelist workflow.

## Monitoring & Resumption

The scraper saves checkpoints in `wa_corpus/data/nayiri/`:
- `dictionary.jsonl` — All scraped entries (append-only)
- `dictionary_full.json` — Complete consolidated dictionary

### Resume an interrupted scrape:
```bash
python -m wa_corpus.nayiri_scraper \
  --start-page 147 \
  --max-pages 500
```

## Compliance Checklist

Before running:
- [ ] I have my IP address
- [ ] I have emailed Serouj with my IP and use case
- [ ] I have received confirmation that my IP is whitelisted
- [ ] I understand the delays are 3-6 seconds (not faster)
- [ ] I will monitor the logs for errors or blocks
- [ ] I will respect any requests from Nayiri to adjust rate-limiting

## Troubleshooting

### "Got 'word not found' errors"
- **Cause**: Old search-based approach with invalid 2-letter prefixes
- **Solution**: Use the updated page-based scraper

### "Connection blocked/timeout"
- **Cause**: IP not whitelisted or rate-limit too aggressive
- **Solution**: Verify whitelisting with Serouj; increase delays

### "Same entries repeatedly"
- **Cause**: Duplicate checkpoint data from previous runs
- **Solution**: Clear `wa_corpus/data/nayiri/*.jsonl` if needed before fresh scrape

## References

- Nayiri dictionary: http://nayiri.com
- Dictionary admin: serouj@nayiri.com
- Scraper implementation: `02-src/wa_corpus/nayiri_scraper.py`
- Configuration constants:
  - `REQUEST_DELAY_MIN = 3.0`
  - `REQUEST_DELAY_MAX = 6.0`
  - `COOLDOWN_EVERY = 50`
  - `COOLDOWN_SECONDS = 30.0`

## Key Changes (March 2026)

| Aspect | Old | New |
|--------|-----|-----|
| **Method** | Search + 2-letter prefixes | Page-based browsing (`imagepage.php`) |
| **Min delay** | 2.5s | 3.0s |
| **Max delay** | 4.5s | 6.0s |
| **Cooldown** | Every 60 requests | Every 50 requests |
| **Cooldown length** | 20s | 30s |
| **User-Agent** | Generic bot | Professional + contact info |
| **IP handling** | Not required | **Whitelisting required** |

