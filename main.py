import random
from enum import Enum

# Statt direkter Item-Objekt-Definitionen:
# from items import ITEMS_DATA
from items import ITEMS_DATA


class MealType(Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"


class Item:
    """
    Arbeitet ausschließlich mit Nährwerten pro Portion (preferred).
    Felder:
      - calories_per_portion, fat_per_portion, carbs_per_portion,
        protein_per_portion, fibre_per_portion, salt_per_portion
      - meal_types: Menge von MealType
      - optional: standard_portion_name (z.B. "Plate", "Bowl")
    """

    def __init__(
        self,
        name: str,
        calories_per_portion: float,
        fat_per_portion: float | None,
        carbs_per_portion: float | None,
        protein_per_portion: float | None,
        fibre_per_portion: float | None,
        salt_per_portion: float | None,
        meal_types: set[MealType] = set(),
        standard_portion_name: str | None = None,
    ) -> None:
        self.name = name

        # required per-portion values (calories should be provided)
        self.calories_per_portion = round(float(calories_per_portion), 2)
        self.fat_per_portion = (
            round(float(fat_per_portion), 2) if fat_per_portion is not None else None
        )
        self.carbs_per_portion = (
            round(float(carbs_per_portion), 2)
            if carbs_per_portion is not None
            else None
        )
        self.protein_per_portion = (
            round(float(protein_per_portion), 2)
            if protein_per_portion is not None
            else None
        )
        self.fibre_per_portion = (
            round(float(fibre_per_portion), 2)
            if fibre_per_portion is not None
            else None
        )
        self.salt_per_portion = (
            round(float(salt_per_portion), 2) if salt_per_portion is not None else None
        )

        self.meal_types: set[MealType] = meal_types
        self.standard_portion_name: str | None = standard_portion_name

    def nutrients_for_portions(self, portions: float) -> dict[str, float]:
        """
        Liefert Nährwerte für die angegebene Anzahl Portionen.
        Fehlende Makros werden als 0.0 behandelt.
        """
        p = float(portions)
        return {
            "calories": round(self.calories_per_portion * p, 2),
            "fat": round((self.fat_per_portion or 0.0) * p, 2),
            "carbs": round((self.carbs_per_portion or 0.0) * p, 2),
            "protein": round((self.protein_per_portion or 0.0) * p, 2),
            "fibre": round((self.fibre_per_portion or 0.0) * p, 2),
            "salt": round((self.salt_per_portion or 0.0) * p, 2),
        }

    def step_portions(self) -> float:
        """
        Wie darf dieses Item erhöht werden? Standard: 1 Portion.
        """
        return 1.0


class Portion:
    """
    Repräsentiert eine Anzahl von Standard-Portionen eines Items.
    Arbeitet ausschließlich mit `standard_portions`.
    """

    def __init__(self, item: Item, standard_portions: float) -> None:
        self.item = item
        sp = float(standard_portions)
        if sp <= 0:
            raise ValueError("standard_portions must be > 0")
        self.portions = sp

    def nutrients(self) -> dict[str, float]:
        return self.item.nutrients_for_portions(self.portions)

    def __repr__(self) -> str:
        if self.item.standard_portion_name is not None:
            return f"Portion({self.item.name}, {self.portions:g} {self.item.standard_portion_name})"
        return f"Portion({self.item.name}, {self.portions:g} portions)"


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


def default_portions(item: Item) -> float:
    # Default: eine Portion
    return 1.0


def protein_per_calorie(item: Item) -> float:
    """
    Proteingehalt pro Kalorie, basierend auf per-portion Daten.
    """
    calories = item.calories_per_portion
    protein = item.protein_per_portion or 0.0

    if calories <= 0:
        return 0.0
    return protein / calories


def generate_day_plan(
    items: list[Item], goals: Goals, seed: int | None = None
) -> DayPlan:
    rng = random.Random(seed)
    plan = DayPlan()

    # Kalorien-Limit (nicht mehr als target + 100 kcal)
    cal_limit = goals.calories_target + 100.0

    # 1) Basis: je Mahlzeit 1 Item (Startportion)
    for mt in [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]:
        pool = items_for_meal(items, mt)
        it = rng.choice(pool)
        plan.add(mt, Portion(it, standard_portions=default_portions(it)))

    def add_best_item(mt: MealType, candidates: list[Item], cal_limit: float) -> bool:
        """
        Versucht, einen Schritt (step_portions) des besten Kandidaten zu mt hinzuzufügen,
        wobei darauf geachtet wird, das gegebene Kalorien-Limit nicht zu überschreiten.
        Bewertungs-Kriterium: zusätzliches Protein pro zusätzlicher Kalorie.
        Gibt True zurück, wenn etwas hinzugefügt wurde, sonst False.
        """
        current_cal = plan.nutrients().get("calories", 0.0)
        best = None
        best_score = -1.0

        for it in candidates:
            step = it.step_portions()
            added_cal = it.calories_per_portion * step
            if added_cal <= 0:
                continue
            # Prüfe, ob Hinzufügen das Kalorien-Limit überschreiten würde
            if current_cal + added_cal > cal_limit:
                continue
            added_protein = (it.protein_per_portion or 0.0) * step
            # Score: protein per added calorie
            s = added_protein / added_cal
            if s > best_score:
                best_score = s
                best = it

        if best is None:
            return False

        plan.add(mt, Portion(best, standard_portions=best.step_portions()))
        return True

    # 2) Protein-Repair (gezielt), respektiere cal_limit
    for _ in range(200):
        n = plan.nutrients()
        if n.get("protein", 0.0) >= goals.protein_min:
            break

        current_cal = n.get("calories", 0.0)
        # Wenn bereits über dem Limit, brechen wir ab (nicht weiter erhöhen)
        if current_cal > cal_limit:
            break

        added = False
        # Versuche für verschiedene Mahlzeiten, etwas hinzuzufügen
        for mt in [MealType.LUNCH, MealType.DINNER, MealType.BREAKFAST]:
            pool = items_for_meal(items, mt)
            # Kandidaten: Items mit "vernünftigem" Protein (per portion)
            pool = [it for it in pool if (it.protein_per_portion or 0.0) > 5]
            if not pool:
                continue
            if add_best_item(mt, pool, cal_limit):
                added = True
                break

        if not added:
            # Kein Kandidat passt mehr ins Kalorien-Limit oder keine geeigneten Items
            break

    # 3) Kalorien-Repair (auffüllen)
    for _ in range(80):
        n = plan.nutrients()
        cal = n.get("calories", 0.0)

        # Stoppen, wenn wir nahe genug am Ziel sind (±100)
        if abs(cal - goals.calories_target) <= 100:
            break
        if cal > goals.calories_target + 100:
            break  # zu hoch, wir reduzieren nicht in diesem MVP

        # Fülle bevorzugt mit Carb-lastigen Sachen (Reis/Haferflocken)
        # Heuristik: max carbs_per_portion bei moderatem Fett
        all_candidates = []
        for mt in [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER]:
            pool = items_for_meal(items, mt)
            all_candidates += [(mt, it) for it in pool]

        # pick best carb-heavy item
        best_mt, best_it = all_candidates[0]

        def carbs_per_portion_val(it: Item) -> float:
            return it.carbs_per_portion or 0.0

        def fat_per_portion_val(it: Item) -> float:
            return it.fat_per_portion or 0.0

        best_score = carbs_per_portion_val(best_it) - fat_per_portion_val(best_it) * 2.0

        for mt, it in all_candidates[1:]:
            s = carbs_per_portion_val(it) - fat_per_portion_val(it) * 2.0
            if s > best_score:
                best_score = s
                best_mt, best_it = mt, it

        # Nur hinzufügen, wenn wir das cal_limit nicht überschreiten
        added_cal = best_it.calories_per_portion * best_it.step_portions()
        if cal + added_cal <= cal_limit:
            plan.add(
                best_mt, Portion(best_it, standard_portions=best_it.step_portions())
            )
        else:
            # wenn das beste Item das Limit sprengt, versuchen wir eine andere Runde:
            # hier einfach abbrechen, um keine Überschreitung zu riskieren
            break

    return plan


def load_items_from_data(data) -> list[Item]:
    result: list[Item] = []
    for d in data:
        # meal_types als Menge von MealType-Enums erzeugen
        mts = {MealType[mt] for mt in d.get("meal_types", [])}

        item = Item(
            d["name"],
            # per-portion (required)
            d["calories_per_portion"],
            d.get("fat_per_portion"),
            d.get("carbs_per_portion"),
            d.get("protein_per_portion"),
            d.get("fibre_per_portion"),
            d.get("salt_per_portion"),
            mts,
            standard_portion_name=d.get("standard_portion_name"),
        )
        result.append(item)
    return result


items = load_items_from_data(ITEMS_DATA)

# Der Rest bleibt gleich: goals, plan, prints ...
goals = Goals(calories_target=2200, protein_min=150, fat_max=80)

plan = generate_day_plan(items, goals, seed=42)

print("Day nutrients:", plan.nutrients())
print("Score:", plan.score(goals))
for mt, meal in plan.meals.items():
    print(mt.value, meal.portions)
