"""
=============================================================
Recipe Preparation Agent - Utility Functions
=============================================================
Helper utilities for input validation, data formatting,
ingredient matching, and session management.
=============================================================
"""

import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


# -------------------------
# Input Validation
# -------------------------

def validate_ingredients(ingredients: List[str]) -> Dict[str, Any]:
    """
    Validate and sanitize a list of ingredient inputs.

    Args:
        ingredients: Raw list of ingredient strings.

    Returns:
        Dict with 'valid' bool, 'ingredients' list, and 'error' message.
    """
    if not ingredients:
        return {"valid": False, "ingredients": [], "error": "No ingredients provided. Please add at least one ingredient."}

    cleaned = []
    for ing in ingredients:
        # Sanitize: strip whitespace, remove special chars, lowercase
        ing = re.sub(r"[^a-zA-Z0-9\s\-]", "", str(ing)).strip().lower()
        if 2 <= len(ing) <= 50:
            cleaned.append(ing)

    if not cleaned:
        return {"valid": False, "ingredients": [], "error": "Invalid ingredients. Use letters only, 2-50 characters each."}

    if len(cleaned) > 20:
        return {"valid": False, "ingredients": [], "error": "Too many ingredients. Maximum 20 allowed at once."}

    return {"valid": True, "ingredients": cleaned, "error": None}


def validate_cuisine(cuisine: str) -> str:
    """Validate cuisine selection against allowed list."""
    allowed = [
        "any", "indian", "italian", "chinese", "mexican",
        "thai", "american", "japanese", "mediterranean"
    ]
    cuisine = str(cuisine).strip().lower()
    return cuisine if cuisine in allowed else "any"


def validate_diet(diet: str) -> str:
    """Validate dietary preference against allowed list."""
    allowed = [
        "any", "vegetarian", "non vegetarian", "vegan",
        "gluten free", "dairy free", "low carb", "high protein",
        "keto", "diabetic friendly"
    ]
    diet = str(diet).strip().lower()
    return diet if diet in allowed else "any"


def validate_difficulty(difficulty: str) -> str:
    """Validate difficulty level."""
    allowed = ["any", "easy", "medium", "hard"]
    difficulty = str(difficulty).strip().lower()
    return difficulty if difficulty in allowed else "any"


# -------------------------
# Ingredient Utilities
# -------------------------

def calculate_ingredient_match(recipe_ingredients: List[str], user_ingredients: List[str]) -> Dict[str, Any]:
    """
    Calculate how well user ingredients match a recipe.

    Args:
        recipe_ingredients: List of recipe required ingredients.
        user_ingredients: List of ingredients the user has.

    Returns:
        Dict with match_percentage, matched, missing, extra.
    """
    recipe_set = set(ing.lower() for ing in recipe_ingredients)
    user_set = set(ing.lower() for ing in user_ingredients)

    # Also check partial matches (e.g., "chicken breast" matches "chicken")
    matched = set()
    for u_ing in user_set:
        for r_ing in recipe_set:
            if u_ing in r_ing or r_ing in u_ing:
                matched.add(r_ing)

    missing = recipe_set - matched
    extra = user_set - set(ing for ing in user_set if any(ing in r or r in ing for r in recipe_set))

    match_percentage = (len(matched) / len(recipe_set) * 100) if recipe_set else 0

    return {
        "match_percentage": round(match_percentage, 1),
        "matched": sorted(list(matched)),
        "missing": sorted(list(missing)),
        "extra": sorted(list(extra)),
        "total_required": len(recipe_set),
        "total_matched": len(matched)
    }


def format_ingredient_list(ingredients: List[str]) -> str:
    """Format ingredient list into a readable string."""
    if not ingredients:
        return "No ingredients"
    return ", ".join(ing.capitalize() for ing in ingredients)


def parse_ingredients_from_text(text: str) -> List[str]:
    """
    Parse ingredients from comma-separated or newline-separated text.

    Args:
        text: Raw text input with ingredients.

    Returns:
        List of cleaned ingredient strings.
    """
    # Split on commas, newlines, or semicolons
    raw = re.split(r"[,\n;]+", text)
    ingredients = []
    for item in raw:
        item = item.strip().lower()
        item = re.sub(r"[^a-zA-Z0-9\s\-]", "", item).strip()
        if item and 2 <= len(item) <= 50:
            ingredients.append(item)
    return ingredients[:20]  # Limit to 20


# -------------------------
# Recipe Formatting
# -------------------------

