import csv
from dataclasses import dataclass
from datetime import datetime
import logging
import os

THREE_WEEKS = 21

@dataclass
class GameConfig:
    name: str
    csv_file: str
    currency_name: str
    pull_item_name: str
    pull_cost: int
    five_star_pity: int
    diary_fetcher: callable # type: ignore
    currency_attr: str

HSR_CONFIG = GameConfig(
    name="HSR",
    csv_file="data/hsr_diary_log.csv",
    currency_name="Stellar Jades",
    pull_item_name="Passes",
    pull_cost=160,
    five_star_pity=80,
    diary_fetcher=lambda client, uid: client.get_starrail_diary(uid=uid),
    currency_attr="current_hcoin",
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
    new_pulls_total = prev_pulls

    total_pulls = new_currency_total / config.pull_cost + new_pulls_total
    currency_needed = max(config.five_star_pity - total_pulls, 0) * config.pull_cost

    rows_for_avg = rows[-(THREE_WEEKS - 1):]
    gains = [
        int(r["Net Currency Gain"]) + int(r["Pulls Net Gain"]) * config.pull_cost for r in rows_for_avg
    ]

    today_total_gain = currency_gain
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
        "3-Week Avg Gain",
        "Estimated Days Til 5 Star"
    ]

    new_row = {
        "Date": today,
        "Net Currency Gain": currency_gain,
        "Pulls Net Gain": 0,
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