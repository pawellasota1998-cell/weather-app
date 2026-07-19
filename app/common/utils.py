from django.apps import apps
from django.contrib import admin
from django.db import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin


# ====== Uniwersalny Resource ======
class GenericResource(resources.ModelResource):  # klasa mapuje plik excell na model Django
    class Meta:
        report_skipped = True  # pokazuje w raporcie, które rekordy zostały pominięte
        skip_unchanged = True  # nie aktualizuje rekordów, jeśli nic się nie zmieniło
        use_bulk = True  # aktualizacja wszystkich obiektów w sql jednorazowo zamiast obiekt po obiekcie


# ====== Uniwersalny Admin ======
class GenericImportExportAdmin(ImportExportModelAdmin):
    import_id_candidates = None  # atrybut klasy, nadpisywany przez type()

    def __init__(self, model, admin_site):
        field_names = [f.name for f in model._meta.fields]

        # wybieramy pierwsze pasujące pole jako import_id
        import_id_field = None
        if self.import_id_candidates:
            import_id_field = next((f for f in self.import_id_candidates if f in field_names), None)

        meta_attrs = {"model": model}

        if import_id_field:
            meta_attrs["import_id_fields"] = [import_id_field]

        self.resource_class = type(
            f"{model.__name__}Resource", (GenericResource,), {"Meta": type("Meta", (), meta_attrs)}
        )

        super().__init__(model, admin_site)

    def get_list_display(self, request):
        return [field.name for field in self.model._meta.fields]

    def get_list_filter(self, request):
        filters = []

        for field in self.model._meta.fields:
            if isinstance(field, models.BooleanField):
                filters.append(field.name)

            elif isinstance(field, (models.DateField, models.DateTimeField)):
                filters.append(field.name)

            elif isinstance(field, models.ForeignKey):
                filters.append(field.name)

            elif field.choices:
                filters.append(field.name)

        return filters


# Funkcja do automatycznej rejestracji modeli z importem/exportem danych


def register_all_models(app_label: str, exclude_models=None, import_id_candidates=None):

    if exclude_models is None:
        exclude_models = []

    # ====== Automatyczna rejestracja ======
    for model in apps.get_app_config(app_label).get_models():
        if model._meta.abstract:
            continue

        if model in exclude_models:
            print(model)
            continue

        try:
            admin.site.register(
                model,
                type(  # Dynamiczne tworzenie klasy z dzidziczeniem po GenericImportExportAdmin
                    f"{model.__name__}Admin",
                    (GenericImportExportAdmin,),
                    {"import_id_candidates": import_id_candidates},  # atrybut klasy
                ),
            )
        except admin.sites.AlreadyRegistered:
            pass
