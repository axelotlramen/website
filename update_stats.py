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
        "ltuid_v2": os.environ["HOYOLAB_LTUID"],
        "ltoken_v2": os.environ["HOYOLAB_LTOKEN"],
    }

    client = genshin.Client(cookies)

    hsr_uid = int(os.environ["HOYOLAB_HSR_UID"])

    # Fetch full Star Rail profile
    user = await client.get_starrail_user(hsr_uid)

    # Fetch characters
    character_response = await client.get_starrail_characters(hsr_uid)
    characters = character_response.avatar_list

    # Filter 5-star characters
    five_stars = [
        char.name for char in characters if char.rarity == 5
    ]

    data = {
        "last_updated": datetime.utcnow().isoformat(),
        "genshin": {},
        "hsr": {
            "nickname": user.info.nickname,
            "server": user.info.server,
            "level": user.info.level,
            "avatar": user.info.avatar,
            "achievements": user.stats.achievement_num,
            "active_days": user.stats.active_days,
            "avatar_count": user.stats.avatar_num,
            "chest_count": user.stats.chest_num,
            "five_star_characters": five_stars,
        },
    }

    os.makedirs("data", exist_ok=True)

    with open("data/stats.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
