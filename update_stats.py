# update_stats.py
import genshin
import asyncio
import json
import os
from datetime import datetime
import requests

def download_google_sheet():
    sheet_url = os.environ["GOOGLE_SHEET_CSV_URL"]
    output_path = "data/sheet.csv"

    os.makedirs("data", exist_ok=True)

    try:
        print("Downloading Google Sheet CSV...")
        r = requests.get(sheet_url, timeout=15)
        print("Status:", r.status_code)

        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            print("Saved to", output_path)
        else:
            print("Failed to download sheet")

    except Exception as e:
        print("Error downloading sheet:", e)


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

    hsr_notes = await client.get_starrail_notes(uid=hsr_uid)

    data = {
        "last_updated": datetime.utcnow().isoformat(),
        "genshin": {},
        "hsr": {
            "nickname": user.info.nickname,
            "server": user.info.server,
            "level": user.info.level,
            "avatar": "data/avatar.png",
            "achievements": user.stats.achievement_num,
            "active_days": user.stats.active_days,
            "avatar_count": user.stats.avatar_num,
            "chest_count": user.stats.chest_num,
            "five_star_characters": five_stars,

            "stamina": hsr_notes.current_stamina,
            "current_train_score": hsr_notes.current_train_score,
        },
    }

    os.makedirs("data", exist_ok=True)

    avatar_url = user.info.avatar
    avatar_path = "data/avatar.png"

    try:
        print("Downloading avatar...")
        r = requests.get(avatar_url, timeout=10)
        print("HTTP Status Code:", r.status_code)
        if r.status_code == 200:
            with open(avatar_path, "wb") as f:
                f.write(r.content)
        else:
            print("Failed to download avatar, status code:", r.status_code)
            avatar_path = ""
    except Exception as e:
        print("Failed to download avatar:", e)
        avatar_path = ""

    with open("data/stats.json", "w") as f:
        json.dump(data, f, indent=2)

    download_google_sheet()


if __name__ == "__main__":
    asyncio.run(main())
