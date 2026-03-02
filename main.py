import asyncio
from datetime import datetime
import json
import logging
import os
import time

import genshin

from scripts.endfield.client import EndfieldClient
from scripts.hoyolab.diary import GENSHIN_CONFIG, HSR_CONFIG, update_diary_csv
from scripts.hoyolab.stats import fetch_genshin_data, fetch_hsr_data
from scripts.logging_config import setup_logging
from scripts.notifier import WebhookClient


async def main():
    start_time = time.perf_counter()
    logger = logging.getLogger("main")

    notifier = WebhookClient(
        webhook=os.environ["HOYOLAB_WEBHOOK"],
    )

    try:
        # ---------------------------
        # Setup + Client
        # ---------------------------

        hoyolab_client = genshin.Client()
        hoyolab_client.set_cookies(os.environ["HOYOLAB_USER_COOKIES"])

        hsr_uid = int(os.environ["HOYOLAB_HSR_UID"])
        genshin_uid = int(os.environ["HOYOLAB_GENSHIN_UID"])

        endfield_client = EndfieldClient(
            cred=os.environ["ENDFIELD_CRED"],
            sk_game_role=os.environ["ENDFIELD_GAME_ROLE"]
        )

        # ---------------------------
        # Fetch Data
        # ---------------------------
        hsr_data = await fetch_hsr_data(hoyolab_client, hsr_uid)
        genshin_data = await fetch_genshin_data(hoyolab_client, genshin_uid)
        hsr_diary = await update_diary_csv(hoyolab_client, hsr_uid, HSR_CONFIG)
        genshin_diary = await update_diary_csv(hoyolab_client, genshin_uid, GENSHIN_CONFIG)

        endfield_attendance = endfield_client.claim_attendance()

        data = {
            "last_updated": datetime.utcnow().isoformat(),
            "hsr_data": hsr_data,
            "genshin_data": genshin_data,
            "hsr_diary": hsr_diary,
            "genshin_diary": genshin_diary,
            "endfield_attendance": endfield_attendance
        }

        os.makedirs("data", exist_ok=True)

        # ---------------------------
        # Save JSON
        # ---------------------------
        with open("data/new_stats.json", "w") as f:
            json.dump(data, f, indent=2)

        # ---------------------------
        # SUCCESS NOTIFICATION
        # ---------------------------
        elapsed = time.perf_counter() - start_time
        logger.info(f"Stats update completed in {elapsed:.2f}s")


    except Exception as e:
        raise

if __name__ == "__main__":
    setup_logging(debug=True)
    logging.info("Starting Stats Update Script")

    try:
        asyncio.run(main())
        logging.info("Script finished successfully.")
    except Exception:
        logging.exception("Script crashed.")
        raise
