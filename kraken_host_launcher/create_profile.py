import json
import shutil
from pathlib import Path


def create_profile(profile_name: str, template_name: str = None,
                   browser: str = "Chrome", group: str = "default") -> str:
    """
    Tworzy profil przeglądarki w:
      <projekt>/profiles/groups/<group>/<profile_name>/

    Jeśli podano template_name, kopiuje z:
      <projekt>/profiles/templates/<browser.lower()>/<template_name>/

    Jeśli template_name jest None, tworzy minimalną pustą strukturę profilu.

    Jeśli profil już istnieje → pomija tworzenie i zwraca jego ścieżkę.
    """
    base_dir = Path(__file__).parent
    target_path = base_dir / "profiles" / "groups" / group / profile_name

    if target_path.exists():
        return str(target_path)

    if template_name:
        template_path = base_dir / "profiles" / "templates" / browser.lower() / template_name
        if not template_path.exists() or not template_path.is_dir():
            raise FileNotFoundError(f"Brak szablonu: {template_path}")
        _RUNTIME_IGNORE = shutil.ignore_patterns(
            "SingletonSocket", "SingletonLock", "SingletonCookie",
            "RunningChromeVersion", "RunningBraveVersion",
            "lockfile", "*.lock", "*.ldb.lock",
            "Crashpad", "crash_reporter_*",
        )
        errors = []

        def _copy_fn(src, dst):
            try:
                shutil.copy2(src, dst)
            except OSError as exc:
                errors.append((src, dst, str(exc)))

        shutil.copytree(template_path, target_path,
                        ignore=_RUNTIME_IGNORE, copy_function=_copy_fn)
        if errors:
            raise RuntimeError(errors)
    else:
        default_dir = target_path / "Default"
        default_dir.mkdir(parents=True, exist_ok=True)
        (default_dir / "Preferences").write_text(json.dumps({}), encoding="utf-8")

    return str(target_path)
