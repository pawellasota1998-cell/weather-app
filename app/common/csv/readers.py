from typing import IO

from common.csv.exceptions import CsvReadError


def read_text_file(file_obj: IO[bytes] | IO[str]) -> str:
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass

    content = file_obj.read()

    if isinstance(content, str):
        text = content.lstrip("\ufeff")  # Usuwamy z początku tekstu znak \ufeff w celu popranwego odczytania typu
    elif isinstance(content, bytes):
        try:
            text = content.decode("utf-8-sig")  # Zamieniamy dane na tekst,  utf-8-sig usuwa opcjonalny znacznik BOM.
        except UnicodeDecodeError as exc:
            raise CsvReadError("Plik musi być zapisany w kodowaniu UTF-8") from exc
    else:
        raise CsvReadError("Nie udało się odczytać zawartości pliku CSV")
    if not text.strip():
        raise CsvReadError("Plik CSV jest pusty")
    return text
