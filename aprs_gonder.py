import aprslib
import time
import sys
import datetime
import urllib.request
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def send_beacon(config, packet):
    try:
        # APRS-IS sunucusuna bağlan
        server = config["aprs"].get("server", "euro.aprs2.net")
        port = int(config["aprs"].get("port", 14580))
        AIS = aprslib.IS(config["aprs"]["callsign"], passwd=config["aprs"]["passcode"], port=port, host=server)
        AIS.connect()
        AIS.sendall(packet)
        print(f"Gönderildi: {packet}")
        AIS.close()
    except Exception as e:
        print(f"Hata: {e}")
    sys.stdout.flush()

def get_korgan_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=40.8065&longitude=37.3424&current_weather=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            temp = data['current_weather']['temperature']
            wind = data['current_weather']['windspeed']
            return f"Korgan: {temp}C Ruzgar:{wind}km/h"
    except Exception as e:
        print(f"Hava durumu çekilemedi: {e}")
        return "Korgan: --C"

def get_last_earthquake():
    try:
        url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            # 3.0 büyüklüğünden büyük ilk depremi bul
            for eq in data.get('result', []):
                if eq.get('mag', 0) >= 3.0:
                    city = eq['title'].split('(')[-1].replace(')', '').strip().title()
                    return f"Son Deprem: {city} {eq['mag']}"
            # Yoksa en son depremi al
            if data.get('result'):
                eq = data['result'][0]
                city = eq['title'].split('(')[-1].replace(')', '').strip().title()
                return f"Son Deprem: {city} {eq['mag']}"
    except Exception as e:
        print(f"Deprem verisi çekilemedi: {e}")
    return ""

def build_packet(pkt_cfg, timestamp, weather_info, quake_info):
    if not pkt_cfg.get("enabled", False):
        return None
        
    weather_short = weather_info.split(' Ruzgar')[0] if ' Ruzgar' in weather_info else weather_info
    
    comment = pkt_cfg.get("comment", "").format(
        weather=weather_info,
        weather_short=weather_short,
        quake=quake_info
    )
    
    packet = f"{pkt_cfg['source']}>{pkt_cfg['destination']}:@{timestamp}{pkt_cfg['latitude']}{pkt_cfg['symbol_table']}{pkt_cfg['longitude']}{pkt_cfg['symbol_code']}{comment}"
    return packet

def send_multiple_beacons():
    try:
        config = load_config()
    except Exception as e:
        print(f"Konfigürasyon okunamadı, işlem iptal: {e}")
        return

    # Güncel UTC zamanını alıp APRS formatına (DDHHMMz) çevir
    now = datetime.datetime.utcnow()
    timestamp = now.strftime("%d%H%M") + "z"
    
    # Anlık verileri çek
    weather_info = get_korgan_weather()
    quake_info = get_last_earthquake()
    
    # Paketleri oluştur
    packet_1 = build_packet(config.get("packet1", {}), timestamp, weather_info, quake_info)
    packet_2 = build_packet(config.get("packet2", {}), timestamp, weather_info, quake_info)
    
    if packet_1:
        send_beacon(config, packet_1)
        
    if packet_1 and packet_2:
        delay = config.get("packet2", {}).get("delay_after_packet1_sec", 180)
        print(f"İkinci veri için {delay} saniye bekleniyor...")
        sys.stdout.flush()
        time.sleep(delay)
        
    if packet_2:
        send_beacon(config, packet_2)

if __name__ == "__main__":
    print("APRS Servisi başlatıldı. İlk paketler gönderiliyor...")
    sys.stdout.flush()
    
    # Konfigürasyon dosyasının varlığını bekle
    while not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} bekleniyor...")
        time.sleep(2)
        
    send_multiple_beacons()
    
    # Döngü
    while True:
        try:
            config = load_config()
            interval = int(config.get("intervals", {}).get("loop_interval_sec", 900))
        except Exception as e:
            print(f"Konfigürasyon okunamadı: {e}, varsayılan 900sn bekleniyor.")
            interval = 900
            
        print(f"Bir sonraki gönderim için {interval} saniye bekleniyor...")
        sys.stdout.flush()
        time.sleep(interval)
        print("Zamanı geldi, paketler gönderiliyor...")
        sys.stdout.flush()
        send_multiple_beacons()
