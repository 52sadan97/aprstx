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
            
            # Update Intervals
            config.setdefault("intervals", {})
            config["intervals"]["loop_interval_sec"] = int(request.form.get("loop_interval_sec", 900))
            
            # Update Packets dynamically
            packets = []
            for i in range(100):  # Maximum 100 pakete kadar destekler
                # Formda bu ID'li bir kaynak varsa paketi al
                if f"packet_{i}_source" in request.form:
                    packet = {
                        "enabled": f"packet_{i}_enabled" in request.form,
                        "source": request.form.get(f"packet_{i}_source", ""),
                        "destination": request.form.get(f"packet_{i}_destination", "SDNNET,TCPIP*"),
                        "latitude": request.form.get(f"packet_{i}_latitude", ""),
                        "longitude": request.form.get(f"packet_{i}_longitude", ""),
                        "symbol_table": request.form.get(f"packet_{i}_symbol_table", "/"),
                        "symbol_code": request.form.get(f"packet_{i}_symbol_code", "-"),
                        "comment": request.form.get(f"packet_{i}_comment", ""),
                        "delay_sec": int(request.form.get(f"packet_{i}_delay", 0))
                    }
                    packets.append(packet)
            
            config["packets"] = packets
            
            save_config(config)
            flash("Ayarlar başarıyla kaydedildi!", "success")
        except Exception as e:
            flash(f"Hata oluştu: {str(e)}", "danger")
            
        return redirect(url_for("index"))
        
    if "packets" not in config:
        config["packets"] = []
        
    return render_template("index.html", config=config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6060, debug=False)
