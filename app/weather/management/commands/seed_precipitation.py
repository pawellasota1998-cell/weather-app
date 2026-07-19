from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import DatabaseError

from weather.services.csv_importer import PrecipitationCsvError, import_precipitation_csv


class Command(BaseCommand):
    help = "Importuje pomiary opadów z pliku CSV. Istniejące pomiary są aktualizowane na podstawie daty."
    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "file_path",
            nargs="?", #argument opcjonalny
            type=Path,
            default=Path(settings.BASE_DIR) / "data" / "precipitation.csv",
            help=("Ścieżka do pliku CSV. Domyślnie: data/precipitation.csv"),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        file_path: Path = options["file_path"].expanduser() # rozwija symbol katalogu domowego ~ np. C:\Users\palasota
        if not file_path.is_absolute(): #sprawdzamy czy ścieżka jest absolutna
            file_path = Path.cwd() / file_path #Dodajemy absolutny katalog, Path.cwd() - miejsce uruchomienia komendy, to nie jkest to samo co  settings.BASE_DIR

        file_path = file_path.resolve() # normalizacja ścieżki, usuwane są fragmenty ., .., mamy ścieżkę absolutną

        if not file_path.exists():
            raise CommandError(
                f"Plik nie istnieje: {file_path}"
            )

        if not file_path.is_file():
            raise CommandError(
                f"Podana ścieżka nie wskazuje pliku: {file_path}"
            )

        try:
            with file_path.open("rb") as csv_file: # r - read, b - binary
                result = import_precipitation_csv(csv_file)
        except PrecipitationCsvError as exc:
            raise CommandError(f"Nie udało się zaimportować CSV: {exc}") from exc
        except OSError as exc:
            raise CommandError(f"Nie udało sie odczytać pliku {file_path}: {exc} ") from exc
        except DatabaseError as exc:
            raise CommandError(f"Błąd bazy danych podczas importowania CSV: {exc}") from exc

        #Wuświetlenie w konsoli podsumowania
        self.stdout.write(self.style.SUCCESS("Import zakończony pomyślnie."))

        self.stdout.write(f"Plik: {file_path}")
        self.stdout.write(f"Utworzono: {result.created}")
        self.stdout.write(f"Zaktualizowano: {result.updated}")
        self.stdout.write(f"Bez zmian: {result.unchanged}")
        self.stdout.write(f"Łącznie: {result.total}")
