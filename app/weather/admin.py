# Register your models here.
from common.utils import register_all_models

# Kolejność MA znaczenie, pola ID z modelów (wymagane przy imporcie excell)
IMPORT_ID_CANDIDATES = [
    "measurement_date",
    "snow",
    "rain",
    "created_at",
    "updated_at"

]

register_all_models(
    "weather",
    None,
    import_id_candidates = IMPORT_ID_CANDIDATES
)