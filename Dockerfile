FROM python:3.10-slim

# Çalışma dizini oluşturun
WORKDIR /app

# Bağımlılıkları kopyalayıp kurun
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama dosyalarını kopyalayın
COPY . .

# start.sh dosyasını çalıştırılabilir yapın
RUN chmod +x start.sh

# Web sunucusu için portu açın
EXPOSE 6000

# Konteyner başladığında start.sh scriptini çalıştırın
CMD ["./start.sh"]
