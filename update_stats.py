# update_stats.py
from locale import currency
from turtle import update

import genshin # type: ignore
import asyncio
import csv
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
import time
import logging
import sys
from dataclasses import dataclass
from typing import Optional

def setup_logging(debug: bool = True):
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("hoyolab.log", mode="a")
        ]
    )

async def fetch_memory_of_chaos(client, uid):
    logger = logging.getLogger("fetch_memory_of_chaos")
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
        logger.error("Failed to fetch Memory of Chaos", exc_info=True)
        return {}
    
async def fetch_hsr_data(client, uid):
    logger = logging.getLogger("fetch_hsr_data")
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
        logger.error("Failed to fetch HSR data", exc_info=True)
        return {}
    
async def fetch_genshin_data(client, uid):
    logger = logging.getLogger("fetch_genshin_data")
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
        logger.error("Failed to fetch Genshin data", exc_info=True)
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
@dataclass
class GameConfig:
    name: str
    csv_file: str
    currency_name: str
    pull_item_name: str
    pull_cost: int
    five_star_pity: int
    diary_fetcher: callable
    currency_attr: str
    pull_attr: Optional[str] = None

HSR_CONFIG = GameConfig(
    name="HSR",
    csv_file="data/hsr_diary_log.csv",
    currency_name="Stellar Jades",
    pull_item_name="Passes",
    pull_cost=160,
    five_star_pity=80,
    diary_fetcher=lambda client, uid: client.get_starrail_diary(uid=uid),
    currency_attr="current_hcoin",
    pull_attr="current_rails_pass"
)

GENSHIN_CONFIG = GameConfig(
    name="Genshin",
    csv_file="data/genshin_diary_log.csv",
    currency_name="Primogems",
    pull_item_name="Fates",
    pull_cost=160,
    five_star_pity=80,
    diary_fetcher=lambda client, uid: client.get_genshin_diary(uid=uid),
    currency_attr="current_primogems",
    pull_attr=""
)

def read_existing_data(csv_file):
    if not os.path.exists(csv_file):
        return []
    
    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)
    
def write_data(csv_file, rows, fieldnames):
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

async def update_diary_csv(client, uid, config: GameConfig):
    logger = logging.getLogger(f"update_{config.name.lower()}_diary")
    os.makedirs("data", exist_ok=True)

    diary = await config.diary_fetcher(client, uid)
    day_data = diary.day_data

    today = datetime.now().strftime("%Y-%m-%d")

    currency_gain = getattr(day_data, config.currency_attr)
    
    if config.pull_attr:
        pulls_gain = getattr(day_data, config.pull_attr)
    else:
        pulls_gain = 0

    rows = read_existing_data(config.csv_file)
    rows = [r for r in rows if r["Date"] != today]

    if rows:
        last_row = rows[-1]
        prev_currency = int(last_row[config.currency_name])
        prev_pulls = float(last_row["Pulls"])
    else:
        prev_currency = 0
        prev_pulls = 0

    new_currency_total = prev_currency + currency_gain
    new_pulls_total = prev_pulls + pulls_gain

    total_pulls = new_currency_total / config.pull_cost + new_pulls_total
    currency_needed = max(config.five_star_pity - total_pulls, 0) * config.pull_cost

    THREE_WEEKS = 21
    rows_for_avg = rows[-(THREE_WEEKS - 1):]
    gains = [
        int(r["Net Currency Gain"]) + int(r["Pulls Net Gain"]) * config.pull_cost for r in rows_for_avg
    ]

    today_total_gain = currency_gain + pulls_gain * config.pull_cost
    gains.append(today_total_gain)

    avg_gain = (
        sum(gains[-THREE_WEEKS:]) / THREE_WEEKS if len(gains) >= THREE_WEEKS else None
    )

    estimated_days = (
        currency_needed / avg_gain
        if avg_gain and avg_gain > 0
        else None
    )

    fieldnames = [
        "Date",
        "Net Currency Gain",
        "Pulls Net Gain",
        config.currency_name,
        "Pulls",
        "Total Pulls",
        "Currency Needed for 5 Star",
        "3 Week Avg Gain",
        "Estimated Days Til 5 Star"
    ]

    new_row = {
        "Date": today,
        "Jades Net Gain": currency_gain,
        "Pulls Net Gain": pulls_gain,
        config.currency_name: new_currency_total,
        "Pulls": new_pulls_total,
        "Total Pulls": round(total_pulls, 2),
        "Currency Needed for 5 Star": round(currency_needed, 2),
        "3-Week Avg Gain": round(avg_gain, 2) if avg_gain else "",
        "Estimated Days Til 5 Star": round(estimated_days, 2) if estimated_days else ""
    }

    rows.append(new_row)
    write_data(config.csv_file, rows, fieldnames)

    logger.info(f"{config.name} diary updated successfully.")
    return new_row

async def main():
    start_time = time.perf_counter()
    logger = logging.getLogger("main")
    notifier = StatsDiscordNotifier(
        webhook=os.environ["HOYOLAB_WEBHOOK"],
        discord_id=os.environ["DISCORD_ID"]
    )

    try:
        # ---------------------------
        # Setup + Client
        # ---------------------------

        client = genshin.Client()
        client.set_cookies(os.environ["HOYOLAB_USER_COOKIES"])

        hsr_uid = int(os.environ["HOYOLAB_HSR_UID"])
        genshin_uid = int(os.environ["HOYOLAB_GENSHIN_UID"])

        # ---------------------------
        # Fetch Data
        # ---------------------------
        hsr_data = await fetch_hsr_data(client, hsr_uid)
        genshin_data = await fetch_genshin_data(client, genshin_uid)
        await update_diary_csv(client, hsr_uid, HSR_CONFIG)
        await update_diary_csv(client, genshin_uid, GENSHIN_CONFIG)

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
        elapsed = time.perf_counter() - start_time
        logger.info(f"Stats update completed in {elapsed:.2f}s")

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
    setup_logging(debug=True)
    logging.info("Starting Hoyolab Stats Update Script")

    try:
        asyncio.run(main())
        logging.info("Script finished successfuly.")
    except Exception:
        logging.exception("Script crashed.")
        raise
