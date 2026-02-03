import random
from enum import Enum


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class Item:
    def __init__(
        self,
        name: str,
        calories_per_100: float,
        fat_per_100: float,
        carbs_per_100: float,
        protein_per_100: float,
        fibre_per_100: float,
        salt_per_100: float,
        meal_types: set[MealType],
        standard_portion_size: float | None = None,
        standard_portion_name: str | None = None,
    ) -> None:

        self.name: str = name

        self.calories_per_100: float = round(float(calories_per_100), 2)
        self.fat_per_100: float = round(float(fat_per_100), 2)
        self.carbs_per_100: float = round(float(carbs_per_100), 2)
        self.protein_per_100: float = round(float(protein_per_100), 2)
        self.fibre_per_100: float = round(float(fibre_per_100), 2)
        self.salt_per_100: float = round(float(salt_per_100), 2)

        self.meal_types: set[MealType] = meal_types

        self.standard_portion_size: float | None = (
            round(float(standard_portion_size), 2)
            if standard_portion_size is not None
            else None
        )
        self.standard_portion_name: str | None = standard_portion_name

    def nutrients_for(self, grams: float) -> dict[str, float]:
        factor = grams / 100.0

        return {
            "calories": round(self.calories_per_100 * factor, 2),
            "fat": round(self.fat_per_100 * factor, 2),
            "carbs": round(self.carbs_per_100 * factor, 2),
            "protein": round(self.protein_per_100 * factor, 2),
            "fibre": round(self.fibre_per_100 * factor, 2),
            "salt": round(self.salt_per_100 * factor, 2),
        }

    def nutrients_for_standard_portion(self) -> dict[str, float] | None:
        if self.standard_portion_size is None:
            return None
        return self.nutrients_for(self.standard_portion_size)


class Portion:
    def __init__(
        self,
        item: Item,
        grams: float | None = None,
        standard_portions: float | None = None,
    ) -> None:
        self.item = item

        if grams is None and standard_portions is None:
            raise ValueError("Provide either grams or standard_portions")

        if grams is not None and standard_portions is not None:
            raise ValueError("Provide only one of grams or standard_portions")

        if standard_portions is not None:
            if item.standard_portion_size is None:
                raise ValueError(f"{item.name} has no standard portion size")
            sp = float(standard_portions)
            if sp <= 0:
                raise ValueError("standard_portions must be > 0")
            self.grams = sp * item.standard_portion_size
        else:
            if grams is None:
                raise ValueError("Provide either grams or standard_portions")
            g = float(grams)
            if g <= 0:
                raise ValueError("grams must be > 0")
            self.grams = g

    def nutrients(self) -> dict[str, float]:
        return self.item.nutrients_for(self.grams)

    def __repr__(self) -> str:
        # Schön für Debug-Ausgaben
        if (
            self.item.standard_portion_size
            and abs(self.grams % self.item.standard_portion_size) < 1e-9
        ):
            count = self.grams / self.item.standard_portion_size
            unit = self.item.standard_portion_name or "portion"
            return f"Portion({self.item.name}, {count:g} {unit} = {self.grams:g}g)"
        return f"Portion({self.item.name}, {self.grams:g}g)"


def add_nutrients(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    keys = set(a) | set(b)
    return {k: round(a.get(k, 0.0) + b.get(k, 0.0), 2) for k in keys}


class Meal:
    def __init__(self, meal_type: MealType) -> None:
        self.meal_type = meal_type
        self.portions: list[Portion] = []

    def add(self, portion: Portion) -> None:
        if self.meal_type not in portion.item.meal_types:
            raise ValueError(
                f"{portion.item.name} is not allowed for {self.meal_type.value}"
            )
        self.portions.append(portion)

    def nutrients(self) -> dict[str, float]:
        total: dict[str, float] = {}
        for p in self.portions:
            total = add_nutrients(total, p.nutrients())
        return total


class Goals:
    def __init__(
        self,
        calories_target: float,
        protein_min: float,
        fat_max: float | None = None,
        carbs_min: float | None = None,
    ) -> None:
        self.calories_target = float(calories_target)
        self.protein_min = float(protein_min)
        self.fat_max = float(fat_max) if fat_max is not None else None
        self.carbs_min = float(carbs_min) if carbs_min is not None else None


class DayPlan:
    def __init__(self) -> None:
        self.meals: dict[MealType, Meal] = {
            MealType.BREAKFAST: Meal(MealType.BREAKFAST),
            MealType.LUNCH: Meal(MealType.LUNCH),
            MealType.DINNER: Meal(MealType.DINNER),
        }

    def add(self, meal_type: MealType, portion: Portion) -> None:
        self.meals[meal_type].add(portion)

    def nutrients(self) -> dict[str, float]:
        total: dict[str, float] = {}
        for meal in self.meals.values():
            total = add_nutrients(total, meal.nutrients())
        return total

    def score(self, goals: Goals) -> float:
        """
        Kleiner Score: 0 ist perfekt, größer ist schlechter.
        (Einfaches "Abweichung minimieren" – später kannst du das tunen.)
        """
        n = self.nutrients()

        cal = n.get("calories", 0.0)
        protein = n.get("protein", 0.0)
        fat = n.get("fat", 0.0)
        carbs = n.get("carbs", 0.0)

        # Strafpunkte: Calories-Abweichung (absolut)
        score = abs(goals.calories_target - cal)

        # Strafpunkte: Protein unterschritten (quadratisch = härter)
        if protein < goals.protein_min:
            score += (goals.protein_min - protein) ** 2 * 3.0

        # Optional: Fett zu hoch
        if goals.fat_max is not None and fat > goals.fat_max:
            score += (fat - goals.fat_max) ** 2 * 2.0

        # Optional: Carbs zu niedrig
        if goals.carbs_min is not None and carbs < goals.carbs_min:
            score += (goals.carbs_min - carbs) ** 2 * 1.5

        return round(score, 2)


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


peanut_butter = Item(
    "Erdnussbutter", 606, 47.9, 15.0, 24.6, 8.4, 0.83, {MealType.BREAKFAST}
)
rice = Item(
    "Reis",
    360,
    0.6,
    78,
    7.5,
    1.3,
    0.01,
    {MealType.LUNCH, MealType.DINNER},
    standard_portion_size=125,
    standard_portion_name="Beutel",
)

skyr = Item(
    "Skyr",
    63,
    0.2,
    3.9,
    11.0,
    0.0,
    0.1,
    {MealType.BREAKFAST},
    standard_portion_size=250,
    standard_portion_name="Becher",
)

chicken = Item(
    "Hähnchenbrust",
    110,
    1.5,
    0.0,
    23.0,
    0.0,
    0.2,
    {MealType.LUNCH, MealType.DINNER},
)

items = [peanut_butter, rice, skyr, chicken]

goals = Goals(calories_target=2200, protein_min=150, fat_max=80)

plan = generate_day_plan(items, goals, seed=42)

print("Day nutrients:", plan.nutrients())
print("Score:", plan.score(goals))
for mt, meal in plan.meals.items():
    print(mt.value, meal.portions)
