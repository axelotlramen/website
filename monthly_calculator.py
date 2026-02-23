import asyncio
import genshin
import csv
import os
from datetime import datetime

CSV_FILE = "data/hsr_diary_log.csv"
PULL_COST = 160
FIVE_STAR_PITY = 80
THREE_WEEKS = 21

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

async def main():
    client = genshin.Client()
    await client.login_with_password(os.environ["HOYOLAB_USER_EMAIL"], os.environ["HOYOLAB_USER_PASSWORD"])

    uid = int(os.environ["HOYOLAB_HSR_UID"])
    hsr_diary = await client.get_starrail_diary(uid=uid)
    day_data = hsr_diary.day_data

    today = datetime.now().strftime("%Y-%m-%d")

    jades_gain = day_data.current_hcoin
    pulls_gain = day_data.current_rails_pass

    rows = read_existing_data()

    # Remove today's row if it exists (we will re-add it)
    rows = [r for r in rows if r["Date"] != today]

    # Get previous totals
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

    # ---- 3 Week Rolling Average ----
    rows_for_avg = rows[-(THREE_WEEKS-1):] # last 20 days
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

    if avg_gain and avg_gain > 0:
        estimated_days = currency_needed / avg_gain
    else:
        estimated_days = None

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

    print("Updated CSV successfully.")
    print(new_row)

if __name__ == "__main__":
    asyncio.run(main())