# Weather

Aplikacja rekrutacyjna napisana w Django, umożliwiająca importowanie dziennych danych o opadach atmosferycznych z pliku CSV do bazy Microsoft SQL Server.

Aplikacja wyświetla pomiary w paginowanej tabeli oraz pobiera bez przeładowania strony statystyki średnich opadów dla ostatniego miesiąca dostępnego w bazie.

## Funkcjonalności

- import pliku CSV przez interfejs internetowy,
- import danych przy użyciu komendy seedującej,
- walidacja struktury i zawartości CSV,
- aktualizacja istniejących pomiarów na podstawie daty,
- idempotentny import danych,
- zapis danych w Microsoft SQL Server,
- paginowana tabela pomiarów,
- obliczanie statystyk dla ostatniego miesiąca danych,
- modal pobierający statystyki przez `fetch()` bez przeładowania strony,
- panel administracyjny Django,
- automatyczna rejestracja modeli w panelu administracyjnym oraz eksportowanie/importowanie danych do modeli

## Technologie

### Backend

- Python 3.12
- Django 5.2
- mssql-django
- pyodbc
- python-dotenv

### Baza danych

- Microsoft SQL Server 2022
- Docker Compose
- Microsoft ODBC Driver 18 for SQL Server

### Frontend

- Django Templates
- HTML
- CSS
- JavaScript
- Fetch API
- natywny element HTML `dialog`

### Narzędzia

- Git
- Ruff
- Black

## Format pliku CSV

Wymagane nagłówki:

```csv
date;snow;rain
```

Przykład:

```csv
date;snow;rain
2022-12-01;4.5;2.3
2022-12-02;0.0;6.1
```

Wymagania:

- kodowanie UTF-8,
- separator `;`,
- data w formacie `YYYY-MM-DD`,
- wymagane kolumny `date`, `snow`, `rain`,
- wartości opadów nie mogą być ujemne,
- jedna data może wystąpić w pliku tylko raz,
- maksymalny rozmiar pliku przesyłanego przez formularz wynosi 2 MB.

Importer akceptuje zarówno kropkę, jak i przecinek jako separator dziesiętny.

## Zachowanie importu

Data pomiaru jest kluczem biznesowym importu.

Dla każdego wiersza importer:

- tworzy rekord, jeśli dana data jeszcze nie istnieje,
- aktualizuje rekord, jeśli data istnieje, ale wartości się zmieniły,
- pozostawia rekord bez zmian, jeśli data i wartości są identyczne.

Ponowne zaimportowanie identycznego pliku nie tworzy duplikatów.

## Wymagania lokalne

Przed uruchomieniem projektu należy zainstalować:

- Python 3.12,
- Docker Desktop,
- Git,
- Microsoft ODBC Driver 18 for SQL Server w wersji x64.

Sterownik dostępny dla Pythona można sprawdzić poleceniem:

```powershell
python -c "import pyodbc; print(pyodbc.drivers())"
```

Na liście powinien znajdować się:

```text
ODBC Driver 18 for SQL Server
```

## Instalacja

### 1. Sklonowanie repozytorium

```powershell
git clone <adres-repozytorium>
cd weather-app
```

### 2. Utworzenie środowiska wirtualnego

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalacja zależności

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Utworzenie konfiguracji lokalnej

```powershell
Copy-Item .env.example .env
```

Następnie należy uzupełnić silne hasła w pliku `.env`.

Przykładowa konfiguracja:

```dotenv
DJANGO_SECRET_KEY=secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

MSSQL_SA_PASSWORD=sa-password
MSSQL_PORT=14333

DB_HOST=localhost
DB_PORT=14333
DB_NAME=weather
DB_USER=weather_app
DB_PASSWORD=app-password

```

Pliku `.env` nie należy dodawać do repozytorium.

### 5. Uruchomienie SQL Servera

```powershell
docker compose up -d
```

Sprawdzenie kontenerów:

```powershell
docker compose ps -a
```

Oczekiwany stan:

```text
db        Up (healthy)
db-init   Exited (0)
```

`db-init` jest kontenerem jednorazowym. Status `Exited (0)` oznacza poprawne utworzenie bazy oraz użytkowników.

Logi inicjalizacji:

```powershell
docker compose logs db-init
```

Ponowne wykonanie skryptu inicjalizacyjnego:

```powershell
docker compose run --rm db-init
```

### 6. Wykonanie migracji

```powershell
python manage.py migrate
```

### 7. Zaimportowanie danych początkowych

```powershell
python manage.py seed_precipitation
```

Domyślnie komenda wykorzystuje:

```text
data/precipitation.csv
```

Można też podać inną ścieżkę:

```powershell
python manage.py seed_precipitation .\data\precipitation.csv
```

### 8. Uruchomienie aplikacji

```powershell
python manage.py runserver
```

