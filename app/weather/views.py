import logging
from typing import Any

from django.contrib import messages
from django.db import DatabaseError
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import ListView

from weather.forms import PrecipitationCsvUploadForm
from weather.models import PrecipitationMeasurement
from weather.services.csv_importer import (
    PrecipitationCsvError,
    import_precipitation_csv,
)
from weather.services.precipitation_statistics import (
    NoPrecipitationMeasurementsError,
    get_latest_month_statistics,
)

logger = logging.getLogger(__name__)


class PrecipitationMeasurementListView(ListView):
    model = PrecipitationMeasurement
    template_name = "weather/precipitation_list.html"
    context_object_name = "measurements"
    paginate_by = 20

    def get_queryset(
        self,
    ) -> QuerySet[PrecipitationMeasurement]:
        return PrecipitationMeasurement.objects.only(
            "measurement_date",
            "snow",
            "rain",
        ).order_by("measurement_date")

    def get_context_data(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        paginator = context["paginator"]
        page_obj = context["page_obj"]

        context["total_measurements"] = paginator.count
        context["pagination_range"] = paginator.get_elided_page_range(
            page_obj.number,
            on_each_side=2,
            on_ends=1,
        )

        return context


@require_GET
def latest_month_statistics(
    request: HttpRequest,
) -> JsonResponse:
    try:
        statistics = get_latest_month_statistics()
    except NoPrecipitationMeasurementsError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "NO_MEASUREMENTS",
                    "message": str(exc),
                }
            },
            status=404,
        )
    except DatabaseError:
        logger.exception("Błąd bazy danych podczas obliczania statystyk.")

        return JsonResponse(
            {
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": ("Nie udało się pobrać statystyk. Spróbuj ponownie."),
                }
            },
            status=500,
        )

    return JsonResponse(
        {
            "period": {
                "year": statistics.year,
                "month": statistics.month,
            },
            "measurement_count": statistics.measurement_count,
            "averages": {
                "snow": format(
                    statistics.average_snow,
                    ".2f",
                ),
                "rain": format(
                    statistics.average_rain,
                    ".2f",
                ),
                "total": format(
                    statistics.average_total,
                    ".2f",
                ),
            },
        }
    )


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

                return redirect("weather:precipitation-list")
    else:
        form = PrecipitationCsvUploadForm()

    return render(
        request,
        "weather/precipitation_upload.html",
        {
            "form": form,
        },
    )
