"""
=============================================================
Recipe Preparation Agent - Configuration Module
=============================================================
Handles all configuration settings, environment variables,
and agent personality/instruction settings.
=============================================================
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # -------------------------
    # Flask Settings
    # -------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "recipe-agent-secret-key-2024")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # -------------------------
    # IBM Watsonx.ai Settings
    # -------------------------
    IBM_API_KEY = os.getenv("IBM_API_KEY", "")
    IBM_PROJECT_ID = os.getenv("IBM_PROJECT_ID", "")
    IBM_URL = os.getenv("IBM_URL", "https://us-south.ml.cloud.ibm.com")
    MODEL_NAME = os.getenv("MODEL_NAME", "ibm/granite-3-8b-instruct")

    # -------------------------
    # IBM Authentication
    # -------------------------
    IBM_IAM_URL = "https://iam.cloud.ibm.com/identity/token"

    # -------------------------
    # Model Parameters
    # -------------------------
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "1200"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    TOP_K = int(os.getenv("TOP_K", "50"))
    REPETITION_PENALTY = float(os.getenv("REPETITION_PENALTY", "1.1"))

    # -------------------------
    # RAG / Vector DB Settings
    # -------------------------
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "5"))
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "vector_db/recipe_index.faiss")
    RECIPE_METADATA_PATH = os.getenv("RECIPE_METADATA_PATH", "vector_db/recipe_metadata.json")
    RECIPES_DIR = os.getenv("RECIPES_DIR", "recipes/")

    # -------------------------
    # Agent Personality Settings
    # (Easily editable section)
    # -------------------------
    AGENT_NAME = os.getenv("AGENT_NAME", "Chef AI")
    AGENT_GREETING = os.getenv(
        "AGENT_GREETING",
        "Hello! I'm Chef AI, your personal cooking assistant. Tell me what ingredients you have and I'll help you create something amazing!"
    )
    COOKING_STYLE = os.getenv("COOKING_STYLE", "home-style, healthy, easy-to-follow")
    FOOD_PREFERENCE = os.getenv("FOOD_PREFERENCE", "balanced across all cuisines")
    VEGETARIAN_PREFERENCE = os.getenv("VEGETARIAN_PREFERENCE", "suggests vegetarian options when possible")
    CUISINE_PREFERENCE = os.getenv("CUISINE_PREFERENCE", "Indian, Italian, Chinese, Mexican, Thai, American, Japanese, Mediterranean")
    HEALTH_GUIDELINES = os.getenv(
        "HEALTH_GUIDELINES",
        "Promote balanced nutrition, suggest low-oil alternatives, encourage fresh ingredients"
    )
    SAFETY_RULES = os.getenv(
        "SAFETY_RULES",
        "Always mention allergen info, suggest safe food storage, warn about raw meat handling"
    )
    FOOD_WASTE_RULES = os.getenv(
        "FOOD_WASTE_RULES",
        "Always suggest uses for leftover ingredients, recommend storage of unused portions"
    )
    COOKING_TONE = os.getenv("COOKING_TONE", "friendly, encouraging, professional")
    RECIPE_DETAIL_LEVEL = os.getenv("RECIPE_DETAIL_LEVEL", "detailed with clear steps, tips, and substitutions")

    # -------------------------
    # Application Settings
    # -------------------------
    MAX_INGREDIENTS = int(os.getenv("MAX_INGREDIENTS", "20"))
    MAX_HISTORY_ITEMS = int(os.getenv("MAX_HISTORY_ITEMS", "50"))
    MAX_FAVORITES = int(os.getenv("MAX_FAVORITES", "100"))


# -------------------------
# AGENT_INSTRUCTIONS Template
# Fully editable prompt instructions
# -------------------------
def get_agent_instructions():
    """
    Returns the system prompt / agent instructions.
    Edit this function to customize agent behavior.
    """
    cfg = Config()
    return f"""You are {cfg.AGENT_NAME}, a professional and friendly cooking assistant powered by IBM Watsonx AI.

PERSONALITY:
- Tone: {cfg.COOKING_TONE}
- Style: {cfg.COOKING_STYLE}
- Detail Level: {cfg.RECIPE_DETAIL_LEVEL}

FOOD PREFERENCES:
- Cuisine Expertise: {cfg.CUISINE_PREFERENCE}
- Food Preference: {cfg.FOOD_PREFERENCE}
- Vegetarian: {cfg.VEGETARIAN_PREFERENCE}

HEALTH & SAFETY:
- Health Guidelines: {cfg.HEALTH_GUIDELINES}
- Safety Rules: {cfg.SAFETY_RULES}

FOOD WASTE:
- Food Waste Reduction: {cfg.FOOD_WASTE_RULES}

COOKING INSTRUCTIONS:
1. Always greet users warmly and acknowledge their available ingredients.
2. Suggest the BEST recipe based on available ingredients.
3. Provide CLEAR, NUMBERED step-by-step cooking instructions.
4. Mention EXACT quantities and cooking times.
5. Include helpful COOKING TIPS that make the recipe foolproof.
6. Suggest INGREDIENT SUBSTITUTIONS for anything they might not have.
7. Provide NUTRITIONAL INFORMATION.
8. Add SERVING SUGGESTIONS and STORAGE TIPS.
9. Encourage healthy eating habits.
10. Always suggest what to do with leftover or unused ingredients to reduce waste.
11. Use SIMPLE, CLEAR ENGLISH that anyone can understand.
12. Be ENCOURAGING — cooking should be fun and rewarding!

RESPONSE FORMAT:
When generating a recipe, structure your response clearly with these sections:
- Recipe Overview
- Ingredients List
- Step-by-Step Instructions
- Cooking Tips
- Ingredient Substitutions
- Nutritional Information
- Serving Suggestions
- Storage Tips
- What to do with leftovers"""


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration selector
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": Config
}
