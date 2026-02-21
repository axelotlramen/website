"""
Endfield Daily Check-In Script

This script was adapted from:
https://gist.github.com/cptmacp/1e9a9f20f69c113a0828fea8d13cb34c

Original author: cpt-macp
Modifications by: axelotlramen (helped by ChatGPT)
Date adapted: 2026-02-20

Changes made:
- Converted from JavaScript to Python
- Refactored into modular class structure
- Added structured logging

This script is for personal automation use only.
"""

import time
import json
import hmac
import hashlib
import requests
from dataclasses import dataclass
from typing import List, Dict, Any
import logging
import sys
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


ATTENDANCE_URL = "https://zonai.skport.com/web/v1/game/endfield/attendance"
REFRESH_URL = "https://zonai.skport.com/web/v1/auth/refresh"

def setup_logging(debug: bool = True):
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("endfield.log", mode="a")
        ]
    )


# ---------------------------
# CONFIG STRUCTURES
# ---------------------------

@dataclass
class Profile:
    cred: str
    sk_game_role: str
    platform: str
    v_name: str
    account_name: str


@dataclass
class DiscordConfig:
    enabled: bool
    webhook: str
    discord_id: str | None = None


# ---------------------------
# END FIELD CLIENT
# ---------------------------

class EndfieldClient:

    def __init__(self, profile: Profile):
        self.profile = profile
        self.logger = logging.getLogger(f"Client[{profile.account_name}]")

    def _timestamp(self) -> str:
        ts = str(int(time.time()))
        self.logger.debug(f"Generated timestamp: {ts}")
        return ts

    def _generate_sign(self, path: str, body: str, timestamp: str, token: str) -> str:
        header_json = (
            f'{{"platform":"{self.profile.platform}",'
            f'"timestamp":"{timestamp}",'
            f'"dId":"",'
            f'"vName":"{self.profile.v_name}"}}'
        )

        raw_string = path + body + timestamp + header_json

        hmac_digest = hmac.new(
            (token or "").encode(),
            raw_string.encode(),
            hashlib.sha256
        ).hexdigest()

        md5_digest = hashlib.md5(hmac_digest.encode()).hexdigest()
        return md5_digest

    def refresh_token(self) -> str:
        self.logger.info("Refreshing token...")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "cred": self.profile.cred,
            "platform": self.profile.platform,
            "vName": self.profile.v_name,
            "Origin": "https://game.skport.com",
            "Referer": "https://game.skport.com/"
        }

        try:
            response = requests.get(REFRESH_URL, headers=headers)
            data = response.json()
            self.logger.debug(f"Refresh response: {data}")

            if data.get("code") == 0:
                token = data["data"]["token"]
                self.logger.info("Token refreshed successfully.")
                return token
            else:
                raise Exception(f"Refresh failed: {data}")
        
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}", exc_info=True)
            raise

    def claim_attendance(self) -> Dict[str, Any]:
        self.logger.info("Starting attendance claim...")

        timestamp = self._timestamp()

        try:
            token = self.refresh_token()
        except Exception as e:
            return {
                "name": self.profile.account_name,
                "success": False,
                "status": "Token Refresh Failed",
                "rewards": str(e)
            }

        sign = self._generate_sign(
            "/web/v1/game/endfield/attendance",
            "",
            timestamp,
            token
        )

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Referer": "https://game.skport.com/",
            "Content-Type": "application/json",
            "sk-language": "en",
            "sk-game-role": self.profile.sk_game_role,
            "cred": self.profile.cred,
            "platform": self.profile.platform,
            "vName": self.profile.v_name,
            "timestamp": timestamp,
            "sign": sign,
            "Origin": "https://game.skport.com",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }

        try:
            self.logger.debug("Sending attendance POST request...")
            response = requests.post(ATTENDANCE_URL, headers=headers)
            data = response.json()
            self.logger.debug(f"Attendance response: {data}")
        
        except Exception as e:
            self.logger.error(f"Attendance request failed: {e}", exc_info=True)
            return {
                "name": self.profile.account_name,
                "success": False,
                "status": "Request Failed",
                "rewards": str(e)
            }

        result = {
            "name": self.profile.account_name,
            "success": False,
            "status": "",
            "rewards": ""
        }

        code = data.get("code")

        if code == 0:
            self.logger.info("Check-in successful.")
            result["success"] = True
            result["status"] = "Check-in Successful"

            rewards = []
            for award in data.get("data", {}).get("awardIds", []):
                reward_id = award.get("id")
                resource = data["data"].get("resourceInfoMap", {}).get(reward_id)
                if resource:
                    rewards.append(f"{resource['name']} x{resource['count']}")
                else:
                    rewards.append(reward_id)

            result["rewards"] = "\n".join(rewards) or "No reward info"

        elif data.get("code") == 10001:
            self.logger.info("Already checked in.")
            result["success"] = True
            result["status"] = "Already Checked In"
            result["rewards"] = "Nothing to claim"

        else:
            self.logger.warning(f"Unexpected response code: {code}")
            result["status"] = f"Error (Code: {data.get('code')})"
            result["rewards"] = data.get("message", "Unknown error")

        return result


