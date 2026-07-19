from django.urls import path
from django.views.generic import RedirectView

from weather import views

app_name = "weather"

urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="weather:precipitation-list",
            permanent=False,
        ),
        name="home",
    ),
    path(
        "measurements/",
        views.PrecipitationMeasurementListView.as_view(),
        name="precipitation-list",
    ),
    path(
        "measurements/import/",
        views.upload_precipitation_csv,
        name="precipitation-upload",
    ),
]
