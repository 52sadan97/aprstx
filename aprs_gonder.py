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

class SafeDict(dict):
    """Bilinmeyen değişkenleri olduğu gibi bırakan güvenli sözlük.
    Örn: Kullanıcı {bilinmeyen} yazarsa hata vermez, olduğu gibi kalır."""
    def __missing__(self, key):
        return '{' + key + '}'

# ============================================================
# VERİ KAYNAKLARI
# ============================================================

def get_all_weather_data():
    """Hava durumu + gün doğumu/batımı (Open-Meteo, tek API çağrısı)"""
    try:
        url = ("https://api.open-meteo.com/v1/forecast?"
               "latitude=40.8065&longitude=37.3424"
               "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
               "precipitation,uv_index,wind_speed_10m"
               "&daily=sunrise,sunset"
               "&timezone=Europe/Istanbul&forecast_days=1")
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            c = data['current']
            d = data.get('daily', {})
            
            temp = c['temperature_2m']
            wind = c['wind_speed_10m']
            humidity = int(c['relative_humidity_2m'])
            feels = c['apparent_temperature']
            precip = c['precipitation']
            uv = int(c['uv_index'])
            
            sr = d.get('sunrise', [''])[0]
            ss = d.get('sunset', [''])[0]
            sunrise = sr.split('T')[1][:5] if 'T' in str(sr) else '--:--'
            sunset = ss.split('T')[1][:5] if 'T' in str(ss) else '--:--'
            
            return {
                "weather": f"Korgan: {temp}C Ruzgar:{wind}km/h",
                "weather_short": f"Korgan: {temp}C",
                "humidity": f"Nem:%{humidity}",
                "uv": f"UV:{uv}",
                "feels_like": f"Hissedilen:{feels:.1f}C",
                "precip": f"Yagis:{precip}mm",
                "sunrise": f"Dogum:{sunrise}",
                "sunset": f"Batim:{sunset}",
            }
    except Exception as e:
        print(f"Hava durumu çekilemedi: {e}")
        return {
            "weather": "Korgan: --C", "weather_short": "Korgan: --C",
            "humidity": "Nem:--%", "uv": "UV:--", "feels_like": "Hissedilen:--C",
            "precip": "Yagis:--mm", "sunrise": "Dogum:--:--", "sunset": "Batim:--:--",
        }

def get_air_quality():
    """Hava kalitesi - PM2.5, AQI (Open-Meteo Air Quality)"""
    try:
        url = ("https://air-quality-api.open-meteo.com/v1/air-quality?"
               "latitude=40.8065&longitude=37.3424"
               "&current=pm2_5,pm10,european_aqi")
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            c = data['current']
            aqi = int(c['european_aqi'])
            pm25 = c['pm2_5']
            
            if aqi <= 20: seviye = "Iyi"
            elif aqi <= 40: seviye = "Orta"
            elif aqi <= 60: seviye = "Hassas"
            elif aqi <= 80: seviye = "Kotu"
            else: seviye = "CokKotu"
            
            return {"aqi": f"AQI:{aqi}({seviye})", "pm25": f"PM2.5:{pm25:.1f}"}
    except Exception as e:
        print(f"Hava kalitesi çekilemedi: {e}")
        return {"aqi": "AQI:--", "pm25": "PM2.5:--"}

def get_last_earthquake():
    """Türkiye'deki son deprem bilgisi (Kandilli Rasathanesi)"""
    try:
        url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            # 3.0 büyüklüğünden büyük ilk depremi bul
            for eq in data.get('result', []):
                if eq.get('mag', 0) >= 3.0:
                    city = eq['title'].split('(')[-1].replace(')', '').strip().title()
                    return {"quake": f"Son Deprem: {city} {eq['mag']}"}
            # Yoksa en son depremi al
            if data.get('result'):
                eq = data['result'][0]
                city = eq['title'].split('(')[-1].replace(')', '').strip().title()
                return {"quake": f"Son Deprem: {city} {eq['mag']}"}
    except Exception as e:
        print(f"Deprem verisi çekilemedi: {e}")
    return {"quake": ""}

