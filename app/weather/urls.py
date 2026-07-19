from django.urls import path

from weather import views

app_name = "weather"

urlpatterns = [
    path(
        "measurements/import/",
        views.upload_precipitation_csv,
        name="precipitation-upload",
    ),
]
