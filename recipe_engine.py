"""
=============================================================
Recipe Preparation Agent - Recipe Engine
=============================================================
Manages recipe operations: filtering, scoring, suggestions,
leftover management, and non-AI recipe logic.
=============================================================
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# Comprehensive ingredient substitution map
SUBSTITUTION_MAP = {
    "butter": ["olive oil", "coconut oil", "ghee", "margarine", "avocado"],
    "milk": ["almond milk", "oat milk", "coconut milk", "soy milk", "water + 1 tbsp butter"],
    "cream": ["coconut cream", "Greek yogurt", "cashew cream", "evaporated milk"],
    "egg": ["flax egg (1 tbsp flaxseed + 3 tbsp water)", "applesauce (1/4 cup)", "banana (mashed)", "silken tofu"],
    "all-purpose flour": ["whole wheat flour", "almond flour", "rice flour", "oat flour"],
    "sugar": ["honey", "maple syrup", "coconut sugar", "stevia", "agave nectar"],
    "soy sauce": ["tamari (gluten-free)", "coconut aminos", "fish sauce", "Worcestershire sauce"],
    "olive oil": ["avocado oil", "coconut oil", "vegetable oil", "butter"],
    "parmesan": ["pecorino romano", "grana padano", "nutritional yeast (vegan)"],
    "garlic": ["garlic powder (1/4 tsp per clove)", "shallots", "garlic paste"],
    "lemon juice": ["lime juice", "white wine vinegar", "apple cider vinegar"],
    "chicken broth": ["vegetable broth", "water + bouillon cube", "mushroom broth"],
    "heavy cream": ["Greek yogurt", "coconut cream", "cashew cream", "half-and-half"],
    "yogurt": ["sour cream", "coconut yogurt", "buttermilk", "silken tofu"],
    "paneer": ["tofu", "halloumi", "queso fresco", "cottage cheese"],
    "ghee": ["clarified butter", "olive oil", "coconut oil"],
    "rice": ["quinoa", "cauliflower rice", "barley", "couscous"],
    "pasta": ["zucchini noodles", "shirataki noodles", "rice noodles", "spaghetti squash"],
    "breadcrumbs": ["crushed crackers", "oats", "almond flour", "crushed cornflakes"],
    "honey": ["maple syrup", "agave nectar", "golden syrup", "date syrup"],
    "vinegar": ["lemon juice", "lime juice", "tamarind water"],
    "cumin": ["caraway seeds", "chili powder", "coriander"],
    "coriander": ["parsley", "basil", "cilantro"],
    "chili powder": ["paprika + cayenne", "hot sauce", "red pepper flakes"],
    "bacon": ["turkey bacon", "pancetta", "smoked tofu", "tempeh"],
    "beef": ["lamb", "pork", "mushrooms (vegetarian)", "lentils (vegan)"],
    "chicken": ["turkey", "tofu", "chickpeas (vegetarian)", "seitan"]
}

# Healthy alternative suggestions
HEALTHY_ALTERNATIVES = {
    "frying": "Try air frying or baking instead — same crispy result with less oil!",
    "white rice": "Swap white rice for brown rice, quinoa, or cauliflower rice for more fiber.",
    "white bread": "Use whole wheat or sourdough for more nutrients.",
    "sugar": "Reduce by 25% — you often won't notice. Use cinnamon for sweetness.",
    "salt": "Use herbs, lemon juice, or spices to reduce sodium intake.",
    "cream": "Greek yogurt adds creaminess with less fat and more protein.",
    "butter": "Replace half the butter with mashed avocado in baking for healthy fats.",
    "mayonnaise": "Greek yogurt is a great substitute — lighter and more nutritious."
}


class RecipeEngine:
    """
    Core recipe logic engine for scoring, filtering, and recommendations.
    Works in conjunction with the RAG system for intelligent suggestions.
    """

    def __init__(self, rag_instance=None):
        """
        Args:
            rag_instance: Optional RecipeRAG instance for data access.
        """
        self.rag = rag_instance

    # -------------------------
    # Recipe Filtering & Scoring
    # -------------------------

    def score_recipe(self, recipe: Dict[str, Any], user_ingredients: List[str]) -> float:
        """
        Score a recipe based on ingredient availability.

        Scoring formula:
        - Ingredient match: 60%
        - Fewer missing ingredients: 30%
        - Complexity bonus for easy recipes: 10%

        Args:
            recipe: Recipe dictionary.
            user_ingredients: User's available ingredients.

        Returns:
            Float score between 0 and 100.
        """
        recipe_ings = [i.lower() for i in recipe.get("ingredients", [])]
        user_ings = [i.lower() for i in user_ingredients]

        if not recipe_ings:
            return 0.0

        # Count matched ingredients (with partial matching)
        matched_count = sum(
            1 for r_ing in recipe_ings
            if any(u_ing in r_ing or r_ing in u_ing for u_ing in user_ings)
        )
        missing_count = len(recipe_ings) - matched_count

        # Score components
        match_score = (matched_count / len(recipe_ings)) * 60
        missing_penalty = (missing_count / len(recipe_ings)) * 30
        ease_bonus = 10 if recipe.get("difficulty") == "Easy" else (5 if recipe.get("difficulty") == "Medium" else 0)

        return round(match_score + ease_bonus - missing_penalty / 2, 2)

    def filter_recipes(
        self,
        recipes: List[Dict[str, Any]],
        cuisine: str = "any",
        diet: str = "any",
        difficulty: str = "any",
        max_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to a list of recipes.

        Args:
            recipes: List of recipe dicts to filter.
            cuisine: Cuisine filter (or "any").
            diet: Dietary filter (or "any").
            difficulty: Difficulty filter (or "any").
            max_time: Max total cooking time in minutes.

        Returns:
            Filtered list of recipes.
        """
        filtered = []
        for recipe in recipes:
            # Cuisine filter
            if cuisine and cuisine.lower() != "any":
                if recipe.get("cuisine", "").lower() != cuisine.lower():
                    continue

            # Diet filter
            if diet and diet.lower() != "any":
                recipe_diets = [d.lower() for d in recipe.get("diet", [])]
                if diet.lower() not in recipe_diets:
                    continue

            # Difficulty filter
            if difficulty and difficulty.lower() != "any":
                if recipe.get("difficulty", "").lower() != difficulty.lower():
                    continue

            # Time filter
            if max_time:
                total_time = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)
                if total_time > max_time:
                    continue

            filtered.append(recipe)

        return filtered

    # -------------------------
    # Substitution Engine
    # -------------------------

    def get_substitutions(self, missing_ingredients: List[str]) -> Dict[str, List[str]]:
        """
        Find substitutions for missing ingredients.

        Args:
            missing_ingredients: List of ingredients the user doesn't have.

        Returns:
            Dict mapping each missing ingredient to list of substitutes.
        """
        substitutions = {}
        for ingredient in missing_ingredients:
            ing_lower = ingredient.lower()
            # Direct match
            if ing_lower in SUBSTITUTION_MAP:
                substitutions[ingredient] = SUBSTITUTION_MAP[ing_lower]
                continue
            # Partial match
            for key, subs in SUBSTITUTION_MAP.items():
                if key in ing_lower or ing_lower in key:
                    substitutions[ingredient] = subs
                    break
        return substitutions

    def get_recipe_substitutions(self, recipe: Dict[str, Any]) -> Dict[str, str]:
        """
        Get substitutions defined within a recipe's own substitution dict,
        merged with global substitution map for missing items.

        Args:
            recipe: Recipe dictionary.

        Returns:
            Combined substitution dict.
        """
        recipe_subs = recipe.get("substitutions", {})
        all_subs = {}

        for ingredient in recipe.get("ingredients", []):
            ing_lower = ingredient.lower()
            if ing_lower in recipe_subs:
                all_subs[ingredient] = recipe_subs[ing_lower]
            elif ing_lower in SUBSTITUTION_MAP:
                all_subs[ingredient] = ", ".join(SUBSTITUTION_MAP[ing_lower][:2])

        return all_subs

    # -------------------------
    # Leftover Recipe Suggestions
    # -------------------------

    def suggest_leftover_recipes(
        self,
        leftover_ingredients: List[str],
        all_recipes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Suggest recipes for using leftover ingredients.

        Args:
            leftover_ingredients: Available leftover ingredients.
            all_recipes: Complete recipe database.

        Returns:
            Top 3 recipes sorted by ingredient match.
        """
        scored_recipes = []
        for recipe in all_recipes:
            score = self.score_recipe(recipe, leftover_ingredients)
            if score > 20:  # Minimum relevance threshold
                scored_recipes.append({**recipe, "match_score": score})

        scored_recipes.sort(key=lambda r: r["match_score"], reverse=True)
        return scored_recipes[:3]

    # -------------------------
    # Healthy Alternatives
    # -------------------------

    def get_healthy_tips(self, recipe: Dict[str, Any]) -> List[str]:
        """
        Generate healthy alternative tips for a recipe.

        Args:
            recipe: Recipe dictionary.

        Returns:
            List of health tip strings.
        """
        tips = []
        ingredients = [i.lower() for i in recipe.get("ingredients", [])]
        instructions = " ".join(recipe.get("instructions", [])).lower()

        for key, tip in HEALTHY_ALTERNATIVES.items():
            if key in ingredients or key in instructions:
                tips.append(tip)

        # Add general tips
        tips.append(f"This recipe has {recipe.get('calories', 0)} calories per serving — "
                    f"consider adjusting portion size to meet your goals.")
        if recipe.get("protein", 0) > 25:
            tips.append("This recipe is high in protein — great for muscle building and satiety!")
        if recipe.get("diet") and "Vegetarian" in recipe.get("diet", []):
            tips.append("This vegetarian recipe is eco-friendly and often lower in saturated fat.")

        return tips[:4]  # Return max 4 tips

    # -------------------------
    # Portion & Time Estimates
    # -------------------------

    def estimate_portions(self, recipe: Dict[str, Any], servings: int) -> Dict[str, Any]:
        """
        Scale recipe nutritional info and ingredient quantities for custom serving size.

        Args:
            recipe: Recipe dict with default servings.
            servings: Desired number of servings.

        Returns:
            Dict with scaled nutritional info.
        """
        default_servings = recipe.get("servings", 2) or 2
        scale_factor = servings / default_servings

        return {
            "servings": servings,
            "calories": round(recipe.get("calories", 0) * scale_factor),
            "protein": round(recipe.get("protein", 0) * scale_factor, 1),
            "fat": round(recipe.get("fat", 0) * scale_factor, 1),
            "carbohydrates": round(recipe.get("carbohydrates", 0) * scale_factor, 1),
            "scale_factor": round(scale_factor, 2)
        }

    def estimate_cooking_time(self, recipe: Dict[str, Any], skill_level: str = "intermediate") -> str:
        """
        Estimate total cooking time with skill level adjustment.

        Args:
            recipe: Recipe dictionary.
            skill_level: 'beginner', 'intermediate', 'advanced'.

        Returns:
            Formatted time string with adjustments.
        """
        base_time = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)
        adjustments = {"beginner": 1.4, "intermediate": 1.1, "advanced": 1.0}
        factor = adjustments.get(skill_level, 1.1)
        adjusted = round(base_time * factor)

        if adjusted > 60:
            hours = adjusted // 60
            mins = adjusted % 60
            return f"~{hours}h {mins}min"
        return f"~{adjusted} min"

    # -------------------------
    # Popular & Category Helpers
    # -------------------------

    def get_categories(self) -> List[Dict[str, str]]:
        """Return recipe category cards for the homepage."""
        return [
            {"name": "Indian", "emoji": "🍛", "description": "Spices, curries, and comfort"},
            {"name": "Italian", "emoji": "🍝", "description": "Pasta, pizza, and more"},
            {"name": "Chinese", "emoji": "🥢", "description": "Wok-fired, flavorful dishes"},
            {"name": "Breakfast", "emoji": "🍳", "description": "Start your day right"},
            {"name": "Desserts", "emoji": "🍰", "description": "Sweet treats and indulgences"},
            {"name": "American", "emoji": "🍔", "description": "Classic comfort food"},
        ]

    def get_cuisines(self) -> List[str]:
        """Return supported cuisine list."""
        return [
            "Any", "Indian", "Italian", "Chinese", "Mexican",
            "Thai", "American", "Japanese", "Mediterranean"
        ]

    def get_dietary_options(self) -> List[str]:
        """Return supported dietary options."""
        return [
            "Any", "Vegetarian", "Non Vegetarian", "Vegan",
            "Gluten Free", "Dairy Free", "Low Carb",
            "High Protein", "Keto", "Diabetic Friendly"
        ]
