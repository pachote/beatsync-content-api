"""Deploy BeatSync Content API to Railway via CLI."""
import subprocess, sys, os, json

RAILWAY_TOKEN = os.environ.get("RAILWAY_TOKEN", "")
SERVICE_NAME = "beatsync-content-api"
API_DIR = os.path.dirname(os.path.abspath(__file__))

# Required env vars to set on Railway
ENV_VARS = {
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "STRIPE_SECRET_KEY": os.environ.get("STRIPE_SECRET_KEY", ""),
    "STRIPE_WEBHOOK_SECRET": os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
    "RAPIDAPI_PROXY_SECRET": os.environ.get("RAPIDAPI_PROXY_SECRET", ""),
    "PORT": "8000",
}

def run(cmd, cwd=None):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or API_DIR)
    if result.returncode != 0:
        print(f"FAILED (exit {result.returncode})")
        sys.exit(result.returncode)

def main():
    print("=== BeatSync Content API — Railway Deploy ===\n")

    # Check Railway CLI
    result = subprocess.run("railway --version", shell=True, capture_output=True)
    if result.returncode != 0:
        print("Railway CLI not found. Install: npm install -g @railway/cli")
        sys.exit(1)

    print(f"Deploying from: {API_DIR}")

    # Login if token provided
    if RAILWAY_TOKEN:
        run(f"railway login --browserless --token {RAILWAY_TOKEN}")

    # Link or create project
    run(f"railway up --service {SERVICE_NAME} --detach")

    print("\nDone. Check Railway dashboard for deployment status.")
    print(f"API will be at: https://{SERVICE_NAME}.up.railway.app")
    print("\nNext: Set env vars in Railway dashboard:")
    for k, v in ENV_VARS.items():
        if v:
            print(f"  {k} = {v[:10]}...")
        else:
            print(f"  {k} = <MISSING — set in Railway>")

    print("\nNext: Submit to RapidAPI:")
    print("  https://rapidapi.com/provider/api-admin")
    print("  See rapidapi_listing.md for full spec")

if __name__ == "__main__":
    main()
