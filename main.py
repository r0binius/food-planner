#!/usr/bin/env python3
import random
from enum import Enum
from typing import List

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
      - optional: max_portions (float) — Maximale Anzahl Standard-Portionen pro Tag
      - optional runtime-only attribute: lunch_role ("MAIN" oder "SIDE")
        Wird beim Laden aus Daten gesetzt, wenn vorhanden. Falls nicht gesetzt,
        kann die Logik beim Erstellen des Mittagessens eine Rolle inferieren.
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
        max_portions: float | None = None,
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

        # optional: maximum standard portions allowed for this item (per day)
        if max_portions is not None:
            mp = float(max_portions)
            if mp <= 0:
                raise ValueError("max_portions must be > 0")
            self.max_portions: float | None = mp
        else:
            self.max_portions = None

        # lunch_role is optional runtime metadata: "MAIN", "SIDE", or None
        self.lunch_role: str | None = None

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

    def __repr__(self) -> str:
        return f"Item({self.name})"


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
        # Enforce item-level max_portions (per day) if set
        maxp = getattr(item, "max_portions", None)
        if maxp is not None and sp > maxp:
            raise ValueError(
                f"standard_portions ({sp}) exceeds item's max_portions ({maxp})"
            )
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

    def __repr__(self) -> str:
        return f"Meal({self.meal_type}, portions={self.portions})"


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
        # Enforce item-level max_portions across the whole DayPlan (per day)
        maxp = getattr(portion.item, "max_portions", None)
        if maxp is not None:
            current_total = 0.0
            for meal in self.meals.values():
                for p in meal.portions:
                    if p.item is portion.item:
                        current_total += p.portions
            if current_total + portion.portions > maxp:
                raise ValueError(
                    f"Cannot add {portion.portions} portions of {portion.item.name}: would exceed max_portions ({maxp})"
                )
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


def items_for_meal(items: List[Item], meal_type: MealType) -> List[Item]:
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


def pick_lunch_pair(rng: random.Random, pool: List[Item]) -> tuple[Item, Item]:
    """
    Wählt ein Lunch-Paar (main, side) aus dem Pool aus.

    Regeln:
      - Das Ergebnis muss genau ein MAIN und genau ein SIDE liefern.
      - Wenn explizite MAIN/SIDE Rollen vorhanden sind, wähle je eine davon.
      - Wenn nur eine Seite der Rollen vorhanden ist (z.B. nur MAIN), versuche
        eine passende Gegenrolle aus dem Pool zu wählen und markiere sie als
        notwendigerweise SIDE (oder MAIN), damit nicht zwei gleiche Rollen kombiniert werden.
      - Wenn keine Rollen gesetzt sind, wähle zwei unterschiedliche Items und
        inferiere MAIN/SIDE nach Kalorien (höhere Kalorien = MAIN).
      - Wenn nur ein Item verfügbar ist, verwende es doppelt (main==side).
    """
    mains = [i for i in pool if getattr(i, "lunch_role", None) == "MAIN"]
    sides = [i for i in pool if getattr(i, "lunch_role", None) == "SIDE"]

    # Case A: both explicit mains and sides -> pick one each
    if mains and sides:
        main = rng.choice(mains)
        side_candidates = [s for s in sides if s is not main]
        side = rng.choice(side_candidates) if side_candidates else rng.choice(sides)
        # ensure roles set
        main.lunch_role = main.lunch_role or "MAIN"
        side.lunch_role = side.lunch_role or "SIDE"
        return main, side

    # Case B: explicit mains only -> pick a main and pick a non-main as side if possible
    if mains and not sides:
        main = rng.choice(mains)
        non_main_candidates = [i for i in pool if i is not main]
        if non_main_candidates:
            side = rng.choice(non_main_candidates)
            # ensure roles are MAIN and SIDE (avoid combining two explicit MAINs)
            main.lunch_role = main.lunch_role or "MAIN"
            side.lunch_role = side.lunch_role or "SIDE"
            return main, side
        # If every candidate is also marked MAIN but there are at least two items, force one to SIDE
        if len(mains) >= 2:
            # pick a different mains item to act as side
            other = rng.choice([m for m in mains if m is not main])
            main.lunch_role = main.lunch_role or "MAIN"
            other.lunch_role = "SIDE"
            return main, other

    # Case C: explicit sides only -> symmetric handling
    if sides and not mains:
        side = rng.choice(sides)
        non_side_candidates = [i for i in pool if i is not side]
        if non_side_candidates:
            main = rng.choice(non_side_candidates)
            main.lunch_role = main.lunch_role or "MAIN"
            side.lunch_role = side.lunch_role or "SIDE"
            return main, side
        if len(sides) >= 2:
            other = rng.choice([s for s in sides if s is not side])
            other.lunch_role = "MAIN"
            side.lunch_role = side.lunch_role or "SIDE"
            return other, side

    # Case D: no explicit roles -> choose two distinct items if possible
    unique_pool = list(dict.fromkeys(pool))  # preserve order but unique
    if len(unique_pool) >= 2:
        a, b = rng.sample(unique_pool, 2)
        # infer roles by calories (higher = MAIN)
        if a.calories_per_portion >= b.calories_per_portion:
            a.lunch_role = a.lunch_role or "MAIN"
            b.lunch_role = b.lunch_role or "SIDE"
            return a, b
        else:
            a.lunch_role = a.lunch_role or "SIDE"
            b.lunch_role = b.lunch_role or "MAIN"
            return b, a

    # Case E: only one item available -> use it for both roles (two portions)
    if len(unique_pool) == 1:
        single = unique_pool[0]
        # mark as MAIN by default (and can be SIDE as well)
        single.lunch_role = single.lunch_role or "MAIN"
        return single, single

    raise ValueError("No lunch candidates available")


