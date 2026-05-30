#!/bin/bash
# Web arayüzünü arka planda başlat
python -u app.py &

# APRS gönderici scriptini başlat
python -u aprs_gonder.py
