from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

app = Flask(__name__)
app.secret_key = "super_secret_key_aprstx" # Change for production if needed

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

@app.route("/", methods=["GET", "POST"])
def index():
    config = load_config()
    
    if request.method == "POST":
        try:
            # Update APRS Settings
            config.setdefault("aprs", {})
            config["aprs"]["callsign"] = request.form.get("aprs_callsign")
            config["aprs"]["passcode"] = request.form.get("aprs_passcode")
            config["aprs"]["server"] = request.form.get("aprs_server", "euro.aprs2.net")
            config["aprs"]["port"] = int(request.form.get("aprs_port", 14580))
            
            # Update Packet 1
            config.setdefault("packet1", {})
            config["packet1"]["enabled"] = "packet1_enabled" in request.form
            config["packet1"]["source"] = request.form.get("packet1_source")
            config["packet1"]["destination"] = request.form.get("packet1_destination")
            config["packet1"]["latitude"] = request.form.get("packet1_latitude")
            config["packet1"]["longitude"] = request.form.get("packet1_longitude")
            config["packet1"]["symbol_table"] = request.form.get("packet1_symbol_table")
            config["packet1"]["symbol_code"] = request.form.get("packet1_symbol_code")
            config["packet1"]["comment"] = request.form.get("packet1_comment")
            
            # Update Packet 2
            config.setdefault("packet2", {})
            config["packet2"]["enabled"] = "packet2_enabled" in request.form
            config["packet2"]["source"] = request.form.get("packet2_source")
            config["packet2"]["destination"] = request.form.get("packet2_destination")
            config["packet2"]["latitude"] = request.form.get("packet2_latitude")
            config["packet2"]["longitude"] = request.form.get("packet2_longitude")
            config["packet2"]["symbol_table"] = request.form.get("packet2_symbol_table")
            config["packet2"]["symbol_code"] = request.form.get("packet2_symbol_code")
            config["packet2"]["comment"] = request.form.get("packet2_comment")
            config["packet2"]["delay_after_packet1_sec"] = int(request.form.get("packet2_delay", 180))
            
            # Update Intervals
            config.setdefault("intervals", {})
            config["intervals"]["loop_interval_sec"] = int(request.form.get("loop_interval_sec", 900))
            
            save_config(config)
            flash("Ayarlar başarıyla kaydedildi!", "success")
        except Exception as e:
            flash(f"Hata oluştu: {str(e)}", "danger")
            
        return redirect(url_for("index"))
        
    return render_template("index.html", config=config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=False)
