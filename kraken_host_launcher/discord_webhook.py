import requests
import json
import os
from datetime import datetime

class DiscordWebhook:
    def __init__(self, config_path="alert/discord.json"):
        """Inicjalizacja webhooka Discord"""
        self.webhook_url = None
        self.enabled = False
        self.mention_role_id = None
        self.send_screenshot = False
        self.username = "Margonem Heros Bot"
        self.avatar_url = None
        
        # Sprawdź czy katalog alert/ istnieje
        alert_dir = os.path.dirname(config_path)
        if alert_dir and not os.path.exists(alert_dir):
            os.makedirs(alert_dir)
            print(f"📁 Utworzono katalog: {alert_dir}")
        
        # Wczytaj konfigurację
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.webhook_url = config.get("webhook_url")
                    self.enabled = config.get("enabled", True)
                    self.mention_role_id = config.get("mention_role_id")
                    self.send_screenshot = config.get("send_screenshot", False)
                    self.username = config.get("username", "Margonem Heros Bot")
                    self.avatar_url = config.get("avatar_url")
                    
                    if not self.webhook_url or self.webhook_url == "https://discord.com/api/webhooks/TWOJ_WEBHOOK_URL":
                        print("⚠️ Discord webhook nie został skonfigurowany w alert/discord.json")
                        self.enabled = False
                    elif self.enabled:
                        print("✅ Discord webhook aktywny")
            except json.JSONDecodeError as e:
                print(f"❌ Błąd parsowania {config_path}: {e}")
                self.enabled = False
        else:
            print(f"⚠️ Brak pliku konfiguracyjnego Discord: {config_path}")
            print(f"   Tworzę przykładowy plik...")
            self._create_example_config(config_path)
    
    def _create_example_config(self, config_path):
        """Tworzy przykładowy plik konfiguracyjny"""
        example_config = {
            "webhook_url": "https://discord.com/api/webhooks/TWOJ_WEBHOOK_URL",
            "enabled": False,
            "mention_role_id": None,
            "send_screenshot": False,
            "username": "Margonem Heros Bot",
            "avatar_url": None
        }
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(example_config, f, indent=2, ensure_ascii=False)
            print(f"✅ Utworzono przykładowy plik: {config_path}")
            print(f"   Edytuj plik i dodaj swój webhook URL z Discorda")
        except Exception as e:
            print(f"❌ Nie można utworzyć pliku: {e}")
    
    def send_heros_alert(self, heros_name=None, map_name=None, coords=None, screenshot_path=None):
        """
        Wysyła alert o znalezieniu herosa na Discord
        
        Args:
            heros_name: nazwa herosa (opcjonalne)
            map_name: nazwa mapy
            coords: tuple (x, y) współrzędne
            screenshot_path: ścieżka do screenshota (opcjonalne)
        """
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Podstawowa treść wiadomości
            content = ""
            if self.mention_role_id:
                content = f"<@&{self.mention_role_id}> "
            
            # Embed Discord
            embed = {
                "title": "🎉 ZNALEZIONO HEROSA! 🎉",
                "color": 0xFF6B00,  # Pomarańczowy kolor
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [],
                "footer": {
                    "text": "Margonem Bot"
                }
            }
            
            # Dodaj informacje o herosie
            if heros_name:
                embed["fields"].append({
                    "name": "👹 Heros",
                    "value": heros_name,
                    "inline": True
                })
            
            if map_name:
                embed["fields"].append({
                    "name": "🗺️ Mapa",
                    "value": map_name,
                    "inline": True
                })
            
            if coords:
                embed["fields"].append({
                    "name": "📍 Koordynaty",
                    "value": f"({coords[0]}, {coords[1]})",
                    "inline": True
                })
            
            embed["fields"].append({
                "name": "⏰ Czas",
                "value": timestamp,
                "inline": False
            })
            
            # Przygotuj payload
            payload = {
                "content": content,
                "embeds": [embed]
            }
            
            # Dodaj username i avatar jeśli są ustawione
            if self.username:
                payload["username"] = self.username
            if self.avatar_url:
                payload["avatar_url"] = self.avatar_url
            
            # Wyślij webhook
            if screenshot_path and self.send_screenshot and os.path.exists(screenshot_path):
                # Wyślij ze screenshotem
                with open(screenshot_path, 'rb') as f:
                    files = {'file': (os.path.basename(screenshot_path), f)}
                    response = requests.post(
                        self.webhook_url,
                        data={"payload_json": json.dumps(payload)},
                        files=files,
                        timeout=10
                    )
            else:
                # Wyślij bez screenshota
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )
            
            if response.status_code in [200, 204]:
                print("✅ Wysłano powiadomienie na Discord")
                return True
            else:
                print(f"⚠️ Błąd wysyłania na Discord: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            print("⏱️ Timeout podczas wysyłania na Discord")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Błąd połączenia z Discord: {e}")
            return False
        except Exception as e:
            print(f"❌ Błąd wysyłania webhooka Discord: {e}")
            return False
    
    def send_simple_message(self, message):
        """Wysyła prostą wiadomość tekstową"""
        if not self.enabled or not self.webhook_url:
            return False
        
        try:
            payload = {"content": message}
            
            if self.username:
                payload["username"] = self.username
            if self.avatar_url:
                payload["avatar_url"] = self.avatar_url
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"❌ Błąd wysyłania wiadomości: {e}")
            return False
    
    def test_webhook(self):
        """Testuje czy webhook działa"""
        if not self.webhook_url:
            print("❌ Webhook URL nie został skonfigurowany")
            return False
        
        print("🧪 Testuję połączenie z Discord...")
        return self.send_simple_message("✅ Test połączenia - webhook działa poprawnie!")