# BeatSync Content API — RapidAPI Listing

## Category
Music + Developer Tools > AI Text Generation

## Short Description (100 chars)
AI content for music creators: captions, YouTube SEO, video scripts, email copy. $0.08/call.

## Long Description

**Turn any beat into a complete content package — captions, YouTube description, video script, and email blast — in one API call.**

BeatSync Content API uses Claude AI to generate platform-optimized content for music producers, beat makers, and independent artists. Stop spending hours writing the same captions and descriptions. Automate it.

### What You Get

| Endpoint | Output | Price/Call |
|----------|--------|-----------|
| `POST /generate/caption` | 3 social captions (Instagram/TikTok/Twitter) with hashtags | $0.08 |
| `POST /generate/yt-description` | Full YouTube description + 500-char tag string | $0.08 |
| `POST /generate/video-script` | Scene-by-scene music video shot list (180s default) | $0.08 |
| `POST /generate/email-blast` | Subject lines + email body + CTA for beat sales | $0.08 |

### Why Producers Use This
- **33x faster** than writing by hand
- **SEO-optimized** for music keywords (BPM, genre, mood)
- **Platform-aware** — TikTok caption ≠ Twitter caption ≠ email subject
- **Royalty-free integration** — includes BeatSync PRO free pack mentions (optional)

### Example Input (caption)
```json
{
  "genre": "trap",
  "bpm": 140,
  "mood": "dark",
  "platforms": ["instagram", "tiktok"],
  "count": 3
}
```

### Example Output
```
1. 🔥 Dark trap energy hits different at 140 BPM. This one's for the street. 
   #trapbeats #darkbeats #typebeatforsale #beatmaker #musicproducer

2. When the 808 hits you in the chest 💀 
   Free trap clips: beatsyncpro.ai 
   #trap #newbeats #freestylebeats #rap

3. Trap producers, this one's yours. Slide in if you want exclusives.
   #beatsforsale #trapproducer #hiphopbeats
```

---

## Pricing Plans

| Plan | Calls/Month | Price |
|------|------------|-------|
| Basic | 100 | $7/mo |
| Pro | 1,000 | $50/mo |
| Ultra | 10,000 | $350/mo |
| Pay Per Use | Unlimited | $0.08/call |

---

## Authentication
Send `X-RapidAPI-Key` header (auto-included by RapidAPI).

---

## Base URL
`https://beatsync-content-api.up.railway.app`

---

## Submit To
https://rapidapi.com/provider/api-admin — category: AI Text Generation + Music
