# captcha.py

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random


def click_solve_now(driver, timeout=2):
    """
    Klika przycisk 'Rozwiąż teraz' aby rozpocząć captchę.
    
    Returns:
        bool: True jeśli kliknięto, False jeśli nie znaleziono (może być już otwarta)
    """
    try:
        # Szukaj przycisku z tekstem "Rozwiąż teraz"
        solve_button = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='label' and text()='Rozwiąż teraz']")
            )
        )
        
        print("🎯 Klikam 'Rozwiąż teraz'...")
        
        # Znajdź parent button
        parent_button = solve_button.find_element(By.XPATH, "./..")
        
        # Kliknij z ActionChains
        actions = ActionChains(driver)
        actions.move_to_element(parent_button)
        actions.pause(random.uniform(0.15, 0.25))
        actions.click()
        actions.perform()
        
        time.sleep(random.uniform(0.5, 0.8))
        return True
        
    except (TimeoutException, NoSuchElementException):
        # Brak przycisku - captcha może być już otwarta
        return False
    except Exception as e:
        print(f"⚠️ Błąd przy klikaniu 'Rozwiąż teraz': {e}")
        return False


def click_star_buttons(driver, timeout=3):
    """
    Klika wszystkie przyciski z gwiazdkami (*) które nie są jeszcze pressed.
    
    Returns:
        int: Liczba klikniętych przycisków
    """
    try:
        # Poczekaj na pojawienie się przycisków captchy
        captcha_container = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".captcha__buttons"))
        )
        
        print("🔐 Rozwiązuję captchę - wybieram przyciski z *...")
        
        # Małe opóźnienie jak prawdziwy gracz
        time.sleep(random.uniform(0.3, 0.6))
        
        # Znajdź wszystkie przyciski BEZ klasy 'pressed'
        buttons = captcha_container.find_elements(
            By.CSS_SELECTOR, 
            ".button:not(.pressed)"
        )
        
        clicked_count = 0
        
        for button in buttons:
            try:
                # Znajdź label wewnątrz przycisku
                label = button.find_element(By.CLASS_NAME, "label")
                text = label.text.strip()
                
                # Sprawdź czy zawiera gwiazdkę
                if "*" in text:
                    print(f"  ✓ Klikam przycisk: {text}")
                    
                    # Symuluj naturalne ruchy myszy
                    actions = ActionChains(driver)
                    actions.move_to_element(button)
                    actions.pause(random.uniform(0.1, 0.2))
                    actions.click()
                    actions.perform()
                    
                    clicked_count += 1
                    
                    # Losowe opóźnienie między kliknięciami
                    time.sleep(random.uniform(0.25, 0.45))
                    
            except Exception as e:
                print(f"  ⚠️ Błąd przy klikaniu przycisku: {e}")
                continue
        
        if clicked_count > 0:
            print(f"✅ Zaznaczono {clicked_count} przycisków z gwiazdkami")
        else:
            print("ℹ️ Brak nowych przycisków do zaznaczenia")
        
        return clicked_count
            
    except TimeoutException:
        print("⚠️ Nie znaleziono przycisków captchy")
        return 0
    except Exception as e:
        print(f"⚠️ Błąd przy klikaniu przycisków: {e}")
        return 0


def click_confirm(driver, timeout=3):
    """
    Klika przycisk 'Potwierdzam' aby zakończyć captchę.
    
    Returns:
        bool: True jeśli kliknięto, False jeśli nie znaleziono
    """
    try:
        # Szukaj przycisku z tekstem "Potwierdzam"
        confirm_label = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='label' and text()='Potwierdzam']")
            )
        )
        
        print("✅ Klikam 'Potwierdzam'...")
        
        # Znajdź parent button
        parent_button = confirm_label.find_element(By.XPATH, "./..")
        
        # Kliknij z ActionChains
        actions = ActionChains(driver)
        actions.move_to_element(parent_button)
        actions.pause(random.uniform(0.15, 0.25))
        actions.click()
        actions.perform()
        
        time.sleep(random.uniform(0.5, 0.8))
        print("🎉 Captcha rozwiązana!")
        return True
        
    except (TimeoutException, NoSuchElementException):
        print("⚠️ Nie znaleziono przycisku 'Potwierdzam'")
        return False
    except Exception as e:
        print(f"⚠️ Błąd przy klikaniu 'Potwierdzam': {e}")
        return False


