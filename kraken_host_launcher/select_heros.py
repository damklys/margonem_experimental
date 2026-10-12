def load_heros_route(heros_json_path):
    """
    Wczytuje route herosa z pliku JSON.
    Zwraca słownik z kluczami: route, route_index
    """
    import json
    
    with open(heros_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    route = data.get("route", [])
    
    if not route:
        print(f"❌ Plik {heros_json_path} nie zawiera route")
        exit(1)
    
    print(f"📋 Załadowano route: {len(route)} lokacji")
    
    return {
        "route": route,
        "route_index": 0,
        "heros_json_path": heros_json_path
    }