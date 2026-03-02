import asyncio
from datetime import datetime
import json
import logging
import os
import time
from zoneinfo import ZoneInfo

import genshin

from scripts.endfield.client import EndfieldClient
from scripts.hoyolab.diary import GENSHIN_CONFIG, HSR_CONFIG, update_diary_csv
from scripts.hoyolab.stats import fetch_genshin_data, fetch_hsr_data
from scripts.logging_config import setup_logging
from scripts.notifier import WebhookClient, endfield_attendance_payload, endfield_payload, hoyolab_diary_payload, hoyolab_payload


async def main():
    start_time = time.perf_counter()
    logger = logging.getLogger("main")

    notifier = WebhookClient(
        webhook=os.environ["HOYOLAB_WEBHOOK"],
        discord_id=os.environ["DISCORD_ID"]
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
        endfield_data = endfield_client.fetch_endfield_data()

        data = {
            "last_updated": datetime.now(ZoneInfo("America/New_York")).isoformat(),
            "hsr_data": hsr_data,
            "genshin_data": genshin_data,
            "hsr_diary": hsr_diary,
            "genshin_diary": genshin_diary,
            "endfield_attendance": endfield_attendance,
            "endfield_data": endfield_data
        }

        os.makedirs("data", exist_ok=True)

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

        notifier.send_duration(elapsed)
        notifier.send(
            payload=hoyolab_payload(
                old_data=old_data,
                genshin_data=genshin_data,
                hsr_data=hsr_data
            )
        )
        notifier.send(
            payload=hoyolab_diary_payload(
                hsr_diary=hsr_diary,
                genshin_diary=genshin_diary
            )
        )

        notifier.send_duration(elapsed, webhook=os.environ["ENDFIELD_WEBHOOK"])
        notifier.send(
            payload=endfield_attendance_payload(endfield_attendance),
            webhook=os.environ["ENDFIELD_WEBHOOK"]
        )
        notifier.send(
            payload=endfield_payload(
                old_data=old_data,
                endfield_data=endfield_data
            ),
            webhook=os.environ["ENDFIELD_WEBHOOK"]
        )

    except Exception as e:
        # ---------------------------
        # FAILURE NOTIFICATION
        # ---------------------------

        notifier.send_failure(
            task_name="main",
            error_message=str(e)
        )
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
