"""
=============================================================
Recipe Preparation Agent - Flask Application
=============================================================
Main Flask application entry point.
Handles all routes, API endpoints, and orchestrates
the RAG + AI pipeline for recipe generation.
=============================================================
"""

import os
import json
import logging
from datetime import datetime
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for
)

from config import Config
from agent import WatsonxAgent
from rag import RecipeRAG
from recipe_engine import RecipeEngine
from utils import (
    validate_ingredients, validate_cuisine, validate_diet,
    validate_difficulty, calculate_ingredient_match,
    format_recipe_for_display, add_to_history,
    add_to_favorites, remove_from_favorites,
    parse_ingredients_from_text, build_error_response,
    build_success_response, get_cuisine_emoji,
    get_difficulty_color
)

# -------------------------
# Logging Configuration
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# -------------------------
# Flask App Initialization
# -------------------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# -------------------------
# Initialize AI/RAG Components
# -------------------------
logger.info("Initializing Recipe Preparation Agent...")

try:
    rag_engine = RecipeRAG()
    recipe_engine = RecipeEngine(rag_instance=rag_engine)
    ai_agent = WatsonxAgent()
    logger.info(f"Agent initialized. {rag_engine.total_recipes} recipes in knowledge base.")
except Exception as e:
    logger.error(f"Initialization error: {e}")
    rag_engine = None
    recipe_engine = RecipeEngine()
    ai_agent = WatsonxAgent()


# -------------------------
# Template Context Processors
# -------------------------

@app.context_processor
def inject_globals():
    """Inject global variables available to all templates."""
    return {
        "agent_name": Config.AGENT_NAME,
        "current_year": datetime.now().year,
        "cuisines": recipe_engine.get_cuisines(),
        "dietary_options": recipe_engine.get_dietary_options(),
        "total_recipes": rag_engine.total_recipes if rag_engine else 0,
        "favorites_count": len(session.get("favorites", [])),
        "history_count": len(session.get("history", []))
    }


# -------------------------
# Main Routes
# -------------------------

@app.route("/")
def index():
    """
    Homepage — display popular recipes, categories, and ingredient search.
    """
    popular_recipes = []
    categories = recipe_engine.get_categories()

    if rag_engine:
        popular_recipes = rag_engine.get_popular_recipes(limit=6)
        # Add display metadata
        for recipe in popular_recipes:
            recipe["emoji"] = get_cuisine_emoji(recipe.get("cuisine", ""))
            recipe["difficulty_color"] = get_difficulty_color(recipe.get("difficulty", ""))
            recipe["total_time"] = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)

    return render_template(
        "index.html",
        popular_recipes=popular_recipes,
        categories=categories,
        greeting=Config.AGENT_GREETING
    )


@app.route("/search", methods=["POST"])
def search_recipes():
    """
    AJAX endpoint to search recipes based on ingredients and filters.
    Returns JSON with retrieved recipes and AI-generated instructions.
    """
    try:
        data = request.get_json() or {}

        # Extract and validate inputs
        raw_ingredients = data.get("ingredients", [])
        cuisine = validate_cuisine(data.get("cuisine", "any"))
        diet = validate_diet(data.get("diet", "any"))
        difficulty = validate_difficulty(data.get("difficulty", "any"))

        # Validate ingredients
        validation = validate_ingredients(raw_ingredients)
        if not validation["valid"]:
            return jsonify(build_error_response(validation["error"])), 400

        ingredients = validation["ingredients"]

        # Step 1: RAG retrieval — find top matching recipes
        retrieved_recipes = rag_engine.retrieve_recipes(
            ingredients=ingredients,
            cuisine=cuisine,
            diet=diet,
            difficulty=difficulty,
            top_k=5
        ) if rag_engine else []

        # Step 2: Generate AI instructions using Granite + RAG context
        ai_result = ai_agent.generate_recipe_instructions(
            user_ingredients=ingredients,
            retrieved_recipes=retrieved_recipes,
            cuisine=cuisine,
            diet=diet,
            difficulty=difficulty
        )

        # Step 3: Format recipes for display
        formatted_recipes = []
        for recipe in retrieved_recipes:
            match_info = {
                "match_percentage": recipe.get("match_percentage", 0),
                "matched": recipe.get("matched_ingredients", []),
                "missing": recipe.get("missing_ingredients", [])
            }
            formatted = format_recipe_for_display(recipe, match_info)
            formatted_recipes.append(formatted)

        # Step 4: Add to session history
        if ai_result.get("selected_recipe"):
            add_to_history(session, ai_result["selected_recipe"], ingredients)

        # Step 5: Get healthy tips for best recipe
        healthy_tips = []
        if ai_result.get("selected_recipe"):
            healthy_tips = recipe_engine.get_healthy_tips(ai_result["selected_recipe"])

        # Step 6: Get substitutions for missing ingredients
        missing_ings = []
        if formatted_recipes:
            missing_ings = formatted_recipes[0].get("missing_ingredients", [])
        substitutions = recipe_engine.get_substitutions(missing_ings)

        response_data = {
            "recipes": formatted_recipes,
            "ai_instructions": ai_result.get("ai_instructions", ""),
            "other_suggestions": ai_result.get("extra_suggestions", ""),
            "healthy_tips": healthy_tips,
            "substitutions": substitutions,
            "total_found": len(formatted_recipes),
            "ingredients_used": ingredients
        }

        return jsonify(build_success_response(response_data, f"Found {len(formatted_recipes)} recipes!"))

    except ValueError as e:
        logger.warning(f"Validation error in search: {e}")
        return jsonify(build_error_response(str(e))), 400
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify(build_error_response("An error occurred while searching. Please try again.")), 500


