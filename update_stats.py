# update_stats.py
import genshin
import asyncio
import json
import os
from datetime import datetime


async def main():
    # Grab your cookie from Hoyolab (ltuid, ltoken, cookie_token, account_id, etc.)
    # Store it in GitHub secrets instead of hardcoding!
    cookies = {
        "ltuid": os.environ["HOYOLAB_LTUID"],
        "ltoken": os.environ["HOYOLAB_LTOKEN"],
        "cookie_token": os.environ["HOYOLAB_COOKIE_TOKEN"],
        "account_id": os.environ["HOYOLAB_ACCOUNT_ID"],
    }

    client = genshin.Client(cookies)

    # Example: Fetch Genshin daily notes
    notes = await client.get_notes(uid=123456789)  # replace with your UID
    # Example: Fetch Honkai: Star Rail daily notes
    hsr_notes = await client.get_starrail_notes(uid=987654321)  # replace with UID

    data = {
        "last_updated": datetime.utcnow().isoformat(),
        "genshin": {
            "resin": notes.current_resin,
            "commissions_done": notes.completed_commissions,
            "commissions_total": notes.total_commissions,
        },
        "hsr": {
            "stamina": hsr_notes.current_stamina,
            "expeditions": len(hsr_notes.expeditions),
        },
    }

    with open("data/stats.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
