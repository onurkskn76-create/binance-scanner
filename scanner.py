import ccxt
import time
import requests

# Kendi Telegram Bilgilerini Buraya Doğrudan Yazabilirsin
TELEGRAM_TOKEN = "8136411060:AAEq_ESAkhg-f-eKAfKk6jzXO7j2FzJ9Zdw"
TELEGRAM_CHAT_ID = "7380293899"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram hatasi: {e}")

def run_scanner():
    exchange = ccxt.binance({'options': {'defaultType': 'future'}, 'enableRateLimit': True})
    
    print("Binance Futures pariteleri çekiliyor...")
    markets = exchange.load_markets()
    symbols = [s for s, m in markets.items() if m['linear'] and m['active'] and s.endswith('/USDT:USDT')]
    
    print(f"Toplam taranacak coin sayısı: {len(symbols)}")
    
    try:
        btc_ohlcv = exchange.fetch_ohlcv('BTC/USDT:USDT', timeframe='15m', limit=200)
        btc_closes = [c[4] for c in btc_ohlcv]
        btc_ema200 = sum(btc_closes) / len(btc_closes)
        is_btc_bull = btc_closes[-1] > btc_ema200
    except:
        is_btc_bull = True

    for symbol in symbols:
        try:
            ohlcv_15m = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=200)
            ohlcv_1h  = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
            
            if len(ohlcv_15m) < 200 or len(ohlcv_1h) < 50:
                continue
                
            closes_15m = [c[4] for c in ohlcv_15m]
            highs_15m  = [c[2] for c in ohlcv_15m]
            lows_15m   = [c[3] for c in ohlcv_15m]
            vols_15m   = [c[5] for c in ohlcv_15m]
            opens_15m  = [c[1] for c in ohlcv_15m]
            
            c_val, op_val = closes_15m[-1], opens_15m[-1]
            h_val, l_val, v_val = highs_15m[-1], lows_15m[-1], vols_15m[-1]
            
            # 5 Altın Filtre Hesabı
            ema200_15m = sum(closes_15m) / 200
            trend_up   = c_val > ema200_15m
            trend_down = c_val < ema200_15m
            
            closes_1h = [c[4] for c in ohlcv_1h]
            ema50_1h  = sum(closes_1h) / 50
            htf_bull  = closes_1h[-1] > ema50_1h
            
            btc_ok_long  = is_btc_bull
            btc_ok_short = not is_btc_bull
            
            delta = (c_val - op_val) / (h_val - l_val if h_val != l_val else 1) * v_val
            cvd_bull = delta > 0
            cvd_bear = delta < 0
            
            tr_list = [max(highs_15m[i] - lows_15m[i], abs(highs_15m[i] - closes_15m[i-1])) for i in range(1, len(ohlcv_15m))]
            atr = sum(tr_list[-14:]) / 14
            atr_ma = sum(tr_list[-50:]) / 50
            is_chaos = atr > (atr_ma * 2.2)
            
            is_clean = not is_chaos
            
            long_signal  = is_clean and trend_up and htf_bull and btc_ok_long and cvd_bull
            short_signal = is_clean and trend_down and not htf_bull and btc_ok_short and cvd_bear
            
            coin_name = symbol.split('/')[0]
            
            if long_signal:
                msg = f"🚀 *NET LONG GİRİŞ SİNYALİ!*\n\n📌 *Coin:* `{coin_name}USDT`\n💵 *Fiyat:* `{c_val}`\n🎯 *5/5 Filtre Onaylandı!*"
                send_telegram(msg)
            elif short_signal:
                msg = f"💥 *NET SHORT GİRİŞ SİNYALİ!*\n\n📌 *Coin:* `{coin_name}USDT`\n💵 *Fiyat:* `{c_val}`\n🎯 *5/5 Filtre Onaylandı!*"
                send_telegram(msg)
                
            time.sleep(0.1)
        except Exception as e:
            continue

if __name__ == "__main__":
    run_scanner()