def generate_day_plan(
    items: List[Item], goals: Goals, seed: int | None = None
) -> DayPlan:
    rng = random.Random(seed)
    plan = DayPlan()

    # Kalorien-Limit (nicht mehr als target + 100 kcal)
    cal_limit = goals.calories_target + 100.0

    # 1) Basis: je Mahlzeit Startportionen
    # Breakfast and dinner: jeweils ein Gericht
    for mt in [MealType.BREAKFAST, MealType.DINNER]:
        pool = items_for_meal(items, mt)
        if not pool:
            raise ValueError(f"No items for meal type {mt}")
        it = rng.choice(pool)
        plan.add(mt, Portion(it, standard_portions=default_portions(it)))

    # Lunch: Baue aus MAIN + SIDE
    lunch_pool = items_for_meal(items, MealType.LUNCH)
    if not lunch_pool:
        raise ValueError("No items for lunch available")
    main_item, side_item = pick_lunch_pair(rng, lunch_pool)

    # Wenn main==side (nur ein Item im Pool), fügen wir zwei Portionen derselben Item hinzu.
    plan.add(
        MealType.LUNCH,
        Portion(main_item, standard_portions=default_portions(main_item)),
    )
    plan.add(
        MealType.LUNCH,
        Portion(side_item, standard_portions=default_portions(side_item)),
    )

    def add_best_item(mt: MealType, candidates: List[Item], cal_limit: float) -> bool:
        """
        Versucht, einen Schritt (step_portions) des besten Kandidaten zu mt hinzuzufügen,
        wobei darauf geachtet wird, das gegebene Kalorien-Limit nicht zu überschreiten
        und item.max_portions zu respektieren.
        Bewertungs-Kriterium: zusätzliches Protein pro zusätzlicher Kalorie.
        Gibt True zurück, wenn etwas hinzugefügt wurde, sonst False.
        """
        current_cal = plan.nutrients().get("calories", 0.0)
        best = None
        best_score = -1.0

        for it in candidates:
            step = it.step_portions()
            # respect item-level max_portions against current plan
            maxp = getattr(it, "max_portions", None)
            if maxp is not None:
                current_item_total = 0.0
                for meal in plan.meals.values():
                    for p in meal.portions:
                        if p.item is it:
                            current_item_total += p.portions
                if current_item_total + step > maxp:
                    # would exceed the allowed maximum for this item; skip
                    continue

            added_cal = it.calories_per_portion * step
            if added_cal <= 0:
                continue
            # Prüfe, ob Hinzufügen das Kalorien-Limit überschreiten würde
            if current_cal + added_cal > cal_limit:
                continue
            added_protein = (it.protein_per_portion or 0.0) * step
            # Score: protein per added calorie
            s = added_protein / added_cal if added_cal > 0 else 0.0
            if s > best_score:
                best_score = s
                best = it

        if best is None:
            return False

        plan.add(mt, Portion(best, standard_portions=best.step_portions()))
        return True

    # 2) Protein-Repair (gezielt), respektiere cal_limit
    # Hinweis: Ursprünglich war Lunch unverändert, aber in dieser Variante erlauben
    # Reparatur-Schritte auch zusätzliche Lunch-Portionen. Daher betrachten wir Breakfast, Lunch und Dinner.
    for _ in range(200):
        n = plan.nutrients()
        if n.get("protein", 0.0) >= goals.protein_min:
            break

        current_cal = n.get("calories", 0.0)
        # Wenn bereits über dem Limit, brechen wir ab (nicht weiter erhöhen)
        if current_cal > cal_limit:
            break

        added = False
        # Versuche für verschiedene Mahlzeiten, etwas hinzuzufügen.
        # Wenn wir Lunch betrachten, dürfen wir nur zusätzliche Portionen von Items
        # hinzufügen, die bereits in der Lunch-Mahlzeit vorhanden sind (keine neuen Lunch-Items).
        for mt in [MealType.DINNER, MealType.BREAKFAST, MealType.LUNCH]:
            pool = items_for_meal(items, mt)
            # Wenn Lunch: nur bereits vorhandene Lunch-Items erlauben
            if mt is MealType.LUNCH:
                existing = [p.item for p in plan.meals[MealType.LUNCH].portions]
                pool = [it for it in pool if it in existing]
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
        all_candidates: list[tuple[MealType, Item]] = []
        # Fülle Breakfast, Dinner und Lunch — Lunch kann hier ebenfalls ergänzt werden,
        # jedoch nur durch bereits vorhandene Lunch-Items (keine neuen Lunch-Items).
        for mt in [MealType.BREAKFAST, MealType.DINNER, MealType.LUNCH]:
            pool = items_for_meal(items, mt)
            # Wenn Lunch: nur bereits vorhandene Lunch-Items erlauben
            if mt is MealType.LUNCH:
                existing = [p.item for p in plan.meals[MealType.LUNCH].portions]
                pool = [it for it in pool if it in existing]
            for it in pool:
                # Prüfe, ob das Item durch einen Schritt das max_portions Limit verletzen würde
                step = it.step_portions()
                maxp = getattr(it, "max_portions", None)
                current_item_total = 0.0
                for meal in plan.meals.values():
                    for p in meal.portions:
                        if p.item is it:
                            current_item_total += p.portions
                if maxp is not None and current_item_total + step > maxp:
                    continue  # überspringe dieses Item
                all_candidates.append((mt, it))

        if not all_candidates:
            break

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

        # Nur hinzufügen, wenn wir das cal_limit nicht überschreiten und nicht max_portions verletzen
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


def load_items_from_data(data) -> List[Item]:
    result: List[Item] = []
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
            max_portions=d.get("max_portions"),
        )

        # Optional: lade explizite Lunch-Rolle (wenn in ITEMS_DATA vorhanden).
        # Erwarteter Wert: "MAIN" oder "SIDE" (case-insensitive).
        lr = d.get("lunch_role")
        if lr:
            lr_up = str(lr).upper()
            if lr_up in ("MAIN", "SIDE"):
                item.lunch_role = lr_up

        result.append(item)
    return result


# Lade Items
items = load_items_from_data(ITEMS_DATA)

# Beispiel Goals und Ausführung
goals = Goals(calories_target=2100, protein_min=160, fat_max=80)

plan = generate_day_plan(items, goals, seed=42)

print("Day nutrients:", plan.nutrients())
print("Score:", plan.score(goals))
for mt, meal in plan.meals.items():
    # Aggregierte Nährwerte pro Mahlzeit zusätzlich ausgeben
    mn = meal.nutrients()
    print(f"{mt.value.capitalize()}:")
    print("  portions:", meal.portions)
    print("  nutrients:")
    for k, v in mn.items():
        print(f"    {k}: {v}")
