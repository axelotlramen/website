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

async def fetch_memory_of_chaos(client, uid):
    try:
        challenge = await client.get_starrail_challenge(uid=uid)

        if not challenge:
            return {}
        
        floor_12 = challenge.floors[0]

        floor_data = {
            "floor": floor_12.name,
            "cycles": floor_12.round_num,
            "first_half": [],
            "second_half": [],
        }

        for avatar in floor_12.node_1.avatars:
            floor_data["first_half"].append({
                "id": avatar.id,
                "level": avatar.level,
                "eidolon": avatar.rank, 
            })

        for avatar in floor_12.node_2.avatars:
            floor_data["second_half"].append({
                "id": avatar.id,
                "level": avatar.level,
                "eidolon": avatar.rank, 
            })

        return {
            "season": challenge.name,
            "total_stars": challenge.total_stars,
            "floor_data": floor_data
        }
    
    except Exception as e:
        print("Failed to fetch Memory of Chaos:", e)
        return {}
    
async def fetch_hsr_data(client, uid):
    try:
        user = await client.get_starrail_user(uid)

        # Fetch characters
        character_response = await client.get_starrail_characters(uid)
        characters = character_response.avatar_list

        # Filter 5-star characters
        five_stars = [
            char.name for char in characters if char.rarity == 5
        ]

        hsr_notes = await client.get_starrail_notes(uid=uid)
        moc_data = await fetch_memory_of_chaos(client, uid)

        return {
            "nickname": user.info.nickname,
            "level": user.info.level,
            "avatar": "data/hsr_avatar.png",
            "avatar_url": user.info.avatar,
            "achievements": user.stats.achievement_num,
            "active_days": user.stats.active_days,
            "avatar_count": user.stats.avatar_num,
            "chest_count": user.stats.chest_num,
            "five_star_characters": five_stars,

            "stamina": hsr_notes.current_stamina,
            "current_train_score": hsr_notes.current_train_score,

            "memory_of_chaos": moc_data,
        }
    except Exception as e:
        print("Failed to fetch HSR data:", e)
        return {}
    
async def fetch_genshin_data(client, uid):
    try:
        user = await client.get_genshin_user(uid)
        characters = await client.get_genshin_characters(uid)

        five_stars = [
            char.name for char in characters if char.rarity == 5
        ]

        notes = await client.get_genshin_notes(uid)

        oculus = user.stats.anemoculi + user.stats.geoculi + user.stats.electroculi + user.stats.dendroculi + user.stats.hydroculi + user.stats.pyroculi + user.stats.lunoculi

        chests = user.stats.common_chests + user.stats.exquisite_chests + user.stats.precious_chests + user.stats.luxurious_chests + user.stats.remarkable_chests

        return {
            "nickname": user.info.nickname,
            "level": user.info.level,
            "avatar": "data/genshin_avatar.png",
            "avatar_url": user.info.in_game_avatar,
            "achievements": user.stats.achievements,
            "active_days": user.stats.days_active,
            "avatar_count": user.stats.characters,
            "oculus": oculus,
            "chest_count": chests,
            "five_star_characters": five_stars,

            "resin": notes.current_resin,
            "daily_task": notes.daily_task.completed_tasks
        }
    
    except Exception as e:
        print("Failed to fetch Genshin data:", e)
        return {}


async def main():
    # Grab your cookie from Hoyolab (ltuid, ltoken, cookie_token, account_id, etc.)
    # Store it in GitHub secrets instead of hardcoding!
    cookies = {
        "ltuid_v2": os.environ["HOYOLAB_LTUID"],
        "ltoken_v2": os.environ["HOYOLAB_LTOKEN"],
    }

    client = genshin.Client(cookies)

    hsr_uid = int(os.environ["HOYOLAB_HSR_UID"])
    genshin_uid = int(os.environ["HOYOLAB_GENSHIN_UID"])

    # fetch both games
    hsr_data = await fetch_hsr_data(client, hsr_uid)
    genshin_data = await fetch_genshin_data(client, genshin_uid)

    data = {
        "last_updated": datetime.utcnow().isoformat(),
        "genshin": genshin_data,
        "hsr": hsr_data,
    }

    os.makedirs("data", exist_ok=True)

    hsr_avatar_url = hsr_data.get("avatar_url", "")
    hsr_avatar_path = "data/hsr_avatar.png"
    genshin_avatar_url = genshin_data.get("avatar_url", "")
    genshin_avatar_path = "data/genshin_avatar.png"

    try:
        print("Downloading avatar...")
        hsr_r = requests.get(hsr_avatar_url, timeout=10)
        genshin_r = requests.get(genshin_avatar_url, timeout=10)
        print("HTTP Status Code:", hsr_r.status_code)
        print("HTTP Status Code:", genshin_r.status_code)
        if hsr_r.status_code == 200:
            with open(hsr_avatar_path, "wb") as f:
                f.write(hsr_r.content)
        else:
            print("Failed to download avatar, status code:", hsr_r.status_code)
            hsr_avatar_path = ""

        if genshin_r.status_code == 200:
            with open(genshin_avatar_path, "wb") as f:
                f.write(genshin_r.content)
        else:
            print("Failed to download avatar, status code:", genshin_r.status_code)
            genshin_avatar_path = ""
        
    except Exception as e:
        print("Failed to download avatar:", e)
        hsr_avatar_path = ""

    with open("data/stats.json", "w") as f:
        json.dump(data, f, indent=2)

    download_google_sheet()


if __name__ == "__main__":
    asyncio.run(main())
