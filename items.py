# Reine Datenbeschreibung der Items. Keine Importe von main.py, damit
# es keine zirkulären Importe gibt.
ITEMS_DATA = [
    {
        "name": "Vanillejoghurt",
        "calories_per_100": 66,
        "fat_per_100": 2.1,
        "carbs_per_100": 7.5,
        "protein_per_100": 3.7,
        "fibre_per_100": 0.9,
        "salt_per_100": 0.2,
        "meal_types": ["BREAKFAST"],  # Enum-Namen aus main.MealType
        # optional:
        "standard_portion_size": None,
        "standard_portion_name": None,
    },
    {
        "name": "Haferflocken",
        "calories_per_100": 361,
        "fat_per_100": 6.7,
        "carbs_per_100": 56,
        "protein_per_100": 14,
        "fibre_per_100": 11,
        "salt_per_100": 0,
        "meal_types": ["BREAKFAST"],  # Enum-Namen aus main.MealType
        # optional:
        "standard_portion_size": None,
        "standard_portion_name": None,
    },
    {
        "name": "Reis",
        "calories_per_100": 360,
        "fat_per_100": 0.6,
        "carbs_per_100": 78,
        "protein_per_100": 7.5,
        "fibre_per_100": 1.3,
        "salt_per_100": 0.01,
        "meal_types": ["LUNCH", "DINNER"],
        "standard_portion_size": 125,
        "standard_portion_name": "Beutel",
    },
    {
        "name": "Toasty",
        "calories_per_100": 242,
        "fat_per_100": 9.9,
        "carbs_per_100": 21,
        "protein_per_100": 17,
        "fibre_per_100": 0,
        "salt_per_100": 1.7,
        "meal_types": ["LUNCH", "DINNER"],
        "standard_portion_size": 70,
        "standard_portion_name": "Scheibe",
    },
]
