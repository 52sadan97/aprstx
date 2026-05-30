# APRSTX - Dinamik APRS Gönderici & Yönetim Paneli 📡

**APRSTX**, belirlediğiniz konum, frekans, sembol ve mesaj bilgilerini APRS-IS ağına periyodik olarak gönderen; aynı zamanda tüm bu ayarları modern bir **Web Arayüzü** üzerinden dinamik olarak yönetebildiğiniz açık kaynaklı bir Python/Flask uygulamasıdır.

## 🌟 Özellikler

* **Karanlık Modlu Modern Arayüz:** Bootstrap 5 ile tasarlanmış, şık ve kullanımı kolay web yönetim paneli.
* **Sınırsız Paket Desteği:** Tek bir bot üzerinden dilediğiniz kadar farklı "Kaynak (Source)" ve "Konum" bilgisine sahip paket ekleyebilirsiniz. Paketler belirlediğiniz gecikme süreleriyle sırayla gönderilir.
* **Dinamik Veri Eklentileri:** Paketlerinizin "Açıklama" (Comment) bölümüne aşağıdaki kodları yazarak **anlık verileri** APRS ağına gönderebilirsiniz:
  * `{weather}` : Tam hava durumu bilgisi (Örn: *Korgan: 12.5C Ruzgar:10km/h*)
  * `{weather_short}` : Kısa hava durumu (Örn: *Korgan: 12.5C*)
  * `{quake}` : Türkiye'deki en son gerçekleşen >3.0 deprem bilgisi (Kandilli Rasathanesi verisi).
  * `{load}` : Sunucunun anlık İşlemci (CPU) Yükü.
  * `{ram}` : Sunucunun anlık RAM Kullanım yüzdesi.
  * `{uptime}` : Sunucunun sistem açık kalma süresi (Örn: *12d4h*).
* **Görsel Sembol Seçici:** Menüden araba (🚗), ev (🏠), anten (📡), hava istasyonu (☁️) gibi ikonları seçerek APRS sembol tablosu ve kodunu otomatik doldurabilme özelliği.
* **Rakım Belirtme (`/A=`):** Yükseklik verinizi Feet cinsinden sisteme girebilme bilgisi.
* **Docker Desteği:** Tek bir satır kodla hem web sunucusunu hem de botu ayağa kaldırabilme imkanı.

---

## 🛠 Kurulum & Kullanım (Docker ile)

Sistemi herhangi bir Linux sunucuda en güvenli ve stabil şekilde çalıştırmak için **Docker** kullanmanız önerilir.

### 1. Repoyu Klonlayın
```bash
git clone https://github.com/52sadan97/aprstx.git
cd aprstx
```

### 2. Örnek Konfigürasyonu Kopyalayın
Projeyi ilk indirdiğinizde güvenlik nedeniyle `config.json` gelmez. Örnek dosyayı kopyalayarak başlayın:
```bash
cp config.example.json config.json
```

### 3. Docker İmajını Oluşturun
```bash
docker build -t aprstx_app .
```

### 4. Konteyneri Başlatın
```bash
# Web arayüzü 6060 portunda çalışacak şekilde başlatılır
docker run -d --name aprstx -p 6060:6060 --restart always aprstx_app
```

> Artık web tarayıcınızdan `http://<sunucu-ip-adresiniz>:6060` adresine giderek sistemi yönetmeye başlayabilirsiniz!

---

## 💻 Manuel Kurulum (Docker Olmadan)

Eğer Docker kullanmak istemiyorsanız, doğrudan Python ile de çalıştırabilirsiniz. Python 3.10 veya üzeri önerilir.

```bash
# 1. Repoyu indirin
git clone https://github.com/52sadan97/aprstx.git
cd aprstx

# 2. Bağımlılıkları kurun
pip install -r requirements.txt

# 3. Konfigürasyonu ayarlayın
cp config.example.json config.json

# 4. Başlatıcı Scripti Çalıştırın (Bu script hem web uygulamasını hem botu aynı anda açar)
chmod +x start.sh
./start.sh
```

---

## 🔐 Güvenlik Notu

* `config.json` dosyanızda **Çağrı İşaretiniz (Callsign)** ve **APRS Şifreniz (Passcode)** bulunur. Bu dosya `.gitignore` tarafından yoksayılmaktadır, bu sayede şifreleriniz GitHub'a açıkça yüklenmez.
* Web arayüzüne varsayılan olarak herhangi bir şifre (Login) ekranı konulmamıştır. Eğer sunucunuz herkese açıksa, portları (`6060`) güvenlik duvarı üzerinden filtrelemeniz önerilir.

---
*Bu proje, telsizcilik ve amatör telsiz camiası için açık kaynaklı olarak geliştirilmiştir. 73!*
