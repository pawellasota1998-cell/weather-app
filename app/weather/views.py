# Create your views here.
import logging

from django.contrib import messages
from django.db import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from weather.forms import PrecipitationCsvUploadForm
from weather.services.csv_importer import (
    PrecipitationCsvError,
    import_precipitation_csv,
)

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def upload_precipitation_csv(
    request: HttpRequest,
) -> HttpResponse:
    if request.method == "POST":
        form = PrecipitationCsvUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]

            try:
                result = import_precipitation_csv(csv_file)
            except PrecipitationCsvError as exc:
                form.add_error("csv_file", str(exc))
            except OSError:
                logger.exception("Nie udało się odczytać przesłanego pliku CSV.")
                form.add_error(
                    "csv_file",
                    "Nie udało się odczytać przesłanego pliku.",
                )
            except DatabaseError:
                logger.exception("Błąd bazy danych podczas importowania CSV.")
                form.add_error(
                    None,
                    ("Wystąpił błąd bazy danych. Dane nie zostały zaimportowane."),
                )
            else:
                messages.success(
                    request,
                    (
                        "Import zakończony pomyślnie. "
                        f"Utworzono: {result.created}, "
                        f"zaktualizowano: {result.updated}, "
                        f"bez zmian: {result.unchanged}."
                    ),
                )

                return redirect("weather:precipitation-upload")
    else:
        form = PrecipitationCsvUploadForm()

    return render(
        request,
        "weather/precipitation_upload.html",
        {
            "form": form,
        },
    )
