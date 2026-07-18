# Create your models here.
from django.db import models
from django.db.models import Q

class PrecipitationMeasurement( models.Model):
    measurement_date = models.DateField(
        verbose_name = "Data pomiaru",
        unique =True
    )
    snow = models.DecimalField(
        verbose_name="Opad śniegu",
        max_digits=6,
        decimal_places=2
    )
    rain = models.DecimalField(
        verbose_name="opad deszczu",
        max_digits=6,
        decimal_places=2
    )
    created_at  = models.DateTimeField(
        verbose_name="Utworzono",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name="Zaktualizowano",
        auto_now=True
    )
    class Meta:
        ordering = ["measurement_date"]
        db_table = "weather_precipitation_measurement"
        get_latest_by = "measurement_date"
        verbose_name = "Pomiar opadów"
        verbose_name_plural = "Pomiary opadów"
        constraints = [
            models.CheckConstraint(
                condition=Q(snow__gte = 0),
                name = "weather_snow_gte_0"
            ),
            models.CheckConstraint(
                condition=Q(rain__gte = 0),
                name = "weather_rain_gte_0"
            )
        ]
    def __str__(self) ->str:
        return (
            f"{self.measurement_date}: "
            f"snow = {self.snow}, rain = {self.rain}"
        )

        