def get_solar_data():
    """Güneş aktivitesi ve propagasyon verileri (NOAA SWPC) - HAM radio için"""
    sfi_val = "--"
    kp_val = "--"
    k_desc = ""
    
    try:
        # Solar Flux Index (10.7cm)
        url_sfi = "https://services.swpc.noaa.gov/products/summary/10cm-flux.json"
        req = urllib.request.Request(url_sfi, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if len(data) > 0:
                sfi_val = data[-1].get('flux', '--')
    except Exception as e:
        print(f"Solar flux çekilemedi: {e}")
    
    try:
        # Planetary K-Index
        url_k = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        req = urllib.request.Request(url_k, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if len(data) > 0:
                kp_val = data[-1].get('Kp', '--')
                if kp_val != '--':
                    kp_num = float(kp_val)
                    if kp_num <= 2: k_desc = "Sakin"
                    elif kp_num <= 4: k_desc = "Aktif"
                    else: k_desc = "Firtina"
    except Exception as e:
        print(f"K-Index çekilemedi: {e}")
    
    k_str = f"K:{kp_val}({k_desc})" if k_desc else f"K:{kp_val}"
    
    return {
        "sfi": f"SFI:{sfi_val}",
        "kindex": k_str,
        "solar": f"SFI:{sfi_val} {k_str}",
    }

def get_exchange_rates():
    """Döviz kurları - USD/TRY, EUR/TRY (Frankfurter / ECB verisi)"""
    usd_try = "--"
    eur_try = "--"
    
    try:
        url = "https://api.frankfurter.dev/v1/latest?base=USD&symbols=TRY"
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            usd_try = f"{data['rates']['TRY']:.2f}"
    except Exception as e:
        print(f"USD kuru çekilemedi: {e}")
    
    try:
        url = "https://api.frankfurter.dev/v1/latest?base=EUR&symbols=TRY"
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            eur_try = f"{data['rates']['TRY']:.2f}"
    except Exception as e:
        print(f"EUR kuru çekilemedi: {e}")
    
    return {
        "dolar": f"USD:{usd_try}",
        "euro": f"EUR:{eur_try}",
        "kur": f"USD:{usd_try} EUR:{eur_try}",
    }

def get_prayer_times():
    """Namaz vakitleri - Diyanet hesaplama yöntemi (AlAdhan API)"""
    try:
        now_tr = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
        date_str = now_tr.strftime("%d-%m-%Y")
        url = (f"https://api.aladhan.com/v1/timings/{date_str}"
               f"?latitude=40.8065&longitude=37.3424&method=13"
               f"&timezonestring=Europe/Istanbul")
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            t = data['data']['timings']
            
            # Zaman dizelerini temizle (bazen " (EET)" gibi ekler olabiliyor)
            def clean(time_str):
                return time_str.split(' ')[0] if ' ' in time_str else time_str
            
            fajr = clean(t['Fajr'])
            dhuhr = clean(t['Dhuhr'])
            asr = clean(t['Asr'])
            maghrib = clean(t['Maghrib'])
            isha = clean(t['Isha'])
            
            # Sıradaki vakti bul
            current_time = now_tr.strftime("%H:%M")
            prayer_order = [
                ("Imsak", fajr),
                ("Gunes", clean(t['Sunrise'])),
                ("Ogle", dhuhr),
                ("Ikindi", asr),
                ("Aksam", maghrib),
                ("Yatsi", isha),
            ]
            
            next_name, next_time = prayer_order[0]
            for name, ptime in prayer_order:
                if ptime > current_time:
                    next_name = name
                    next_time = ptime
                    break
            
            return {
                "namaz": f"Ogle:{dhuhr} Ikindi:{asr} Aksam:{maghrib}",
                "ezan": f"Siradaki:{next_name} {next_time}",
                "imsak": f"Imsak:{fajr}",
            }
    except Exception as e:
        print(f"Namaz vakitleri çekilemedi: {e}")
        return {"namaz": "", "ezan": "", "imsak": ""}

def get_sea_temperature():
    """Karadeniz deniz suyu sıcaklığı (Open-Meteo Marine)"""
    try:
        url = ("https://marine-api.open-meteo.com/v1/marine?"
               "latitude=41.0&longitude=37.3"
               "&current=sea_surface_temperature")
        req = urllib.request.Request(url, headers={'User-Agent': 'APRSTX/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            sea_temp = data['current']['sea_surface_temperature']
            return {"deniz": f"Karadeniz:{sea_temp:.1f}C"}
    except Exception as e:
        print(f"Deniz sıcaklığı çekilemedi: {e}")
        return {"deniz": "Karadeniz:--C"}

def get_sys_info():
    """Sunucu sistem bilgileri (sadece Linux)"""
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

# ============================================================
# PAKET OLUŞTURMA VE GÖNDERME
# ============================================================

def build_packet(pkt_cfg, timestamp, all_data):
    """APRS paketini oluşturur. Comment alanındaki {degisken} ifadeleri otomatik doldurulur."""
    if not pkt_cfg.get("enabled", False):
        return None
    
    # SafeDict ile bilinmeyen değişkenler hata vermez, olduğu gibi kalır
    comment = pkt_cfg.get("comment", "").format_map(SafeDict(all_data))
    
    packet = (f"{pkt_cfg['source']}>{pkt_cfg['destination']}:"
              f"@{timestamp}{pkt_cfg['latitude']}{pkt_cfg['symbol_table']}"
              f"{pkt_cfg['longitude']}{pkt_cfg['symbol_code']}{comment}")
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
    
    # Tüm veri kaynaklarını tek sözlükte topla
    print("Veriler çekiliyor...")
    sys.stdout.flush()
    
    all_data = {}
    all_data.update(get_all_weather_data())
    all_data.update(get_air_quality())
    all_data.update(get_last_earthquake())
    all_data.update(get_solar_data())
    all_data.update(get_exchange_rates())
    all_data.update(get_prayer_times())
    all_data.update(get_sea_temperature())
    all_data.update(get_sys_info())
    
    print(f"Toplam {len(all_data)} değişken hazır.")
    sys.stdout.flush()
    
    packets = config.get("packets", [])
    
    for i, pkt_cfg in enumerate(packets):
        packet = build_packet(pkt_cfg, timestamp, all_data)
        
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
