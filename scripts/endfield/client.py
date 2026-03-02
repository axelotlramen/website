import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional, Tuple

import requests

ATTENDANCE_URL = "https://zonai.skport.com/web/v1/game/endfield/attendance"
REFRESH_URL = "https://zonai.skport.com/web/v1/auth/refresh"

class EndfieldClient:
    def __init__(self, cred: str, sk_game_role: str):
        self.cred = cred
        self.sk_game_role = sk_game_role
        self.logger = logging.getLogger("EndfieldClient")
        self._token: Optional[str] = None

    # ------------------------
    # Internal helpers
    # ------------------------

    def _timestamp(self) -> str:
        ts = str(int(time.time()))
        self.logger.debug(f"Generated timestamp: {ts}")
        return ts
    
    def _generate_sign(self, path: str, body: str, timestamp: str) -> str:
        if not self._token:
            raise Exception("Missing token")
        
        header_json = (
            f'{{"platform":"3",'
            f'"timestamp":"{timestamp}",'
            f'"dId":"",'
            f'"vName":"1.0.0"}}'
        )

        raw = path + body + timestamp + header_json

        hmac_digest = hmac.new(
            self._token.encode(),
            raw.encode(),
            hashlib.sha256
        ).hexdigest()

        md5_digest = hashlib.md5(hmac_digest.encode()).hexdigest()
        return md5_digest
    
    def _refresh_token(self) -> None:
        self.logger.info("Refreshing token...")

        headers = {
            "cred": self.cred,
            "platform": "3",
            "vName": "1.0.0"
        }

        res = requests.get(REFRESH_URL, headers=headers)

        data = res.json()

        if data.get("code") != 0:
            raise Exception(data.get("message"))

        self._token = data["data"]["token"]

    def _request(self, method: str, path: str, *, body: str = "", extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:

        if not self._token:
            self._refresh_token()

        timestamp = self._timestamp()
        sign = self._generate_sign(path, body, timestamp)

        headers = {
            "cred": self.cred,
            "platform": "3",
            "vName": "1.0.0",
            "timestamp": timestamp,
            "sign": sign,
            "sk-language": "en",
            "sk-game-role": self.sk_game_role,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=1.0",
            "Accept-Encoding": "br;q=1.0, gzip;q=0.9, deflate;q=0.8",
            "Cache-Control": 'no-cache',
            "Content-Type": "application/json",
            "Referer": "https://game.skport.com/",
            "Origin": "https://game.skport.com",
        }

        if extra_headers:
            headers.update(extra_headers)

        response = requests.request(
            method=method,
            url=path,
            headers=headers,
            json=body if body else None
        )

        data = response.json()
        self.logger.debug(f"Response for {path}: {data}")

        return data
    
    # ------------------------
    # Attendance
    # ------------------------
    
    def _check_attendance(self) -> Tuple[Dict[str, Any], bool]:
        data = self._request(
            "GET",
            ATTENDANCE_URL
        )

        if data.get("code") == 0:
            has_today = data.get("data", {}).get("hasToday", False)

            return (
                data,
                not has_today
            )
        
        return (
            data,
            False
        )
    
    def _claim_attendance(self):
        data = self._request(
            "POST",
            ATTENDANCE_URL
        )

        if data.get("code") == 0:
            self.logger.info("Successfully claimed attendance.")

            awards = data.get("data", {}).get("awardIds", [])
            resourceMap = data.get("data", {}).get("resourceInfoMap", {})
            rewards = []

            for award in awards:
                info = resourceMap[award.id]
                if info:
                    self.logger.info(f"- {info['name']} x{info['count']}")
                    rewards.append({
                        "name": info["name"],
                        "count": info["count"],
                        "icon": info["icon"] or ""
                    })
            
            return (True, rewards)
        
        self.logger.error(f"Error: {data.get('message', 'Unknown error')}")
        return (False, [])

        
    def claim_attendance(self) -> Dict[str, Any]:
        self.logger.info("Starting attendance claim...")

        result = {
            "status": "error",
            "rewards": [],
            "totalSignIns": 0,
            "attendance": {
                "totalSignIns": 0,
            },
            "error": None
        }

        attendanceData, canClaim = self._check_attendance()

        if attendanceData.get("code") == 0 and attendanceData.get("data") is not None:
            data = attendanceData.get("data", {})
            calendar = data.get("calendar", [])
            doneRecords = [r for r in calendar if r.get("done")]

            result["attendance"] = {
                "totalSignIns": len(doneRecords),
                "calendar": [{"awardId": c.get("awardId"), "available": c.get("available"), "done": c.get("done")} for c in calendar]
            }

            if (not canClaim):
                lastDone = doneRecords[len(doneRecords) - 1]
                if (lastDone):
                    info = data.get("resourceInfoMap")[lastDone.get("awardId")]
                    if info:
                        result["rewards"] = [{
                            "name": info["name"],
                            "count": info["count"],
                            "icon": info["icon"]
                        }]
                
                firstNotDone = next(
                    (r for r in calendar if not r.get("done")),
                    None
                )

                if firstNotDone:
                    info = data.get("resourceInfoMap")[firstNotDone.get("awardId")]

                    if info:
                        result["nextAward"] = {
                            "name": info["name"],
                            "count": info["count"],
                            "icon": info["icon"]
                        }

        if canClaim:
            success, rewards = self._claim_attendance()

            if success:
                result["status"] = "claimed"
                result["rewards"] = rewards
                if result["attendance"]:
                    if result.get("attendance", {}).get("totalSignIns") is not None:
                        result["attendance"]["totalSignIns"] += 1
                    
                    firstNotDone = next(
                        (r for r in result["attendance"]["calendar"] if not r.get("done")),
                        None
                    )
                    if firstNotDone:
                        firstNotDone["done"] = True
            else:
                result["status"] = "error"
                result["error"] = "Failed to claim attendance"
        
        elif attendanceData.get("code") == 0:
            self.logger.info("Already signed in today. Nothing to claim.")
            result["status"] = "already_claimed"
        
        else:
            self.logger.warning("Could not determine attendance status.")
            result["error"] = "Could not determine attendance status"
        
        return result