def is_captcha_visible(driver):
    """
    Sprawdza czy captcha jest widoczna (przyciski z opcjami).
    
    Returns:
        bool: True jeśli captcha jest widoczna
    """
    try:
        driver.find_element(By.CSS_SELECTOR, ".captcha__buttons")
        return True
    except NoSuchElementException:
        return False


def solve_captcha_full(driver):
    """
    Pełny proces rozwiązywania captchy:
    1. Sprawdź czy captcha jest już otwarta
    2. Jeśli nie - spróbuj kliknąć "Rozwiąż teraz"
    3. Zaznacz wszystkie przyciski z *
    4. Kliknij "Potwierdzam"
    
    Returns:
        bool: True jeśli captcha została w pełni rozwiązana
    """
    
    # Sprawdź czy captcha jest już otwarta (widoczne przyciski)
    captcha_already_open = is_captcha_visible(driver)
    
    if captcha_already_open:
        print("ℹ️ Captcha już otwarta - pomijam 'Rozwiąż teraz'")
    else:
        # Krok 1: Spróbuj kliknąć "Rozwiąż teraz"
        clicked = click_solve_now(driver, timeout=2)
        
        if not clicked:
            # Sprawdź ponownie czy captcha się pojawiła
            if not is_captcha_visible(driver):
                # Nie ma captchy w ogóle
                return False
            else:
                print("ℹ️ Captcha widoczna bez 'Rozwiąż teraz'")
    
    # Krok 2: Zaznacz przyciski z gwiazdkami
    clicked = click_star_buttons(driver)
    
    if clicked == 0:
        print("⚠️ Nie zaznaczono żadnych przycisków")
        # Może być już rozwiązana, spróbuj potwierdzić
    
    # Krok 3: Kliknij "Potwierdzam"
    return click_confirm(driver)


def check_and_solve_captcha(driver):
    """
    Sprawdza czy captcha istnieje i rozwiązuje ją w pełni.
    Obsługuje dwa warianty:
    - Captcha z przyciskiem "Rozwiąż teraz"
    - Captcha od razu widoczna (po zalogowaniu)
    
    Returns:
        bool: True jeśli captcha była i została rozwiązana, False jeśli nie było captchy
    """
    try:
        # Sprawdź czy istnieje przycisk "Rozwiąż teraz" LUB captcha jest już widoczna
        has_solve_button = False
        has_captcha_buttons = False
        
        try:
            driver.find_element(By.XPATH, "//div[@class='label' and text()='Rozwiąż teraz']")
            has_solve_button = True
        except NoSuchElementException:
            pass
        
        try:
            driver.find_element(By.CSS_SELECTOR, ".captcha__buttons")
            has_captcha_buttons = True
        except NoSuchElementException:
            pass
        
        # Jeśli nie ma ani przycisku ani captchy - brak captchy
        if not has_solve_button and not has_captcha_buttons:
            return False
        
        # Jest captcha - rozwiąż ją
        print("\n" + "="*50)
        print("🔐 CAPTCHA WYKRYTA - rozpoczynam rozwiązywanie")
        if has_captcha_buttons and not has_solve_button:
            print("ℹ️ Typ: Captcha od razu widoczna (po logowaniu)")
        else:
            print("ℹ️ Typ: Captcha z przyciskiem 'Rozwiąż teraz'")
        print("="*50)
        
        success = solve_captcha_full(driver)
        
        if success:
            print("="*50)
            print("✅ CAPTCHA POMYŚLNIE ROZWIĄZANA")
            print("="*50 + "\n")
        else:
            print("="*50)
            print("❌ BŁĄD - nie udało się rozwiązać captchy")
            print("="*50 + "\n")
        
        return success
        
    except Exception as e:
        print(f"⚠️ Nieoczekiwany błąd przy captcha: {e}")
        return False
