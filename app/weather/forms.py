from pathlib import Path

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

DEFAULT_MAX_CSV_UPLOAD_SIZE = 2 * 1024 * 1024


class PrecipitationCsvUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Plik CSV",
        help_text=("Wymagane kolumny: date, snow, rain. Separator: średnik. Maksymalny rozmiar: 2 MB."),
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".csv,text/csv",
                "class": "file-input",
            }
        ),
    )

    def clean_csv_file(self) -> UploadedFile:
        uploaded_file: UploadedFile = self.cleaned_data["csv_file"]

        file_name = uploaded_file.name

        if not file_name:
            raise ValidationError(
                "Przesłany plik nie ma nazwy.",
                code="missing_file_name",
            )

        file_extension = Path(file_name).suffix.lower()

        if file_extension != ".csv":
            raise ValidationError(
                "Dozwolone są wyłącznie pliki z rozszerzeniem .csv.",
                code="invalid_extension",
            )

        max_size: int = getattr(
            settings,
            "WEATHER_MAX_CSV_UPLOAD_SIZE",
            DEFAULT_MAX_CSV_UPLOAD_SIZE,
        )

        file_size = uploaded_file.size

        if file_size is None:
            raise ValidationError(
                "Nie udało się określić rozmiaru pliku.",
                code="unknown_file_size",
            )

        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)

            raise ValidationError(
                f"Plik jest zbyt duży. Maksymalny rozmiar to {max_size_mb:g} MB.",
                code="file_too_large",
            )

        return uploaded_file
