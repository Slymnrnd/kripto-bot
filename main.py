import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

TOKEN = "8763439212:AAFssZwIdgb9K2DAVMwTUUXJDenOExVwig8"
SYMBOLS = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "AVAX-USD", "DOGE-USD", "DOT-USD"]

class ProfesyonelKriptoAnalizor:
    def __init__(self, symbol):
        self.symbol = symbol
        self.df = None
        
    def veri_cek(self):
        try:
            self.df = yf.Ticker(self.symbol).history(period="1y")
            if self.df.empty or len(self.df) < 200:
                return False
            return True
        except:
            return False

    def vade_analizi_yap(self):
        if not self.veri_cek():
            return None
            
        df = self.df
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        df['BB_Mid'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Lower'] = df['BB_Mid'] - (bb_std * 2)
        df['BB_Upper'] = df['BB_Mid'] + (bb_std * 2)
        
        df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
        
        son = df.iloc[-1]
        close, rsi, sma50, sma200, ema20 = son['Close'], son['RSI'], son['SMA_50'], son['SMA_200'], son['EMA_20']
        bb_lower, bb_upper, vol, vol_ma = son['BB_Lower'], son['BB_Upper'], son['Volume'], son['Volume_MA']
        
        kisa_puan = 0
        if rsi < 40: kisa_puan += 1
        elif rsi > 70: kisa_puan -= 1
        if close <= bb_lower * 1.02: kisa_puan += 1
        elif close >= bb_upper * 0.98: kisa_puan -= 1
        if close > ema20: kisa_puan += 1
        else: kisa_puan -= 1
        
        orta_puan = 0
        if close > sma50: orta_puan += 2
        else: orta_puan -= 2
        if vol > vol_ma: orta_puan += 1
        else: orta_puan -= 1
        
        uzun_puan = 0
        if close > sma200: uzun_puan += 3
        else: uzun_puan -= 3
        if sma50 > sma200: uzun_puan += 1
            
        toplam_skor = kisa_puan + orta_puan + uzun_puan
        
        if toplam_skor >= 5:
            karar = "🟢 GÜÇLÜ AL"
        elif 2 <= toplam_skor < 5:
            karar = "🟢 AL"
        elif -1 <= toplam_skor < 2:
            karar = "⏳ BEKLE / NÖTR"
        elif -4 <= toplam_skor < -1:
            karar = "🔴 SAT"
        else:
            karar = "🚨 GÜÇLÜ SAT"
            
        return {
            "Fiyat": close,
            "RSI": rsi,
            "Skor": toplam_skor,
            "Karar": karar
        }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Profesyonel Kripto Analiz Botu Aktif**\n\n"
        "Komutlar:\n"
        "• `/tara` - Tüm havuzu çoklu indikatörle tarar.\n"
        "• *Coin Adı* (Örn: `ETH-USD` veya `SOL`) - Anlık detaylı skor analizi yapar."
    )

async def tara(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Piyasa çoklu indikatör matrisiyle taranıyor, lütfen bekleyin...")
    sonuclar = []
    for symbol in SYMBOLS:
        analizor = ProfesyonelKriptoAnalizor(symbol)
        res = analizor.vade_analizi_yap()
        if res:
            sonuclar.append(f"• **{symbol}**: ${res['Fiyat']:,.2f} | RSI: {res['RSI']:.1f} | **{res['Karar']}** (Skor: {res['Skor']})")

    mesaj = "📊 **PROFESYONEL PİYASA TARAMA RAPORU**\n\n" + "\n".join(sonuclar)
    await update.message.reply_text(mesaj, parse_mode="Markdown")

async def ozel_analiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip()
    if "-" not in text and len(text) <= 6:
        text = text + "-USD"
        
    await update.message.reply_text(f"🔍 {text} derinlemesine analiz ediliyor...")
    analizor = ProfesyonelKriptoAnalizor(text)
    res = analizor.vade_analizi_yap()
    
    if not res:
        await update.message.reply_text(f"❌ {text} için veri bulunamadı. Lütfen geçerli bir sembol girin.")
    else:
        await update.message.reply_text(
            f"📈 **{text} Profesyonel Analiz Sonucu:**\n\n"
            f"• Anlık Fiyat: ${res['Fiyat']:,.2f}\n"
            f"• RSI (14): {res['RSI']:.1f}\n"
            f"• Toplam Matematiksel Skor: {res['Skor']}\n"
            f"• **Net Karar: {res['Karar']}**",
            parse_mode="Markdown"
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tara", tara))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ozel_analiz))
    
    print("🤖 Telegram Botu bulut sunucuda başlatılıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