# ---------------------------
# DISCORD NOTIFIER
# ---------------------------

class DiscordNotifier:
    def __init__(self, config: DiscordConfig):
        self.config = config
        self.logger = logging.getLogger("DiscordNotifier")

    def send(self, results: List[Dict[str, Any]]):

        if not self.config.enabled:
            self.logger.info("Discord notifications disabled.")
            return
        
        self.logger.info("Sending webhook notification...")

        all_success = all(r["success"] for r in results)
        embed_color = 5763719 if all_success else 15548997

        fields = [
            {
                "name": f"👤 {r['name']}",
                "value": f"**Status:** {r['status']}\n**Rewards:**\n{r['rewards']}",
                "inline": True
            }
            for r in results
        ]

        now_est = datetime.now(ZoneInfo("America/New_York"))

        payload = {
            "username": "Endfield Assistant",
            "embeds": [{
                "title": "Endfield Daily Check-in Report",
                "color": embed_color,
                "fields": fields,
                "footer": {
                    "text": f"Time: {now_est.strftime('%m/%d/%Y, %I:%M:%S %p')} (ET)",
                    "icon_url": "https://assets.skport.com/assets/favicon.ico"
                }
            }]
        }

        if not all_success and self.config.discord_id:
            payload["content"] = f"<@{self.config.discord_id}> Error occurred!"

        try:
            requests.post(self.config.webhook, json=payload)
            self.logger.info("Webhook sent successfully.")
        except Exception as e:
            self.logger.error(f"Failed to send webhook: {e}", exc_info=True)


# ---------------------------
# MAIN ENTRY
# ---------------------------

if __name__ == "__main__":
    setup_logging(debug=True)

    logging.info("Starting Endfield Check-in Script")

    profiles = [
        Profile(
            cred=os.environ["ENDFIELD_CRED"],
            sk_game_role=os.environ["ENDFIELD_GAME_ROLE"],
            platform="3",
            v_name="1.0.0",
            account_name="axelotlramen"
        )
    ]

    discord_config = DiscordConfig(
        enabled=True,
        webhook=os.environ["ENDFIELD_WEBHOOK"],
        discord_id=os.environ["DISCORD_ID"]
    )

    results = []

    for profile in profiles:
        client = EndfieldClient(profile)
        result = client.claim_attendance()
        results.append(result)

    notifier = DiscordNotifier(discord_config)
    notifier.send(results)

    # Fail workflow if any account failed
    all_success = all(r["success"] for r in results)

    if not all_success:
        logging.error("One or more check-ins failed. Exiting with error code.")
        sys.exit(1)

    logging.info("All check-ins successful.")
    logging.info("Script finished.")