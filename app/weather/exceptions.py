class PrecipitationCsvError(ValueError):
    """Błąd struktury lub zawartości pliku CSV."""


class NoPrecipitationMeasurementsError(LookupError):
    """Brak pomiarów potrzebnych do obliczenia statystyk."""