@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    """
    Recipe detail page — shows full recipe with AI-enhanced instructions.
    """
    if not rag_engine:
        return redirect(url_for("index"))

    recipe = rag_engine.get_recipe_by_id(recipe_id)
    if not recipe:
        return render_template("index.html", error="Recipe not found."), 404

    # Add display metadata
    recipe["emoji"] = get_cuisine_emoji(recipe.get("cuisine", ""))
    recipe["difficulty_color"] = get_difficulty_color(recipe.get("difficulty", ""))
    recipe["total_time"] = recipe.get("prep_time", 0) + recipe.get("cook_time", 0)

    # Get ingredient substitutions
    substitutions = recipe_engine.get_recipe_substitutions(recipe)

    # Get healthy tips
    healthy_tips = recipe_engine.get_healthy_tips(recipe)

    # Get similar recipes
    similar_recipes = rag_engine.retrieve_recipes(
        ingredients=recipe.get("ingredients", []),
        cuisine=recipe.get("cuisine", ""),
        top_k=4
    )
    similar_recipes = [r for r in similar_recipes if r.get("id") != recipe_id][:3]
    for r in similar_recipes:
        r["emoji"] = get_cuisine_emoji(r.get("cuisine", ""))
        r["difficulty_color"] = get_difficulty_color(r.get("difficulty", ""))
        r["total_time"] = r.get("prep_time", 0) + r.get("cook_time", 0)

    # Check if recipe is in favorites
    favorites = session.get("favorites", [])
    is_favorited = any(f["recipe_id"] == recipe_id for f in favorites)

    # Add to history
    add_to_history(session, recipe, recipe.get("ingredients", []))

    return render_template(
        "recipe.html",
        recipe=recipe,
        substitutions=substitutions,
        healthy_tips=healthy_tips,
        similar_recipes=similar_recipes,
        is_favorited=is_favorited
    )


@app.route("/about")
def about():
    """About page — project info, tech stack, and usage guide."""
    stats = {
        "total_recipes": rag_engine.total_recipes if rag_engine else 0,
        "cuisines": 8,
        "dietary_options": 9,
        "ai_powered": True
    }
    return render_template("about.html", stats=stats)


@app.route("/history")
def history():
    """Recipe history and favorites page."""
    history_items = session.get("history", [])
    favorites = session.get("favorites", [])
    return render_template(
        "history.html",
        history=history_items,
        favorites=favorites
    )


# -------------------------
# API Endpoints
# -------------------------

@app.route("/api/recipe/<recipe_id>", methods=["GET"])
def api_get_recipe(recipe_id):
    """API: Get a single recipe by ID."""
    if not rag_engine:
        return jsonify(build_error_response("Service unavailable")), 503

    recipe = rag_engine.get_recipe_by_id(recipe_id)
    if not recipe:
        return jsonify(build_error_response("Recipe not found", 404)), 404

    return jsonify(build_success_response(recipe))


@app.route("/api/favorites/add", methods=["POST"])
def api_add_favorite():
    """API: Add a recipe to session favorites."""
    data = request.get_json() or {}
    recipe_id = data.get("recipe_id", "").strip()

    if not recipe_id:
        return jsonify(build_error_response("recipe_id is required")), 400

    if not rag_engine:
        return jsonify(build_error_response("Service unavailable")), 503

    recipe = rag_engine.get_recipe_by_id(recipe_id)
    if not recipe:
        return jsonify(build_error_response("Recipe not found")), 404

    result = add_to_favorites(session, recipe)
    return jsonify(result)


