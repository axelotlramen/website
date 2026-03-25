import logging


async def fetch_hsr_data(client, uid):
    logger = logging.getLogger("fetch_hsr_data")

    try:
        user = await client.get_starrail_user(uid)

        # Fetch characters
        character_response = await client.get_starrail_characters(uid)
        characters = character_response.avatar_list

        # Filter 5-star characters
        five_stars = {
            char.name: {
                "icon": char.icon,
                "eidolon": char.rank,
                "element": char.element,
                "path": char.path,
                "level": char.level,
                "lc": {
                    "name": char.equip.name,
                    "icon": char.equip.icon,
                    "rarity": char.equip.rarity,
                    "level": char.equip.level,
                    "superimposition": char.equip.rank
                } if char.equip else None
            } for char in characters if char.rarity == 5
        }

        hsr_notes = await client.get_starrail_notes(uid=uid)
        moc_data = await fetch_memory_of_chaos(client, uid)
        apoc_data = await fetch_apocalyptic_shadow(client, uid)
        pf_data = await fetch_pure_fiction(client, uid)
        aa_data = await fetch_anomaly_arbitration(client, uid)

        return {
            "nickname": user.info.nickname,
            "level": user.info.level,
            "avatar_url": user.info.avatar,
            "achievements": user.stats.achievement_num,
            "active_days": user.stats.active_days,
            "avatar_count": user.stats.avatar_num,
            "chest_count": user.stats.chest_num,
            "five_star_characters": five_stars,

            "stamina": hsr_notes.current_stamina,
            "current_train_score": hsr_notes.current_train_score,

            "anomaly_arbitration": aa_data,
            "apocalyptic_shadow": apoc_data,
            "pure_fiction": pf_data,
            "memory_of_chaos": moc_data,
        }
    
    except Exception:
        logger.error("Failed to fetch HSR data", exc_info=True)
        return {}
    
async def fetch_anomaly_arbitration(client, uid):
    logger = logging.getLogger("fetch_anomaly_arbitration")
    try:
        challenge = await client.get_anomaly_arbitration(uid=uid)
        if not challenge or not challenge.records:
            return {}
        
        record = challenge.records[0]
        if not record.has_data:
            return {}
        
        boss_record = None
        if record.boss_record and record.boss_record.has_data:
            boss_record = {
                "characters": [
                    {"id": a.id,
                     "level": a.level,
                     "eidolon": a.rank}
                     for a in record.boss_record.characters
                ],
                "cycles_used": record.boss_record.cycles_used,
                "stars": record.boss_record.stars,
                "medal_type": record.boss_record.medal_type,
            }

        mini_boss_records = [
            {
                "characters": [
                    {"id": a.id, "level": a.level, "eidolon": a.rank}
                    for a in mb.characters
                ],
                "cycles_used": mb.cycles_used,
                "stars": mb.stars,
            }
            for mb in record.mini_boss_records
            if mb.has_data
        ]

        return {
            "season": record.season.name if record.season else None,
            "boss_stars": record.boss_stars,
            "mini_boss_stars": record.mini_boss_stars,
            "cycles_used": record.cycles_used,
            "boss_record": boss_record,
            "mini_boss_records": mini_boss_records,
        }
    
    except Exception:
        logger.error("Failed to fetch Anomaly Arbitration", exc_info=True)
        return {}
    
async def fetch_apocalyptic_shadow(client, uid):
    logger = logging.getLogger("fetch_apocalyptic_shadow")
    try:
        challenge = await client.get_starrail_apc_shadow(uid=uid)
        if not challenge or not challenge.has_data or not challenge.floors:
            return {}
        
        floor_4 = challenge.floors[0]

        floor_data = {
            "floor": floor_4.name,
            "score": floor_4.score,
            "first_half": [],
            "second_half": [],
        }

        for avatar in floor_4.node_1.avatars:
            floor_data["first_half"].append({
                "id": avatar.id,
                "level": avatar.level,
                "eidolon": avatar.rank, 
            })

        for avatar in floor_4.node_2.avatars:
            floor_data["second_half"].append({
                "id": avatar.id,
                "level": avatar.level,
                "eidolon": avatar.rank, 
            })

        return {
            "total_stars": challenge.total_stars,
            "floor_data": floor_data
        }
    
    except Exception:
        logger.error("Failed to fetch Apocalyptic Shadow", exc_info=True)
        return {}
    
async def fetch_pure_fiction(client, uid):
    logger = logging.getLogger("fetch_pure_fiction")
    try:
        challenge = await client.get_starrail_pure_fiction(uid=uid)
        if not challenge or not challenge.has_data or not challenge.floors:
            return {}
        
        floor_4 = challenge.floors[0]
        
        floor_data = {
            "floor": floor_4.name,
            "score": floor_4.score,
            "first_half": [],
            "second_half": [],
        }

        for avatar in floor_4.node_1.avatars:
            floor_data["first_half"].append({
                "id": avatar.id,
                "level": avatar.level,
                "eidolon": avatar.rank, 
            })

        for avatar in floor_4.node_2.avatars:
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
    
    except Exception:
        logger.error("Failed to fetch Memory of Chaos", exc_info=True)
        return {}

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
    
    except Exception:
        logger.error("Failed to fetch Memory of Chaos", exc_info=True)
        return {}
    
async def fetch_genshin_data(client, uid):
    logger = logging.getLogger("fetch_genshin_data")
    try:
        user = await client.get_genshin_user(uid)
        characters = await client.get_genshin_characters(uid)

        five_stars = {
            char.name: {
                "icon": char.icon,
                "constellation": char.constellation,
                "element": char.element,
                "weaponType": char.weapon_type,
                "level": char.level,
                "friendship": char.friendship,
                "weapon": {
                    "name": char.weapon.name,
                    "icon": char.weapon.icon,
                    "rarity": char.weapon.rarity,
                    "level": char.weapon.level,
                    "refinement": char.weapon.refinement
                } if char.weapon else None
            } for char in characters if char.rarity == 5
        }

        notes = await client.get_genshin_notes(uid)

        oculus = user.stats.anemoculi + user.stats.geoculi + user.stats.electroculi + user.stats.dendroculi + user.stats.hydroculi + user.stats.pyroculi + user.stats.lunoculi

        chests = user.stats.common_chests + user.stats.exquisite_chests + user.stats.precious_chests + user.stats.luxurious_chests + user.stats.remarkable_chests

        return {
            "nickname": user.info.nickname,
            "level": user.info.level,
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
    
    except Exception:
        logger.error("Failed to fetch Genshin data", exc_info=True)
        return {}