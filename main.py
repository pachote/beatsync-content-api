"""
BeatSync Content API — Machine 2
AI-powered content generation for music creators.
33x markup on Anthropic API costs. Runs 24/7 automated.

Endpoints:
  POST /generate/caption      — social media caption from audio metadata
  POST /generate/yt-description — YouTube description + tags for beat/song
  POST /generate/video-script  — video script for music video
  POST /generate/email-blast   — email marketing copy for beat sales

Pricing (Stripe metered):
  /generate/* → $0.08 per call (costs us ~$0.003 in Claude API)

Deploy: Railway (1-click), or any ASGI host
List on: RapidAPI Marketplace → instant dev traffic
"""

import os, json, time, hashlib, hmac, smtplib, requests as _requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import stripe

# ── Config ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
RAPIDAPI_PROXY_SECRET = os.environ.get("RAPIDAPI_PROXY_SECRET", "")  # from RapidAPI dashboard
GMAIL_USER = os.environ.get("GMAIL_USER", "beatsyncpro.official@gmail.com")
GMAIL_PASS = os.environ.get("GMAIL_PASS", "xlgkuiejvmktmznt")
PORT = int(os.environ.get("PORT", 8000))

R2_BASE = "https://pub-7e0619ec319a46fba7be7399e50c93a1.r2.dev/"
PRICE_PRODUCTS = {
    "price_1TZv8zIWH9q4fDUwFt9l1pNQ": {"name": "150 AI Music Video Director Prompts",   "file": "150-ai-music-video-prompts.txt"},
    "price_1TZv90IWH9q4fDUwGVsS8dY1": {"name": "Wan2GP + Kling AI Master Prompt Bundle", "file": "wan2gp-kling-master-bundle.txt"},
    "price_1TZv91IWH9q4fDUwwGdyjOrK": {"name": "Cold Email AI Writing System",           "file": "cold-email-ai-writing-system.txt"},
}

stripe.api_key = STRIPE_SECRET_KEY
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

