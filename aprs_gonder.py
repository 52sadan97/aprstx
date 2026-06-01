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
        server = config.get("aprs", {}).get("server", "euro.aprs2.net")
        port = int(config.get("aprs", {}).get("port", 14580))
        callsign = config.get("aprs", {}).get("callsign", "")
        passcode = config.get("aprs", {}).get("passcode", "")
        
        AIS = aprslib.IS(callsign, passwd=passcode, port=port, host=server)
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

def get_sys_info():
    try:
        # Yük Ortalaması (Load Average - 1 dakikalık)
        load1, load5, load15 = os.getloadavg()
        
        # RAM Kullanımı
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        mem_total = mem_avail = mem_free = 0
        for line in lines:
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1])
            elif line.startswith('MemFree:'):
                mem_free = int(line.split()[1])
            elif line.startswith('MemAvailable:'):
                mem_avail = int(line.split()[1])
        if mem_avail == 0: mem_avail = mem_free
        mem_used = mem_total - mem_avail
        ram_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0
        
        # Çalışma Süresi (Uptime)
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        uptime_days = int(uptime_seconds // 86400)
        uptime_hours = int((uptime_seconds % 86400) // 3600)
        
        if uptime_days > 0:
            uptime_str = f"{uptime_days}d{uptime_hours}h"
        else:
            uptime_str = f"{uptime_hours}h"
            
        return {
            "load": f"{load1:.2f}",
            "ram": f"{ram_percent:.1f}%",
            "uptime": uptime_str
        }
    except Exception as e:
        return {"load": "N/A", "ram": "N/A", "uptime": "N/A"}

def build_packet(pkt_cfg, timestamp, weather_info, quake_info, sys_info):
    if not pkt_cfg.get("enabled", False):
        return None
        
    weather_short = weather_info.split(' Ruzgar')[0] if ' Ruzgar' in weather_info else weather_info
    
    comment = pkt_cfg.get("comment", "").format(
        weather=weather_info,
        weather_short=weather_short,
        quake=quake_info,
        load=sys_info["load"],
        ram=sys_info["ram"],
        uptime=sys_info["uptime"]
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
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%d%H%M") + "z"
    
    # Anlık verileri çek
    weather_info = get_korgan_weather()
    quake_info = get_last_earthquake()
    sys_info = get_sys_info()
    
    packets = config.get("packets", [])
    
    for i, pkt_cfg in enumerate(packets):
        packet = build_packet(pkt_cfg, timestamp, weather_info, quake_info, sys_info)
        
        if packet:
            send_beacon(config, packet)
            
            # Sonraki paket için bekleme süresi
            delay = pkt_cfg.get("delay_sec", 0)
            # Eğer dizideki son paket değilse veya özel bir bekleme varsa bekle
            if delay > 0 and i < len(packets) - 1:
                print(f"Bir sonraki paket için {delay} saniye bekleniyor...")
                sys.stdout.flush()
                time.sleep(delay)

if __name__ == "__main__":
    print("APRS Servisi başlatıldı. İlk paketler gönderiliyor...")
    sys.stdout.flush()
    
    # Konfigürasyon dosyasının varlığını bekle
    while not os.path.exists(CONFIG_FILE):
        print(f"{CONFIG_FILE} bekleniyor...")
        time.sleep(2)
        
    last_send_time = time.time()
    send_multiple_beacons()
    
    # Döngü
    while True:
        try:
            config = load_config()
            interval = int(config.get("intervals", {}).get("loop_interval_sec", 900))
        except Exception as e:
            # print(f"Konfigürasyon okunamadı: {e}, varsayılan 900sn bekleniyor.") # Çok log basmaması için kapatıldı
            interval = 900
            
        now = time.time()
        if now - last_send_time >= interval:
            print("Zamanı geldi, paketler gönderiliyor...")
            sys.stdout.flush()
            send_multiple_beacons()
            last_send_time = time.time()
            
        # 5 saniyede bir konfigürasyonu kontrol et, böylece arayüzden yapılan değişiklik anında işleme alınır
        time.sleep(5)