Aplikacja będzie dostępna pod adresem:

```text
http://127.0.0.1:8000/
```

## Dostępne widoki

| Adres                                    | Opis                              |
| ---------------------------------------- | --------------------------------- |
| `/`                                      | Przekierowanie do tabeli pomiarów |
| `/measurements/`                         | Paginowana tabela pomiarów        |
| `/measurements/import/`                  | Formularz importu CSV             |
| `/measurements/statistics/latest-month/` | Endpoint JSON ze statystykami     |
| `/admin/`                                | Panel administracyjny Django      |

## Statystyki ostatniego miesiąca

Aplikacja nie ma grudnia wpisanego na stałe.

Mechanizm:

1. znajduje najnowszą datę pomiaru,
2. ustala jej miesiąc i rok,
3. pobiera pomiary z tego miesiąca,
4. oblicza średnią wartość śniegu,
5. oblicza średnią wartość deszczu,
6. oblicza średni łączny opad.

Dla dołączonego pliku ostatnim miesiącem jest grudzień 2022.

Oczekiwane wartości:

```text
Liczba pomiarów: 31
Średni opad śniegu: 4,45
Średni opad deszczu: 4,30
Średni łączny opad: 8,75
```

## Endpoint statystyk

Żądanie:

```http
GET /measurements/statistics/latest-month/
Accept: application/json
```

Przykładowa odpowiedź:

```json
{
  "period": {
    "year": 2022,
    "month": 12
  },
  "measurement_count": 31,
  "averages": {
    "snow": "4.45",
    "rain": "4.30",
    "total": "8.75"
  }
}
```

Wartości dziesiętne są zwracane jako tekst, aby zachować kontrolę nad precyzją i liczbą miejsc po przecinku.

## Kontrola jakości kodu

Sprawdzenie Ruff:

```powershell
python -m ruff check .
```

Automatyczne poprawienie:

```powershell
python -m ruff check . --fix
```

Sprawdzenie formatowania:

```powershell
python -m ruff format . --check
```

Formatowanie kodu:

```powershell
python -m ruff format .
```

Sprawdzenie typów

```powershell
python -m mypy .
```

Kontrola Django:

```powershell
python manage.py check
```

Sprawdzenie, czy modele nie wymagają nowych migracji:

```powershell
python manage.py makemigrations --check
```

## Reset lokalnej bazy

Zatrzymanie kontenerów bez usuwania danych:

```powershell
docker compose down
```

Usunięcie kontenerów razem z wolumenem bazy:

```powershell
docker compose down --volumes
```

Następnie środowisko można odtworzyć:

```powershell
docker compose up -d
python manage.py migrate
python manage.py seed_precipitation
```

Polecenie `docker compose down --volumes` usuwa wszystkie lokalne dane SQL Servera należące do projektu.

## Najważniejsze decyzje projektowe

### Wspólny serwis importujący

Formularz internetowy i seeder korzystają z tej samej funkcji `import_precipitation_csv()`. Zapobiega to powielaniu logiki walidacji oraz zapisu danych.

### Walidacja przed zapisem

Cały plik jest parsowany i walidowany przed rozpoczęciem zapisywania rekordów.

### Transakcja bazodanowa

Operacja zapisu jest wykonywana w `transaction.atomic()`. Błąd zapisu powoduje wycofanie całej operacji.

### Integralność w bazie

Unikalność dat oraz nieujemne wartości opadów są wymuszane również przez ograniczenia SQL Servera, a nie tylko przez kod Pythona.

### Brak przeładowania strony

Modal pobiera statystyki za pomocą `fetch()`. Otwarcie modala nie powoduje przejścia na inną stronę ani ponownego renderowania tabeli.

### Rozdzielenie odpowiedzialności

- `models.py` – struktura danych,
- `forms.py` – walidacja przesłanego pliku,
- `csv_importer.py` – parsowanie i zapis CSV,
- `precipitation_statistics.py` – obliczanie statystyk,
- `views.py` – obsługa żądań HTTP,
- `seed_precipitation.py` – interfejs komendy seedującej.

## Bezpieczeństwo

Projekt jest skonfigurowany do lokalnego środowiska deweloperskiego.

Przed wdrożeniem produkcyjnym należy między innymi:

- ustawić `DJANGO_DEBUG=False`,
- skonfigurować poprawne `ALLOWED_HOSTS`,
- użyć silnego, unikalnego `SECRET_KEY`,
- nie używać konta `sa` przez aplikację,
- zastosować poprawny certyfikat TLS dla SQL Servera,
- nie używać `TrustServerCertificate=yes`,
- uruchomić Django przez produkcyjny serwer WSGI lub ASGI,
- skonfigurować HTTPS,
- skonfigurować obsługę plików statycznych,
- ograniczyć uprawnienia użytkowników bazy danych.
