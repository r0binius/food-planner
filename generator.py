import random

import main.py


def items_for_meal(items: list[Item], meal_type: MealType) -> list[Item]:
    return [i for i in items if meal_type in i.meal_types]


def default_grams(item: Item) -> float:
    if item.standard_portion_size is not None:
        return item.standard_portion_size
    return 100.0


def generate_day_plan(
    items: list[Item], goals: Goals, seed: int | None = None
) -> DayPlan:
    rng = random.Random(seed)
    plan = DayPlan()

    # 1) Basis-Füllung: je Mahlzeit 1 Item
    for mt in [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]:
        pool = items_for_meal(items, mt)
        if not pool:
            raise ValueError(f"No items available for {mt.value}")
        it = rng.choice(pool)
        plan.add(mt, Portion(it, grams=default_grams(it)))

    # 2) Repair: wenn Protein zu niedrig, addiere/erhöhe proteinreiche Items
    # (MVP: sehr simple Heuristik)
    for _ in range(30):  # 30 kleine Schritte
        n = plan.nutrients()
        if (
            n.get("protein", 0.0) >= goals.protein_min
            and abs(n.get("calories", 0.0) - goals.calories_target) <= 150
        ):
            break

        # Wähle Mahlzeit zufällig und erhöhe dort ein Item in 10g Schritten
        mt = rng.choice([MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER])
        meal = plan.meals[mt]

        # Falls keine Portionen: skip (sollte nicht passieren)
        if not meal.portions:
            continue

        # Erhöhe random Portion
        p = rng.choice(meal.portions)
        p.grams += 10.0  # einfache Schrittgröße

    return plan