@app.route("/api/favorites/remove", methods=["POST"])
def api_remove_favorite():
    """API: Remove a recipe from session favorites."""
    data = request.get_json() or {}
    recipe_id = data.get("recipe_id", "").strip()

    if not recipe_id:
        return jsonify(build_error_response("recipe_id is required")), 400

    result = remove_from_favorites(session, recipe_id)
    return jsonify(result)


@app.route("/api/favorites", methods=["GET"])
def api_get_favorites():
    """API: Get all favorited recipes."""
    favorites = session.get("favorites", [])
    return jsonify(build_success_response(favorites))


@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    """API: Clear all recipe history."""
    session["history"] = []
    session.modified = True
    return jsonify({"status": "cleared", "message": "History cleared successfully."})


@app.route("/api/leftovers", methods=["POST"])
def api_leftover_suggestions():
    """API: Get recipe suggestions for leftover ingredients."""
    data = request.get_json() or {}
    raw_ingredients = data.get("ingredients", [])

    validation = validate_ingredients(raw_ingredients)
    if not validation["valid"]:
        return jsonify(build_error_response(validation["error"])), 400

    ingredients = validation["ingredients"]

    # Get matching recipes
    leftover_recipes = rag_engine.get_leftover_suggestions(ingredients) if rag_engine else []

    # Generate AI suggestions
    ai_suggestions = ai_agent.generate_leftover_suggestions(ingredients, leftover_recipes)

    return jsonify(build_success_response({
        "recipes": leftover_recipes[:3],
        "ai_suggestions": ai_suggestions
    }))


@app.route("/api/ingredient-info", methods=["POST"])
def api_ingredient_info():
    """API: Get AI-generated info about a specific ingredient."""
    data = request.get_json() or {}
    ingredient = data.get("ingredient", "").strip()

    if not ingredient or len(ingredient) < 2:
        return jsonify(build_error_response("Please provide a valid ingredient name.")), 400

    info = ai_agent.get_ingredient_info(ingredient)
    return jsonify(build_success_response({"ingredient": ingredient, "info": info}))


@app.route("/api/cuisines", methods=["GET"])
def api_get_cuisines():
    """API: Get list of supported cuisines."""
    return jsonify(build_success_response(recipe_engine.get_cuisines()))


@app.route("/api/popular", methods=["GET"])
def api_popular_recipes():
    """API: Get popular recipes for homepage."""
    if not rag_engine:
        return jsonify(build_error_response("Service unavailable")), 503
    popular = rag_engine.get_popular_recipes(limit=6)
    for r in popular:
        r["emoji"] = get_cuisine_emoji(r.get("cuisine", ""))
        r["difficulty_color"] = get_difficulty_color(r.get("difficulty", ""))
        r["total_time"] = r.get("prep_time", 0) + r.get("cook_time", 0)
    return jsonify(build_success_response(popular))


@app.route("/api/rebuild-index", methods=["POST"])
def api_rebuild_index():
    """API: Rebuild the FAISS vector index (admin use)."""
    if not rag_engine:
        return jsonify(build_error_response("Service unavailable")), 503
    try:
        count = rag_engine.reload_recipes()
        return jsonify(build_success_response(
            {"recipes_indexed": count},
            f"Index rebuilt successfully with {count} recipes."
        ))
    except Exception as e:
        logger.error(f"Index rebuild error: {e}")
        return jsonify(build_error_response(f"Rebuild failed: {str(e)}")), 500


@app.route("/api/parse-ingredients", methods=["POST"])
def api_parse_ingredients():
    """API: Parse ingredients from free-form text input."""
    data = request.get_json() or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify(build_error_response("No text provided.")), 400

    ingredients = parse_ingredients_from_text(text)
    return jsonify(build_success_response({"ingredients": ingredients}))


# -------------------------
# Error Handlers
# -------------------------

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    if request.path.startswith("/api/"):
        return jsonify(build_error_response("Endpoint not found", 404)), 404
    return render_template("index.html", error="Page not found."), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"Server error: {e}")
    if request.path.startswith("/api/"):
        return jsonify(build_error_response("Internal server error", 500)), 500
    return render_template("index.html", error="Something went wrong. Please try again."), 500


# -------------------------
# App Entry Point
# -------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = Config.DEBUG
    logger.info(f"Starting Recipe Preparation Agent on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=debug)
