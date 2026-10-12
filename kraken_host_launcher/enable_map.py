from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def enable_map(driver, enabled: bool, timeout: int = 5):
    """
    Włącza lub wyłącza minimapę (mmpWrapper) niezależnie od focusu gry.
    
    Parametry:
    - driver: Selenium WebDriver
    - enabled: True -> włącz minimapę, False -> wyłącz minimapę
    - timeout: maksymalny czas oczekiwania w sekundach
    """

    try:
        # Poczekaj aż wrapper się załaduje
        wrapper = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "mmpWrapper"))
        )
    except TimeoutException:
        raise RuntimeError("❌ Nie znaleziono mmpWrapper – minimapa nie istnieje")

    def is_map_enabled():
        style = wrapper.get_attribute("style") or ""
        return "display: block" in style

    currently_enabled = is_map_enabled()

    if currently_enabled == enabled:
        # Mapa już jest w żądanym stanie
        return

    # --- Wymuszenie stanu przez JS ---
    js_command = "document.querySelector('.mmpWrapper').style.display='block';" if enabled else "document.querySelector('.mmpWrapper').style.display='none';"
    driver.execute_script(js_command)

    # --- krótka pauza, żeby JS miał czas na zmianę ---
    time.sleep(0.2)

    # --- sprawdzenie efektu ---
    end_time = time.time() + timeout
    while time.time() < end_time:
        if is_map_enabled() == enabled:
            return
        time.sleep(0.05)

    # Jeśli mimo wszystko stan się nie zmienił, wyrzuć błąd
    raise RuntimeError(f"❌ Nie udało się {'włączyć' if enabled else 'wyłączyć'} minimapy")
