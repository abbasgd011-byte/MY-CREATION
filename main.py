import flet as ft
import requests
from datetime import datetime
import threading
import time

# --- CONFIGURATION (REPLACE WITH YOUR ACTUAL DETAILS) ---
TOKEN_ID = "20260831193748364470041"
REG_NO = "SNK4HQK4MA"
API_URL = f"https://www.solaxcloud.com/proxyApp/proxy/api/getRealtimeInfo.do?tokenId={TOKEN_ID}&sn={REG_NO}"
THRESHOLDS = [100, 125, 150]

def main(page: ft.Page):
    page.title = "Solar Meter Monitor"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Load persistent storage on Android
    baseline = page.client_storage.get("baseline")
    cycle_count = page.client_storage.get("cycle_count") or 1
    last_alert = page.client_storage.get("last_alert") or 0
    history = page.client_storage.get("history") or []

    # Display Elements
    title_text = ft.Text("CURRENT METER UNITS", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
    units_text = ft.Text("0.0 kWh", size=55, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_400)
    status_text = ft.Text("Status: Initializing...", size=16)
    cycle_text = ft.Text(f"Active Meter Cycle: #{cycle_count}", size=16, italic=True)
    
    # Audio Alert Player
    alarm_audio = ft.Audio(src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg", autoplay=False)
    page.overlay.append(alarm_audio)

    def fetch_api():
        try:
            res = requests.get(API_URL, timeout=10)
            data = res.json()
            if data.get("success"):
                return float(data["result"].get("consumeenergy", 0))
        except Exception:
            return None

    def reset_meter(e):
        nonlocal baseline, cycle_count, last_alert, history
        
        # Save previous reading to history
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_units = float(units_text.value.replace(" kWh", ""))
        history.insert(0, f"Cycle #{cycle_count}: {current_units} kWh ({now_str})")
        
        # Reset counters to new meter baseline
        current_total = fetch_api()
        if current_total is not None:
            baseline = current_total
            page.client_storage.set("baseline", baseline)
            
        cycle_count += 1
        last_alert = 0
        page.client_storage.set("cycle_count", cycle_count)
        page.client_storage.set("last_alert", last_alert)
        page.client_storage.set("history", history[:10])
        
        units_text.value = "0.0 kWh"
        units_text.color = ft.colors.GREEN_400
        cycle_text.value = f"Active Meter Cycle: #{cycle_count}"
        status_text.value = "Status: New Meter Started!"
        page.update()

    btn_change = ft.ElevatedButton(
        text="I HAVE CHANGED THE METER\n(Reset to 0 & Save)",
        bgcolor=ft.colors.RED_400,
        color=ft.colors.WHITE,
        width=320,
        height=85,
        on_click=reset_meter
    )

    page.add(title_text, units_text, status_text, cycle_text, ft.Divider(height=40), btn_change)

    # Background Polling Thread
    def auto_poll():
        nonlocal baseline, last_alert
        while True:
            total_import = fetch_api()
            if total_import is not None:
                if baseline is None:
                    baseline = total_import
                    page.client_storage.set("baseline", baseline)

                units_used = round(total_import - baseline, 2)
                if units_used < 0:
                    units_used = 0.0

                units_text.value = f"{units_used:.1f} kWh"
                
                # Check threshold alerts
                triggered = None
                for t in THRESHOLDS:
                    if units_used >= t and last_alert < t:
                        triggered = t
                
                if triggered:
                    last_alert = triggered
                    page.client_storage.set("last_alert", last_alert)
                    status_text.value = f"⚠️ ALERT: REACHED {triggered} UNITS!"
                    units_text.color = ft.colors.RED_400
                    alarm_audio.play()
                elif triggered is None and units_text.color != ft.colors.RED_400:
                    status_text.value = f"Status: Normal ({units_used:.1f} kWh used)"
                    units_text.color = ft.colors.GREEN_400
                    
                page.update()
            
            time.sleep(300) # Checks every 5 minutes

    threading.Thread(target=auto_poll, daemon=True).start()

ft.app(target=main)
