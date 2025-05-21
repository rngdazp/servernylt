from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# In-memory ban storage
ban_data = {}
timed_bans = {}

@app.route("/")
def index():
    return "Roblox Moderation API is live."

@app.route("/ban", methods=["POST"])
def ban():
    data = request.json
    user_id = data.get("user_id")
    reason = data.get("reason", "No reason provided.")
    admin = data.get("admin", "Unknown")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    ban_data[user_id] = {"reason": reason, "admin": admin, "timestamp": time.time()}
    return jsonify({"status": "banned", "user_id": user_id})

@app.route("/kick", methods=["POST"])
def kick():
    data = request.json
    user_id = data.get("user_id")
    reason = data.get("reason", "No reason provided.")
    admin = data.get("admin", "Unknown")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    return jsonify({
        "status": "kick",
        "user_id": user_id,
        "reason": reason,
        "admin": admin
    })

@app.route("/unban", methods=["POST"])
def unban():
    data = request.json
    user_id = data.get("user_id")

    if user_id in ban_data:
        del ban_data[user_id]
        return jsonify({"status": "unbanned", "user_id": user_id})
    else:
        return jsonify({"error": "User not banned"}), 404

@app.route("/ban-check", methods=["GET"])
def ban_check():
    user_id = request.args.get("user_id")
    if user_id in ban_data:
        return jsonify({"banned": True, **ban_data[user_id]})
    else:
        return jsonify({"banned": False})

@app.route("/timed-ban", methods=["POST"])
def timed_ban():
    data = request.json
    user_id = data.get("user_id")
    duration = data.get("duration", 60)
    reason = data.get("reason", "No reason provided.")
    admin = data.get("admin", "Unknown")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    expire_time = time.time() + duration
    timed_bans[user_id] = {
        "reason": reason,
        "admin": admin,
        "expire_time": expire_time
    }

    return jsonify({"status": "timed_banned", "user_id": user_id, "expires_in": duration})

@app.route("/timed-ban-check", methods=["GET"])
def timed_ban_check():
    user_id = request.args.get("user_id")

    ban = timed_bans.get(user_id)
    if ban:
        if time.time() >= ban["expire_time"]:
            del timed_bans[user_id]
            return jsonify({"banned": False})
        else:
            return jsonify({
                "banned": True,
                "reason": ban["reason"],
                "admin": ban["admin"],
                "remaining": ban["expire_time"] - time.time()
            })
    return jsonify({"banned": False})

# ✅ NEW: Combined moderation command endpoint
@app.route("/api/moderate", methods=["POST"])
def moderate():
    data = request.json
    command = data.get("command")
    user_id = data.get("user_id")
    reason = data.get("reason", "No reason provided.")
    admin = data.get("admin", "Unknown")

    if not user_id or not command:
        return jsonify({"error": "Missing user_id or command"}), 400

    command = command.lower()

    if command == "ban":
        ban_data[user_id] = {"reason": reason, "admin": admin, "timestamp": time.time()}
        return jsonify({"status": "banned", "user_id": user_id})
    
    elif command == "kick":
        return jsonify({
            "status": "kick",
            "user_id": user_id,
            "reason": reason,
            "admin": admin
        })
    
    elif command == "unban":
        if user_id in ban_data:
            del ban_data[user_id]
            return jsonify({"status": "unbanned", "user_id": user_id})
        else:
            return jsonify({"error": "User not banned"}), 404

    elif command == "timedban":
        duration = data.get("duration", 60)
        expire_time = time.time() + duration
        timed_bans[user_id] = {
            "reason": reason,
            "admin": admin,
            "expire_time": expire_time
        }
        return jsonify({"status": "timed_banned", "user_id": user_id, "expires_in": duration})

    return jsonify({"error": f"Unknown command '{command}'"}), 400

# ✅ NEW: Used by Roblox to check if a user is banned or timed-banned
@app.route("/api/isBanned/<user_id>", methods=["GET"])
def is_banned(user_id):
    if user_id in ban_data:
        return jsonify({"banned": True, **ban_data[user_id]})
    
    timed = timed_bans.get(user_id)
    if timed:
        if time.time() >= timed["expire_time"]:
            del timed_bans[user_id]
            return jsonify({"banned": False})
        else:
            return jsonify({
                "banned": True,
                "reason": timed["reason"],
                "admin": timed["admin"],
                "remaining": timed["expire_time"] - time.time()
            })

    return jsonify({"banned": False})

# ✅ NEW: Returns all current bans and timed bans (for debugging)
@app.route("/api/getActions", methods=["GET"])
def get_actions():
    actions = {
        "bans": ban_data,
        "timed_bans": {
            k: {
                "reason": v["reason"],
                "admin": v["admin"],
                "remaining": v["expire_time"] - time.time()
            } for k, v in timed_bans.items() if v["expire_time"] > time.time()
        }
    }
    return jsonify(actions)

if __name__ == "__main__":
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule} - Methods: {rule.methods}")

    app.run(host="0.0.0.0", port=5000)
