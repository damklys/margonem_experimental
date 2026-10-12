from __future__ import annotations

from typing import Optional, Union

from actions.find_object import FoundObject


def kill_object_action(
    driver,
    targets: Optional[Union[list[FoundObject], FoundObject]] = None,
    char_level: Optional[int] = None,
) -> Optional[FoundObject]:
    """
    Zabija pierwszy dostępny obiekt z listy targets.

    Argumenty:
        driver      — Selenium WebDriver
        targets     — wynik find_object: lista lub pojedynczy FoundObject
        char_level  — poziom postaci do sprawdzenia zakresu (opcjonalne)

    Zwraca zaatakowany FoundObject jeśli sukces, None jeśli brak celu lub niepowodzenie.
    """
    from kill_object import kill_object

    if targets is None:
        return None

    if isinstance(targets, FoundObject):
        targets = [targets]

    if not targets:
        return None

    target = targets[0]
    result = kill_object(driver, target.tip_id, char_level=char_level)

    if result in (False, "IGNORED", None):
        return None

    return target
