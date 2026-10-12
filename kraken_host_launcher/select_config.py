import os

def select_config(config_file=None):
    """
    Wybiera plik konfiguracyjny.
    Jeśli config_file jest podany, używa go bezpośrednio.
    W przeciwnym razie wyświetla interaktywny prompt.
    """
    config_dir = "config"
    
    # Jeśli podano plik przez argument
    if config_file:
        config_path = os.path.join(config_dir, config_file)
        if os.path.exists(config_path) and config_file.endswith('.json'):
            print(f"✅ Użyto config z argumentu: {config_file}\n")
            return config_path
        else:
            print(f"❌ Plik {config_file} nie istnieje lub nie jest plikiem .json")
            exit(1)
    
    # Interaktywny wybór
    json_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
    json_files.sort()
    
    if not json_files:
        print("❌ Brak plików .json w katalogu config/")
        exit(1)
    
    print("\n" + "="*40)
    print("📋 SELECT CONFIG")
    print("="*40)
    
    for idx, filename in enumerate(json_files, start=1):
        print(f"[{idx}] {filename}")
    
    print("="*40)
    
    while True:
        try:
            choice = input("Wybierz numer pliku: ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(json_files):
                selected_file = json_files[choice_num - 1]
                config_path = os.path.join(config_dir, selected_file)
                print(f"✅ Wybrany config: {selected_file}\n")
                return config_path
            else:
                print(f"⚠️ Podaj numer od 1 do {len(json_files)}")
        except ValueError:
            print("⚠️ Podaj poprawny numer")
        except KeyboardInterrupt:
            print("\n❌ Przerwano")
            exit(0)