app = FastAPI(
    title="BeatSync Content API",
    description="AI content generation for music creators. Social captions, YouTube SEO, video scripts.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ────────────────────────────────────────────────────────────────────

class CaptionRequest(BaseModel):
    genre: str                         # "trap", "lo-fi", "phonk", "drill", "edm"
    bpm: Optional[int] = None
    mood: Optional[str] = None         # "dark", "chill", "hype", "emotional"
    artist_name: Optional[str] = None
    platforms: list[str] = ["instagram", "tiktok", "twitter"]
    count: int = 3                     # number of variations

class YouTubeDescRequest(BaseModel):
    song_title: str
    genre: str
    bpm: Optional[int] = None
    mood: Optional[str] = None
    artist_name: Optional[str] = None
    free_pack_url: str = "https://beatsyncpro.ai"
    include_tags: bool = True

class VideoScriptRequest(BaseModel):
    genre: str
    bpm: Optional[int] = None
    mood: Optional[str] = None
    duration_seconds: int = 180        # default 3-minute video
    style: str = "music_video"         # "music_video", "type_beat", "lyric_video"

class EmailBlastRequest(BaseModel):
    beat_title: str
    genre: str
    price: float
    bpm: Optional[int] = None
    target_audience: str = "music producers"
    call_to_action_url: str = "https://beatsyncpro.ai"

class MeterUsageRequest(BaseModel):
    customer_id: str
    quantity: int = 1

# ── Auth ──────────────────────────────────────────────────────────────────────

async def verify_rapidapi(x_rapidapi_proxy_secret: str = Header(None)):
    """RapidAPI sends a proxy secret on every request. Validate it."""
    if RAPIDAPI_PROXY_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_PROXY_SECRET:
        raise HTTPException(status_code=403, detail="Invalid RapidAPI proxy secret")
    return True

async def get_stripe_customer(x_api_key: str = Header(None)):
    """Validate Stripe API key header and return subscription item ID for metering."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    # In production: look up customer by API key from your database
    # For MVP: validate format and return placeholder
    if not x_api_key.startswith("bsapi_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    return x_api_key

# ── Core generator ─────────────────────────────────────────────────────────────

def _generate(system: str, user: str, max_tokens: int = 600) -> str:
    msg = claude.messages.create(
        model="claude-haiku-4-5-20251001",  # cheapest + fast
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text.strip()

def _meter_stripe(subscription_item_id: str, quantity: int = 1):
    """Record usage for Stripe metered billing."""
    try:
        stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=quantity,
            timestamp=int(time.time()),
            action="increment",
        )
    except Exception:
        pass  # Don't fail requests on billing errors — log separately

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "BeatSync Content API",
        "version": "1.0.0",
        "endpoints": ["/generate/caption", "/generate/yt-description",
                      "/generate/video-script", "/generate/email-blast"],
        "pricing": "$0.08/call via RapidAPI or direct subscription",
        "docs": "/docs",
        "website": "https://beatsyncpro.ai",
    }

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": int(time.time())}

@app.post("/generate/caption")
async def generate_caption(req: CaptionRequest, _auth=Depends(verify_rapidapi)):
    """Generate social media captions for a music track."""
    platform_str = ", ".join(req.platforms)
    mood_str = f" with a {req.mood} mood" if req.mood else ""
    bpm_str = f" at {req.bpm} BPM" if req.bpm else ""
    artist_str = f" by {req.artist_name}" if req.artist_name else ""

    system = (
        "You are a music marketing expert who writes viral social media captions for music producers. "
        "Write punchy, platform-appropriate captions that drive streams and follows. "
        "Never use generic phrases like 'check this out'. Be specific to the genre and vibe. "
        "Always include relevant hashtags at the end."
    )
    user = (
        f"Write {req.count} social media caption variations for a {req.genre} track"
        f"{bpm_str}{mood_str}{artist_str}. "
        f"Platforms: {platform_str}. "
        f"Format: numbered list. Each caption complete with hashtags."
    )

    result = _generate(system, user)
    return {
        "captions": result,
        "genre": req.genre,
        "platforms": req.platforms,
        "generated_at": int(time.time()),
        "powered_by": "BeatSync Content API | beatsyncpro.ai",
    }

@app.post("/generate/yt-description")
async def generate_yt_description(req: YouTubeDescRequest, _auth=Depends(verify_rapidapi)):
    """Generate SEO-optimized YouTube description + tags for a beat/song."""
    bpm_str = f" | {req.bpm} BPM" if req.bpm else ""
    mood_str = f" | {req.mood}" if req.mood else ""

    system = (
        "You are a YouTube SEO expert specializing in music and beats. "
        "Write descriptions that rank for high-volume music production keywords. "
        "Include a structured description with timestamps placeholder, social links section, "
        "and a keyword-rich tags list."
    )
    user = (
        f"Write a YouTube description for: '{req.song_title}' — {req.genre} beat{bpm_str}{mood_str}.\n"
        f"Artist: {req.artist_name or 'Independent Producer'}\n"
        f"Free pack URL: {req.free_pack_url}\n\n"
        f"Include:\n"
        f"1. Opening hook (2 lines, keyword-rich)\n"
        f"2. Description body (what the beat sounds like, use cases)\n"
        f"3. Free pack CTA: get free clips at {req.free_pack_url}\n"
        f"4. Social links section (placeholder)\n"
        f"5. Hashtags (15-20 relevant tags)\n"
        f"{'6. Tags list (comma-separated, 500 chars max)' if req.include_tags else ''}"
    )

    result = _generate(system, user, max_tokens=800)
    return {
        "description": result,
        "song_title": req.song_title,
        "genre": req.genre,
        "generated_at": int(time.time()),
        "powered_by": "BeatSync Content API | beatsyncpro.ai",
    }

@app.post("/generate/video-script")
async def generate_video_script(req: VideoScriptRequest, _auth=Depends(verify_rapidapi)):
    """Generate a video script/shot list for a music video."""
    bpm_str = f" at {req.bpm} BPM" if req.bpm else ""
    mood_str = f" {req.mood} mood" if req.mood else ""

    system = (
        "You are a music video director with experience creating viral YouTube content for independent producers. "
        "Write detailed, actionable shot lists and scripts that can be executed with a clip library (no actors needed). "
        "Format: scene by scene with timestamps, visual descriptions, and clip type suggestions."
    )
    user = (
        f"Write a {req.style} script for a {req.genre} track{bpm_str} with a{mood_str} vibe. "
        f"Duration: {req.duration_seconds} seconds ({req.duration_seconds // 60}m{req.duration_seconds % 60}s). "
        f"Format as: Scene 1 [0:00-0:15]: [visual description] | [clip type from library] | [transition]. "
        f"Include intro, verse, chorus, bridge, outro structure. "
        f"Reference stock footage styles that are available royalty-free."
    )

    result = _generate(system, user, max_tokens=1000)
    return {
        "script": result,
        "genre": req.genre,
        "duration_seconds": req.duration_seconds,
        "style": req.style,
        "generated_at": int(time.time()),
        "powered_by": "BeatSync Content API | beatsyncpro.ai",
    }

@app.post("/generate/email-blast")
async def generate_email_blast(req: EmailBlastRequest, _auth=Depends(verify_rapidapi)):
    """Generate email marketing copy for beat/music sales."""
    bpm_str = f" ({req.bpm} BPM)" if req.bpm else ""

    system = (
        "You are a music industry email copywriter who specializes in converting producers "
        "and artists into paying customers. Write emails that feel personal, not spammy. "
        "Focus on the emotional value: what this beat will help the artist CREATE."
    )
    user = (
        f"Write a marketing email for: '{req.beat_title}' — {req.genre} beat{bpm_str}. "
        f"Price: ${req.price}. Target: {req.target_audience}. "
        f"CTA URL: {req.call_to_action_url}\n\n"
        f"Include: Subject line (3 variations), email body (150-200 words), "
        f"P.S. line, and a clear CTA button text."
    )

    result = _generate(system, user, max_tokens=600)
    return {
        "email_copy": result,
        "beat_title": req.beat_title,
        "genre": req.genre,
        "price": req.price,
        "generated_at": int(time.time()),
        "powered_by": "BeatSync Content API | beatsyncpro.ai",
    }

# ── Stripe Webhook ─────────────────────────────────────────────────────────────

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email", "")
        session_id = session.get("id", "")
        if customer_email and session_id:
            try:
                items = stripe.checkout.Session.list_line_items(session_id)
                for item in items.get("data", []):
                    price_id = item.get("price", {}).get("id", "")
                    if price_id in PRICE_PRODUCTS:
                        prod = PRICE_PRODUCTS[price_id]
                        _send_download_email(customer_email, prod["name"], R2_BASE + prod["file"])
            except Exception as e:
                print(f"Delivery error: {e}")
    elif event["type"] == "customer.subscription.created":
        pass
    elif event["type"] == "invoice.payment_failed":
        pass

    return {"status": "ok"}


def _send_download_email(to_email: str, product_name: str, download_url: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your download is ready: {product_name}"
    msg["From"] = f"BeatSync PRO <{GMAIL_USER}>"
    msg["To"] = to_email
    body = (
        f"Hi there,\n\nThank you for purchasing {product_name}!\n\n"
        f"Download your file here:\n{download_url}\n\n"
        f"This is a direct link. Save it somewhere safe.\n\n"
        f"Questions? Reply to this email.\n\n-- BeatSync PRO\nhttps://beatsyncpro.ai"
    )
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(GMAIL_USER, GMAIL_PASS)
            s.send_message(msg)
        print(f"Delivery email sent: {to_email} / {product_name}")
    except Exception as e:
        print(f"Email send error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
