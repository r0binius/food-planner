from dataclasses import dataclass
from typing import Literal, Optional

Sex = Literal["male", "female"]
Goal = Literal["cut", "maintain", "bulk"]

ACTIVITY_FACTORS = {
    "sedentary": 1.2,  # kaum Bewegung
    "light": 1.375,  # leicht aktiv
    "moderate": 1.55,  # moderat aktiv (3-5x Training/Woche)
    "very_active": 1.725,  # sehr aktiv
    "extreme": 1.9,  # extrem aktiv
}


@dataclass(frozen=True)
class MacroTargets:
    bmr_kcal: int
    tdee_kcal: int
    target_kcal: int

    protein_g: int
    fat_g: int
    carbs_g: int

    protein_kcal: int
    fat_kcal: int
    carbs_kcal: int


def mifflin_st_jeor_bmr(
    *, weight_kg: float, height_cm: float, age_years: int, sex: Sex
) -> float:
    """Basal Metabolic Rate (BMR) nach Mifflin-St Jeor."""
    if sex == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age_years + 5
    elif sex == "female":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age_years - 161
    else:
        raise ValueError("sex must be 'male' or 'female'")


def calories_target_from_goal(
    tdee_kcal: float, goal: Goal, delta_kcal: Optional[int] = None
) -> float:
    """
    Kalorienziel aus Ziel ableiten.
    - cut: Standard -400 kcal (wenn delta_kcal None)
    - maintain: 0
    - bulk: Standard +250 kcal (wenn delta_kcal None)
    """
    if goal == "maintain":
        return tdee_kcal

    if goal == "cut":
        d = -400 if delta_kcal is None else -abs(delta_kcal)
        return tdee_kcal + d

    if goal == "bulk":
        d = 250 if delta_kcal is None else abs(delta_kcal)
        return tdee_kcal + d

    raise ValueError("goal must be 'cut', 'maintain', or 'bulk'")


def compute_targets(
    *,
    weight_kg: float,
    height_cm: float,
    age_years: int,
    sex: Sex,
    activity: Literal["sedentary", "light", "moderate", "very_active", "extreme"],
    goal: Goal = "maintain",
    goal_delta_kcal: Optional[int] = None,
    protein_g_per_kg: float = 1.8,
    fat_g_per_kg: float = 0.9,
) -> MacroTargets:
    """
    Berechnet Kalorien & Makros:
    - Protein und Fett via g/kg
    - Kohlenhydrate = Restkalorien
    """
    if weight_kg <= 0 or height_cm <= 0 or age_years <= 0:
        raise ValueError("weight_kg, height_cm, age_years must be > 0")

    if activity not in ACTIVITY_FACTORS:
        raise ValueError(
            f"activity must be one of: {', '.join(ACTIVITY_FACTORS.keys())}"
        )

    if protein_g_per_kg <= 0:
        raise ValueError("protein_g_per_kg must be > 0")

    if fat_g_per_kg <= 0:
        raise ValueError("fat_g_per_kg must be > 0")

    # 1) BMR & TDEE
    bmr = mifflin_st_jeor_bmr(
        weight_kg=weight_kg, height_cm=height_cm, age_years=age_years, sex=sex
    )
    tdee = bmr * ACTIVITY_FACTORS[activity]

    # 2) Kalorienziel (cut/maintain/bulk)
    target_kcal = calories_target_from_goal(tdee, goal, goal_delta_kcal)

    # 3) Makros
    protein_g = protein_g_per_kg * weight_kg
    fat_g = fat_g_per_kg * weight_kg

    protein_kcal = protein_g * 4
    fat_kcal = fat_g * 9

    remaining_kcal = target_kcal - protein_kcal - fat_kcal
    carbs_g = (
        remaining_kcal / 4
    )  # kann < 0 werden, wenn Protein/Fett zu hoch gewählt wurden

    # Guardrail: wenn carbs negativ -> Werte sind unlogisch für das Kalorienziel
    if carbs_g < 0:
        raise ValueError(
            "Makros ergeben negative Kohlenhydrate. "
            "Reduziere protein_g_per_kg/fat_g_per_kg oder erhöhe target kcal."
        )

    carbs_kcal = carbs_g * 4

    # gerundete Ausgabe
    return MacroTargets(
        bmr_kcal=int(round(bmr)),
        tdee_kcal=int(round(tdee)),
        target_kcal=int(round(target_kcal)),
        protein_g=int(round(protein_g)),
        fat_g=int(round(fat_g)),
        carbs_g=int(round(carbs_g)),
        protein_kcal=int(round(protein_kcal)),
        fat_kcal=int(round(fat_kcal)),
        carbs_kcal=int(round(carbs_kcal)),
    )


if __name__ == "__main__":
    # Beispiel: 80 kg, 180 cm, 23, male, moderat aktiv, Erhalt
    targets = compute_targets(
        weight_kg=82,
        height_cm=175,
        age_years=20,
        sex="male",
        activity="light",
        goal="cut",
        protein_g_per_kg=2.0,
        fat_g_per_kg=0.9,
    )
    print(targets)