def format_recipe_for_display(recipe: Dict[str, Any], match_info: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Format a recipe dictionary for frontend display.

    Args:
        recipe: Raw recipe dictionary.
        match_info: Optional match info from calculate_ingredient_match.

    Returns:
        Formatted recipe dict with all display fields.
    """
    formatted = {
        "id": recipe.get("id", ""),
        "name": recipe.get("name", "Unknown Recipe"),
        "cuisine": recipe.get("cuisine", ""),
        "diet": recipe.get("diet", []),
        "difficulty": recipe.get("difficulty", ""),
        "prep_time": recipe.get("prep_time", 0),
        "cook_time": recipe.get("cook_time", 0),
        "total_time": recipe.get("prep_time", 0) + recipe.get("cook_time", 0),
        "servings": recipe.get("servings", 2),
        "calories": recipe.get("calories", 0),
        "protein": recipe.get("protein", 0),
        "fat": recipe.get("fat", 0),
        "carbohydrates": recipe.get("carbohydrates", 0),
        "ingredients": recipe.get("ingredients", []),
        "instructions": recipe.get("instructions", []),
        "cooking_tips": recipe.get("cooking_tips", []),
        "serving_suggestions": recipe.get("serving_suggestions", ""),
        "storage_tips": recipe.get("storage_tips", ""),
        "substitutions": recipe.get("substitutions", {}),
        "tags": recipe.get("tags", []),
        "emoji": get_cuisine_emoji(recipe.get("cuisine", "")),
        "difficulty_color": get_difficulty_color(recipe.get("difficulty", "")),
        "difficulty_badge": recipe.get("difficulty", "Easy"),
    }

    if match_info:
        formatted["match_percentage"] = match_info.get("match_percentage", 0)
        formatted["matched_ingredients"] = match_info.get("matched", [])
        formatted["missing_ingredients"] = match_info.get("missing", [])

    return formatted


def get_cuisine_emoji(cuisine: str) -> str:
    """Return appropriate emoji for a cuisine."""
    emojis = {
        "Indian": "🍛",
        "Italian": "🍝",
        "Chinese": "🥢",
        "Mexican": "🌮",
        "Thai": "🍜",
        "American": "🍔",
        "Japanese": "🍱",
        "Mediterranean": "🥗"
    }
    return emojis.get(cuisine, "🍽️")


def get_difficulty_color(difficulty: str) -> str:
    """Return Bootstrap color class for difficulty level."""
    colors = {
        "Easy": "success",
        "Medium": "warning",
        "Hard": "danger"
    }
    return colors.get(difficulty, "secondary")


# -------------------------
# History Management
# -------------------------

def add_to_history(session: dict, recipe: Dict[str, Any], ingredients: List[str]) -> None:
    """Add a recipe view to the session history."""
    if "history" not in session:
        session["history"] = []

    entry = {
        "recipe_id": recipe.get("id", ""),
        "recipe_name": recipe.get("name", ""),
        "cuisine": recipe.get("cuisine", ""),
        "ingredients_used": ingredients,
        "timestamp": datetime.now().isoformat(),
        "calories": recipe.get("calories", 0)
    }

    # Avoid duplicates (same recipe within 5 min)
    session["history"] = [
        h for h in session["history"]
        if h["recipe_id"] != entry["recipe_id"]
    ]

    session["history"].insert(0, entry)
    session["history"] = session["history"][:50]  # Keep max 50
    session.modified = True


def add_to_favorites(session: dict, recipe: Dict[str, Any]) -> Dict[str, str]:
    """Add recipe to favorites. Returns status message."""
    if "favorites" not in session:
        session["favorites"] = []

    # Check if already in favorites
    if any(f["recipe_id"] == recipe.get("id") for f in session["favorites"]):
        return {"status": "exists", "message": "Recipe is already in your favorites!"}

    if len(session["favorites"]) >= 100:
        return {"status": "full", "message": "Favorites list is full. Remove some to add new ones."}

    entry = {
        "recipe_id": recipe.get("id", ""),
        "recipe_name": recipe.get("name", ""),
        "cuisine": recipe.get("cuisine", ""),
        "difficulty": recipe.get("difficulty", ""),
        "calories": recipe.get("calories", 0),
        "timestamp": datetime.now().isoformat()
    }
    session["favorites"].insert(0, entry)
    session.modified = True
    return {"status": "added", "message": f"'{recipe.get('name')}' added to favorites!"}


def remove_from_favorites(session: dict, recipe_id: str) -> Dict[str, str]:
    """Remove a recipe from favorites."""
    if "favorites" not in session:
        return {"status": "not_found", "message": "Recipe not found in favorites."}

    original_len = len(session["favorites"])
    session["favorites"] = [f for f in session["favorites"] if f["recipe_id"] != recipe_id]
    session.modified = True

    if len(session["favorites"]) < original_len:
        return {"status": "removed", "message": "Recipe removed from favorites."}
    return {"status": "not_found", "message": "Recipe not found in favorites."}


# -------------------------
# Response Formatting
# -------------------------

def build_error_response(message: str, code: int = 400) -> Dict[str, Any]:
    """Build a standardized error response."""
    return {
        "success": False,
        "error": message,
        "code": code
    }


def build_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Build a standardized success response."""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def truncate_text(text: str, max_length: int = 150) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."
