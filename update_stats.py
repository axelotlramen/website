# update_stats.py
import genshin # type: ignore
import asyncio
import csv
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
import time

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
            return f"{new_value} (+{diff})"
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

        now_est = datetime.now(ZoneInfo("America/New_York"))

        embed = {
            "title": "Hoyolab Stats Updated",
            "description": "✅ **Site updated successfully!**",
            "color": embed_color,
            "fields": fields,
            "footer": {
                "text": f"Time: {now_est.strftime('%m/%d/%Y, %I:%M:%S %p')} (ET)",
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

# reading trailblaze monthly calculator
PULL_COST = 160
FIVE_STAR_PITY = 80
THREE_WEEKS = 21
CSV_FILE = "data/hsr_diary_log.csv"

def read_existing_data():
    if not os.path.exists(CSV_FILE):
        return []
    
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
    
def write_data(rows):
    fieldnames = [
        "Date",
        "Jades Net Gain",
        "Pulls Net Gain",
        "Stellar Jades",
        "Pulls",
        "Total Pulls",
        "Currency Needed for 5 Star",
        "3-Week Avg Gain",
        "Estimated Days Til 5 Star"
    ]

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

async def update_hsr_diary_csv(client, hsr_uid):
    os.makedirs("data", exist_ok=True)

    hsr_diary = await client.get_starrail_diary(uid=hsr_uid)
    day_data = hsr_diary.day_data

    today = datetime.now().strftime("%Y-%m-%d")

    jades_gain = day_data.current_hcoin
    pulls_gain = day_data.current_rails_pass

    rows = read_existing_data()

    rows = [r for r in rows if r["Date"] != today]

    if rows:
        last_row = rows[-1]
        prev_jades = int(last_row["Stellar Jades"])
        prev_pulls = float(last_row["Pulls"])
    else:
        prev_jades = 0
        prev_pulls = 0

    new_jades_total = prev_jades + jades_gain
    new_pulls_total = prev_pulls + pulls_gain

    total_pulls = new_jades_total / PULL_COST + new_pulls_total
    currency_needed = max(FIVE_STAR_PITY - total_pulls, 0) * PULL_COST

    rows_for_avg = rows[-(THREE_WEEKS - 1):]
    gains = []

    for r in rows_for_avg:
        total_gain = int(r["Jades Net Gain"]) + int(r["Pulls Net Gain"]) * PULL_COST
        gains.append(total_gain)

    today_total_gain = jades_gain + pulls_gain * PULL_COST
    gains.append(today_total_gain)

    if len(gains) >= THREE_WEEKS:
        avg_gain = sum(gains[-THREE_WEEKS:]) / THREE_WEEKS
    else:
        avg_gain = None

    estimated_days = (
        currency_needed / avg_gain
        if avg_gain and avg_gain > 0
        else None
    )

    new_row = {
        "Date": today,
        "Jades Net Gain": jades_gain,
        "Pulls Net Gain": pulls_gain,
        "Stellar Jades": new_jades_total,
        "Pulls": new_pulls_total,
        "Total Pulls": round(total_pulls, 2),
        "Currency Needed for 5 Star": round(currency_needed, 2),
        "3-Week Avg Gain": round(avg_gain, 2) if avg_gain else "",
        "Estimated Days Til 5 Star": round(estimated_days, 2) if estimated_days else ""
    }

    rows.append(new_row)
    write_data(rows)

    print("HSR Diary CSV Updated.")
    return new_row

async def main():
    notifier = StatsDiscordNotifier(
        webhook=os.environ["HOYOLAB_WEBHOOK"],
        discord_id=os.environ["DISCORD_ID"]
    )

    try:
        # ---------------------------
        # Setup + Client
        # ---------------------------

        client = genshin.Client()
        await client.login_with_password(os.environ["HOYOLAB_USER_EMAIL"], os.environ["HOYOLAB_USER_PASSWORD"])

        hsr_uid = int(os.environ["HOYOLAB_HSR_UID"])
        genshin_uid = int(os.environ["HOYOLAB_GENSHIN_UID"])

        # ---------------------------
        # Fetch Data
        # ---------------------------
        hsr_data = await fetch_hsr_data(client, hsr_uid)
        genshin_data = await fetch_genshin_data(client, genshin_uid)
        csv_row = await update_hsr_diary_csv(client, hsr_uid)
        print(csv_row)

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
