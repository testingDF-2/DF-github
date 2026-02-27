from flask import Flask, request, jsonify
import json
import os
import uuid
import logging
import sys
from datetime import datetime, timezone

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)


if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(__file__)

data_dir = os.path.join(base_dir, "darkfluidapi_data")

def load_json(filename):
    path = os.path.join(data_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

game_client_config_data    = load_json("GameClientConfig.json")
war_info_data              = load_json("WarInfo.json")
galactic_war_effects_data  = load_json("GalacticWarEffects.json")
news_ticker_data           = load_json("NewsTicker.json")
war_assignment_data        = load_json("WarAssignment.json")
war_status_data            = load_json("WarStatus.json")
operation_data             = load_json("Operation.json")
item_packages_data         = load_json("ItemPackages.json")
progression_packages_data  = load_json("ProgressionPackages.json")
progression_items_data     = load_json("ProgressionItems.json")
level_spec_data            = load_json("LevelSpec.json")
progression_data           = load_json("Progression.json")
progression_inventory_data = load_json("ProgressionInventory.json")
reward_entries_data        = load_json("RewardEntries.json")
season_pass_data           = load_json("SeasonPass.json")
news_feed_data             = load_json("NewsFeed.json")

sessions = {}
account_keys = {}


def extract_session_id(auth_header):
    if not auth_header:
        return None
    parts = auth_header.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "session":
        return parts[1].strip()
    return None


@app.route('/api/Account/Login', methods=['POST'])
def account_login():
    data = request.get_json() or {}
    public_key = data.get("publicKey")

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "publicKey": public_key,
        "accountId": None,
        "lobbyProcessed": False
    }

    if public_key:
        log.info(f"[LOGIN] New session created | session_id={session_id} | public_key={public_key}")
    else:
        log.warning(f"[LOGIN] New session created but request contained no publicKey | session_id={session_id}")

    return jsonify({"sessionId": session_id}), 200

@app.route('/api/lobby', methods=['PUT'])
def put_lobby():
    auth_header = request.headers.get("Authorization", "")
    session_id = extract_session_id(auth_header)

    if not session_id:
        log.warning("[LOBBY] PUT received with no parseable session ID in Authorization header")
        return "", 202

    if session_id not in sessions:
        log.warning(f"[LOBBY] PUT received with unrecognised session_id={session_id}")
        return "", 202

    session = sessions[session_id]

    if session["lobbyProcessed"]:
        return "", 202

    data = request.get_json() or {}
    players = data.get("players", [])
    host = next((p for p in players if p.get("isHost")), None)

    if not host:
        log.warning(f"[LOBBY] No host player found in player list | session_id={session_id}")
        return "", 202

    account_id = host.get("memberAccountId")

    if not account_id or account_id == "0":
        log.warning(f"[LOBBY] Host player found but memberAccountId is missing or zero | session_id={session_id}")
        return "", 202

    session["accountId"] = account_id
    session["lobbyProcessed"] = True

    if session["publicKey"]:
        account_keys[account_id] = session["publicKey"]
        log.info(
            f"[LOBBY] Successfully paired account to public key | "
            f"session_id={session_id} | account_id={account_id} | public_key={session['publicKey']}"
        )
    else:
        log.warning(
            f"[LOBBY] Host account resolved but session has no publicKey to pair with | "
            f"session_id={session_id} | account_id={account_id}"
        )

    return "", 202

@app.route('/api/Account/Keys', methods=['GET'])
def get_account_keys():
    account_id = request.args.get("id")

    if not account_id:
        log.warning("[KEYS] Request received with no id parameter")
        return jsonify({"error": "missing id parameter"}), 400

    key = account_keys.get(account_id)

    if key is None:
        log.info(f"[KEYS] Lookup for unknown account_id={account_id} — returning empty result")
        return jsonify({"accountKeys": []}), 200

    log.info(f"[KEYS] Returning key for account_id={account_id}")
    return jsonify({
        "accountKeys": [
            {
                "platformAccountId": account_id,
                "key": key
            }
        ]
    }), 200


@app.route('/api/Configuration/GameClient', methods=['GET'])
def get_game_configuration():
    return jsonify(game_client_config_data)

@app.route('/api/WarSeason/current/WarId', methods=['GET'])
def war_id():
    return jsonify({"id": 801})

@app.route('/api/WarSeason/801/warinfo', methods=['GET'])
def get_war_info_801():
    return jsonify(war_info_data)

@app.route('/api/WarSeason/801/timeSinceStart', methods=['GET'])
def get_time_since_war_start():
    start_time_str = "2024-01-23 12:05:13"
    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    seconds_since_start = int((current_time - start_time).total_seconds())
    return jsonify({"secondsSinceStart": seconds_since_start})

@app.route('/api/WarSeason/GalacticWarEffects', methods=['GET'])
def get_galactic_war_effects():
    return jsonify(galactic_war_effects_data)

@app.route('/api/WarSeason/NewsTicker', methods=['GET'])
def get_news_ticker():
    return jsonify(news_ticker_data)

@app.route('/api/v2/Assignment/War/801', methods=['GET'])
def get_assignment_war_801():
    return jsonify(war_assignment_data)

@app.route('/api/WarSeason/801/Status', methods=['GET'])
def get_war_status_801():
    return jsonify(war_status_data)

@app.route('/api/NewsFeed/801', methods=['GET'])
def get_news_feed_801():
    return jsonify(news_feed_data)

@app.route('/api/Operation', methods=['GET'])
def get_operation_ids():
    return jsonify(operation_data)

@app.route('/api/Progression/ItemPackages', methods=['GET'])
def get_item_packages():
    return jsonify(item_packages_data)

@app.route('/api/Progression/ProgressionPackages', methods=['GET'])
def get_progression_packages():
    return jsonify(progression_packages_data)

@app.route('/api/Progression/items', methods=['GET'])
def get_progression_items():
    return jsonify(progression_items_data)

@app.route('/api/Progression/levelspec', methods=['GET'])
def get_level_spec():
    return jsonify(level_spec_data)

@app.route('/api/Progression', methods=['GET'])
def get_progression():
    return jsonify(progression_data)

@app.route('/api/Progression/inventory', methods=['GET'])
def get_progression_inventory():
    return jsonify(progression_inventory_data)

@app.route('/api/Progression/customization', methods=['GET'])
def get_progression_customization():
    return jsonify({})

@app.route('/api/Mission/RewardEntries', methods=['GET'])
def get_reward_entries():
    return jsonify(reward_entries_data)

@app.route('/api/SeasonPass', methods=['GET'])
def get_season_pass():
    return jsonify(season_pass_data)

@app.route('/api/Progression/items/discounts/801', methods=['GET'])
def get_items_discounts():
    return jsonify([])

@app.route('/', methods=['GET'])
def generic_message():
    return jsonify({"message": "darkfluid-api running on this host"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)