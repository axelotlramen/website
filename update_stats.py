# update_stats.py
import genshin # type: ignore
import asyncio
import json
import os
from datetime import datetime, timezone
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
    
def calculate_delta(old_value, new_value):
    try:
        old_value = int(old_value)
        new_value = int(new_value)
        diff = new_value - old_value

        if diff > 0:
            return f"{new_value} (⬆️ +{diff})"
        elif diff < 0:
            return f"{new_value} ({diff})"
        else:
            return f"{new_value}"
    except Exception:
        return str(new_value)

class StatsDiscordNotifier:
    def __init__(self, webhook: str, discord_id: str | None = None):
        self.webhook = webhook
        self.discord_id = discord_id
        
    def send(self, old_data: dict | None, genshin_data: dict, hsr_data: dict, success: bool, error_message: str | None = None):
        embed_color = 5763719 if success else 15548997

        if old_data:
            old_genshin = old_data.get("genshin", {})
            old_hsr = old_data.get("hsr", {})
        else:
            old_genshin = {}
            old_hsr = {}

        fields = [
            {
                "name": "Genshin Impact",
                "value": (
                    f"**AR:** {genshin_data.get('level', 'N/A')}\n"
                    f"**Achievements:** {calculate_delta(old_genshin.get('achievements', '0'), genshin_data.get('achievements', '0'))}\n"
                    f"**Active Days:** {calculate_delta(old_genshin.get('active_days', '0'), genshin_data.get('active_days', '0'))}\n"
                    f"**Character Count:** {calculate_delta(old_genshin.get('avatar_count', '0'), genshin_data.get('avatar_count', '0'))}\n"
                    f"**Oculus:** {calculate_delta(old_genshin.get('oculus', '0'), genshin_data.get('oculus', '0'))}\n"
                    f"**Chest Count:** {calculate_delta(old_genshin.get('chest_count', '0'), genshin_data.get('chest_count', '0'))}\n"
                    f"**Resin:** {calculate_delta(old_genshin.get('resin', '0'), genshin_data.get('resin', '0'))}\n"
                    f"**Daily Tasks:** {calculate_delta(old_genshin.get('daily_task', '0'), genshin_data.get('daily_task', '0'))}\n"
                ),
                "inline": True
            },
            {
                "name": "Honkai: Star Rail",
                "value": (
                    f"**Trailblaze Level:** {hsr_data.get('level', 'N/A')}\n"
                    f"**Achievements:** {calculate_delta(old_hsr.get('achievements', '0'), hsr_data.get('achievements', '0'))}\n"
                    f"**Active Days:** {calculate_delta(old_hsr.get('active_days', '0'), hsr_data.get('active_days', '0'))}\n"
                    f"**Character Count:** {calculate_delta(old_hsr.get('avatar_count', '0'), hsr_data.get('avatar_count', '0'))}\n"
                    f"**Chest Count:** {calculate_delta(old_hsr.get('chest_count', '0'), hsr_data.get('chest_count', '0'))}\n"
                    f"**Trailblaze Power:** {calculate_delta(old_hsr.get('stamina', '0'), hsr_data.get('stamina', '0'))}\n"
                    f"**Daily Training:** {calculate_delta(old_hsr.get('current_train_score', '0'), hsr_data.get('current_train_score', '0'))}\n"
                ),
                "inline": True
            }
        ]

        embed = {
            "title": "Hoyolab Stats Updated",
            "description": "✅ **Site updated successfully!**",
            "color": embed_color,
            "fields": fields,
            "footer": {
                "text": f"Time: {datetime.now(timezone.utc).strftime('%m/%d/%Y, %I:%M:%S %p')} (UTC)",
                "icon_url": "https://www.hoyolab.com/favicon.ico"
            }
        }

        payload = {
            "username": "Hoyolab Stats Bot",
            "embeds": [embed]
        }

        if not success and self.discord_id:
            payload["content"] = f"<@{self.discord_id}> Stats update failed!\n{error_message or ''}"

        try:
            response = requests.post(self.webhook, json=payload)
            response.raise_for_status()
        except Exception as e:
            raise

async def main():
    notifier = StatsDiscordNotifier(
        webhook=os.environ["HOYOLAB_WEBHOOK"],
        discord_id=os.environ["DISCORD_ID"]
    )

    try:
        # ---------------------------
        # Setup + Client
        # ---------------------------
   
        cookies = {
            "ltuid_v2": os.environ["HOYOLAB_LTUID"],
            "ltoken_v2": os.environ["HOYOLAB_LTOKEN"],
        }

        client = genshin.Client(cookies)

        hsr_uid = int(os.environ["HOYOLAB_HSR_UID"])
        genshin_uid = int(os.environ["HOYOLAB_GENSHIN_UID"])

        # ---------------------------
        # Fetch Data
        # ---------------------------
        hsr_data = await fetch_hsr_data(client, hsr_uid)
        genshin_data = await fetch_genshin_data(client, genshin_uid)

        data = {
            "last_updated": datetime.utcnow().isoformat(),
            "genshin": genshin_data,
            "hsr": hsr_data,
        }

        os.makedirs("data", exist_ok=True)

        # ---------------------------
        # Avatar Download (Non-Fatal)
        # ---------------------------
        try:
            print("Downloading avatars...")

            hsr_avatar_url = hsr_data.get("avatar_url", "")
            genshin_avatar_url = genshin_data.get("avatar_url", "")

            if hsr_avatar_url:
                r = requests.get(hsr_avatar_url, timeout=10)
                r.raise_for_status()
                with open("data/hsr_avatar.png", "wb") as f:
                    f.write(r.content)

            if genshin_avatar_url:
                r = requests.get(genshin_avatar_url, timeout=10)
                r.raise_for_status()
                with open("data/genshin_avatar.png", "wb") as f:
                    f.write(r.content)

        except Exception as avatar_error:
            print(f"Avatar download failed: {avatar_error}")

        # ---------------------------
        # Save JSON
        # ---------------------------
        old_data = None

        if os.path.exists("data/stats.json"):
            try:
                with open("data/stats.json", "r") as f:
                    old_data = json.load(f)
            except Exception:
                old_data = None

        with open("data/stats.json", "w") as f:
            json.dump(data, f, indent=2)

        download_google_sheet()

        # ---------------------------
        # SUCCESS NOTIFICATION
        # ---------------------------
        notifier.send(
            old_data=old_data,
            genshin_data=genshin_data,
            hsr_data=hsr_data,
            success=True
        )

    except Exception as e:
        # ---------------------------
        # FAILURE NOTIFICATION
        # ---------------------------
        notifier.send(
            old_data={},
            genshin_data={},
            hsr_data={},
            success=False,
            error_message=str(e)
        )

        raise


if __name__ == "__main__":
    asyncio.run(main())
