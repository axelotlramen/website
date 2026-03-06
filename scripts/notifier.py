import calendar
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import requests

GREEN_EMBED = 5763719
RED_EMBED = 15548997

class WebhookClient:
    def __init__(self, hoyolab_webhook: str, endfield_webhook: str, discord_id: str | None = None):
        self.hoyolab_webhook = hoyolab_webhook
        self.endfield_webhook = endfield_webhook
        self.discord_id = discord_id

    def send_hoyolab(self, elapsed: float, embeds):
        payload = {
            "username": "Hoyolab Stats Bot",
            "content": f"✅ Task completed in `{elapsed:.2f}s`",
            "embeds": embeds
        }

        response = requests.post(self.hoyolab_webhook, json=payload, timeout=10)
        response.raise_for_status()

    def send_endfield(self, elapsed: float, embeds):
        payload = {
            "username": "Chen Qianyu - Dijiang Control Nexus Assistant",
            "content": f"✅ Task completed in `{elapsed:.2f}s`",
            "embeds": embeds
        }

        response = requests.post(self.endfield_webhook, json=payload, timeout=10)
        response.raise_for_status()

    def send_failure(self, task_name: str, error_message: str):
        now_est = datetime.now(ZoneInfo("America/New_York"))

        embed = {
            "title": "Task Failure",
            "description": f"❌ **{task_name} Failed**\n\n```{error_message}```",
            "color": RED_EMBED,
            "footer": {
                "text": f"Time: {now_est.strftime('%m/%d/%Y, %I:%M:%S %p')} (ET)"
            }
        }

        payload = {
            "content": f"<@{self.discord_id}> Stats update failed!\n{error_message or ''}",
            "embeds": [embed]
        }

        response = requests.post(self.hoyolab_webhook, json=payload, timeout=10)
        response.raise_for_status()

def hoyolab_embed(old_data: dict | None, genshin_data: dict, hsr_data: dict):
    embed_color = GREEN_EMBED

    if old_data:
        old_genshin = old_data.get("genshin_data", {})
        old_hsr = old_data.get("hsr_data", {})
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

    return embed

def hoyolab_diary_embed(hsr_diary: dict | None, genshin_diary: dict | None):
    embed_color = GREEN_EMBED

    now_est = datetime.now(ZoneInfo("America/New_York"))

    fields = []

    if genshin_diary:
        fields.append({
            "name": "Genshin Impact",
            "value": (
                f"**Net Currency Gain:** {genshin_diary.get('Net Currency Gain', '0')}\n"
                f"**Pulls Net Gain:** {genshin_diary.get('Pulls Net Gain', '0')}\n"
                f"**Total Pulls:** {genshin_diary.get('Total Pulls', '0')}\n"
            ),
            "inline": True
        })

    if hsr_diary:
        fields.append({
            "name": "Honkai: Star Rail",
            "value": (
                f"**Net Currency Gain:** {hsr_diary.get('Net Currency Gain', '0')}\n"
                f"**Pulls Net Gain:** {hsr_diary.get('Pulls Net Gain', '0')}\n"
                f"**Total Pulls:** {hsr_diary.get('Total Pulls', '0')}\n"
            ),
            "inline": True
        })

    embed = {
        "title": "Daily Pull Progress Update",
        "description": "📈 **Diary Updated Successfully**",
        "color": embed_color,
        "fields": fields,
        "footer": {
            "text": f"Time: {now_est.strftime('%m/%d/%Y, %I:%M:%S %p')} (ET)",
            "icon_url": "https://www.hoyolab.com/favicon.ico"
        }
    }

    return embed

def endfield_attendance_embed(results: Dict[str, Any]):
    embed_color = GREEN_EMBED

    now_est = datetime.now(ZoneInfo("America/New_York"))

    rewards_text = ", ".join(f"{r['name']} x {r['count']}" for r in results.get("rewards", []))
    rewards_icon_url = results.get("rewards", [])[0].get("icon", "") if results.get("rewards", []) else ""

    currentSignIns = int(results.get("attendance", {}).get("totalSignIns", 0))
    total_days = calendar.monthrange(datetime.now(ZoneInfo("America/New_York")).year, datetime.now(ZoneInfo("America/New_York")).month)[1]

    next_rewards_text = f"{results.get('nextAward', {}).get('name')} x{results.get('nextAward', {}).get('count')}"

    embed = {
        "title": ":date: Daily Sign-In",
        "color": embed_color,
        "fields": [
            {
                "name": "Status",
                "value": results.get("status") or "-",
            },
            {
                "name": "Claimed Rewards" if results.get("status") == "Already Claimed" else "Rewards",
                "value": rewards_text
            },
            {
                "name": "Progress",
                "value": f"{currentSignIns}/{total_days}"
            },
            {
                "name": "Next Rewards",
                "value": next_rewards_text
            }
        ],
        "footer": {
            "text": f"Time: {now_est.strftime('%m/%d/%Y, %I:%M:%S %p')} (ET)",
            "icon_url": "https://assets.skport.com/assets/favicon.ico"
        }
    }

    if rewards_icon_url:
        embed["thumbnail"] = {
            "url": rewards_icon_url
        }
    
    return embed

def endfield_embed(old_data: dict | None, endfield_data: dict):
    embed_color = GREEN_EMBED

    if old_data:
        old_endfield = old_data.get("endfield_data", {})
    else:
        old_endfield = {}

    fields = [
        {
            "name": "Arknights: Endfield",
            "value": (
                f"**Level:** {endfield_data.get('level', 'N/A')}\n"
                f"**Achievements:** {calculate_delta(old_endfield.get('achievements', 0), endfield_data.get('achievements', '0'))}\n"
                f"**Character Count:** {calculate_delta(old_endfield.get('avatar_count', '0'), endfield_data.get('avatar_count', '0'))}\n"
                f"**Stamina:** {calculate_delta(old_endfield.get('stamina', '0'), endfield_data.get('stamina', '0'))}\n"
                f"**Daily Mission:** {calculate_delta(old_endfield.get('daily_mission', '0'), endfield_data.get('daily_mission', '0'))}\n"
            )
        }
    ]

    now_est = datetime.now(ZoneInfo("America/New_York"))

    embed = {
        "title": "Arknights: Endfield Stats Updated",
        "description": "✅ **Site updated successfully!**",
        "color": embed_color,
        "fields": fields,
        "footer": {
            "text": f"Time: {now_est.strftime('%m/%d/%Y, %I:%M:%S %p')} (ET)",
            "icon_url": "https://assets.skport.com/assets/favicon.ico"
        }
    }

    return embed

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