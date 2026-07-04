"""
=============================================================
Recipe Preparation Agent - AI Agent Module
=============================================================
Handles IBM Watsonx.ai integration and AI recipe generation
using the Granite model with RAG-retrieved context.
=============================================================
"""

import logging
import requests
from typing import List, Dict, Any, Optional

from config import Config, get_agent_instructions

logger = logging.getLogger(__name__)


class WatsonxAgent:
    """
    AI Agent powered by IBM Watsonx.ai Granite model.
    Generates personalized cooking instructions, tips, and suggestions
    using RAG-retrieved recipes as context.
    """

    def __init__(self):
        self.api_key = Config.IBM_API_KEY
        self.project_id = Config.IBM_PROJECT_ID
        self.url = Config.IBM_URL
        self.model_name = Config.MODEL_NAME
        self.iam_url = Config.IBM_IAM_URL
        self._access_token: Optional[str] = None

    # -------------------------
    # IBM IAM Authentication
    # -------------------------

    def _get_access_token(self) -> Optional[str]:
        """
        Retrieve IBM Cloud IAM access token using API key.

        Returns:
            Bearer access token string or None if failed.
        """
        if not self.api_key:
            logger.warning("IBM API key is not configured.")
            return None

        try:
            response = requests.post(
                self.iam_url,
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if token:
                self._access_token = token
                logger.info("IBM IAM access token retrieved successfully.")
            return token
        except requests.RequestException as e:
            logger.error(f"Failed to get IBM IAM token: {e}")
            return None

    def _is_configured(self) -> bool:
        """Check if IBM credentials are properly configured."""
        return bool(self.api_key and self.project_id and self.url)

    # -------------------------
    # Core Generation Method
    # -------------------------

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to IBM Watsonx.ai Granite model and return the response.

        Args:
            prompt: The full prompt to send to the model.

        Returns:
            Generated text from the model.
        """
        if not self._is_configured():
            return self._fallback_response("IBM Watsonx.ai credentials are not configured. Please add your IBM_API_KEY and IBM_PROJECT_ID to the .env file.")

        token = self._get_access_token()
        if not token:
            return self._fallback_response("Could not authenticate with IBM Cloud. Please check your API key.")

        endpoint = f"{self.url}/ml/v1/text/generation?version=2024-03-14"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "model_id": self.model_name,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": Config.MAX_NEW_TOKENS,
                "temperature": Config.TEMPERATURE,
                "top_p": Config.TOP_P,
                "top_k": Config.TOP_K,
                "repetition_penalty": Config.REPETITION_PENALTY,
                "stop_sequences": ["<|endoftext|>", "---END---"]
            },
            "project_id": self.project_id
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
            if not response.ok:
                logger.error(f"Watsonx.ai error {response.status_code}: {response.text}")
            response.raise_for_status()
            result = response.json()
            generated_text = result["results"][0]["generated_text"].strip()
            logger.info("Watsonx.ai generation successful.")
            return generated_text
        except requests.exceptions.Timeout:
            logger.error("Watsonx.ai request timed out.")
            return self._fallback_response("The AI service timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Watsonx.ai API error: {e}")
            return self._fallback_response(f"AI service error: {str(e)}")
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected response format from Watsonx.ai: {e}")
            return self._fallback_response("Received an unexpected response from the AI service.")

    # -------------------------
    # Recipe Generation (RAG + AI)
    # -------------------------

    def generate_recipe_instructions(
        self,
        user_ingredients: List[str],
        retrieved_recipes: List[Dict[str, Any]],
        cuisine: str = "any",
        diet: str = "any",
        difficulty: str = "any"
    ) -> Dict[str, Any]:
        """
        Generate personalized cooking instructions using RAG + Granite.

        RAG Flow:
        1. Top 5 retrieved recipes are passed as context.
        2. Granite selects the BEST recipe and generates full instructions.

        Args:
            user_ingredients: Ingredients the user has available.
            retrieved_recipes: Top-K recipes from FAISS retrieval.
            cuisine: Cuisine preference.
            diet: Dietary preference.
            difficulty: Difficulty preference.

        Returns:
            Dict with 'selected_recipe', 'ai_instructions', and 'extra_suggestions'.
        """
        # If no recipes retrieved, inform the user
        if not retrieved_recipes:
            return {
                "selected_recipe": None,
                "ai_instructions": "I couldn't find any matching recipes for your ingredients. Try adding more common ingredients like onion, garlic, or oil.",
                "extra_suggestions": ""
            }

        # Build RAG context from retrieved recipes
        context_text = self._build_recipe_context(retrieved_recipes)
        system_prompt = get_agent_instructions()

        # Construct the full prompt
        prompt = f"""{system_prompt}

=== RETRIEVED RECIPES CONTEXT ===
{context_text}

=== USER REQUEST ===
Available Ingredients: {', '.join(user_ingredients)}
Cuisine Preference: {cuisine if cuisine != 'any' else 'Any cuisine'}
Dietary Preference: {diet if diet != 'any' else 'No restriction'}
Difficulty Preference: {difficulty if difficulty != 'any' else 'Any difficulty'}

=== YOUR TASK ===
Based on the retrieved recipes and user's available ingredients above:
1. Select the BEST matching recipe from the retrieved context.
2. Generate COMPLETE, PERSONALIZED cooking instructions.
3. Include EXACTLY what the user should do with their available ingredients.
4. Suggest SUBSTITUTIONS for any missing ingredients.
5. Add HELPFUL COOKING TIPS specific to this recipe.
6. Provide NUTRITIONAL INFORMATION per serving.
7. Suggest what to do with any LEFTOVER ingredients.

Format your response as follows:

🍽️ BEST RECIPE: [Recipe Name]
📊 MATCH: [X% of ingredients available]

📋 INGREDIENTS NEEDED:
✅ You have: [list ingredients they have]
❌ Missing: [list missing ingredients with substitutions]

👨‍🍳 STEP-BY-STEP INSTRUCTIONS:
[Numbered steps]

💡 COOKING TIPS:
[Bullet tips]

🔄 INGREDIENT SUBSTITUTIONS:
[Substitution suggestions]

🥗 NUTRITION (per serving):
Calories: | Protein: | Fat: | Carbs:

🍽️ SERVING SUGGESTIONS:
[How to serve]

🫙 STORAGE TIPS:
[Storage instructions]

♻️ LEFTOVER IDEAS:
[What to do with extra ingredients]

"""

        ai_response = self.generate(prompt)

        # Extract the best matching recipe from retrieved list
        best_recipe = retrieved_recipes[0] if retrieved_recipes else None

        return {
            "selected_recipe": best_recipe,
            "ai_instructions": ai_response,
            "extra_suggestions": self._generate_extra_suggestions(
                user_ingredients, retrieved_recipes[1:] if len(retrieved_recipes) > 1 else []
            )
        }

    def generate_leftover_suggestions(
        self,
        leftover_ingredients: List[str],
        leftover_recipes: List[Dict[str, Any]]
    ) -> str:
        """
        Generate creative suggestions for using leftover ingredients.

        Args:
            leftover_ingredients: List of leftover ingredients.
            leftover_recipes: Pre-retrieved recipes using these leftovers.

        Returns:
            AI-generated suggestion text.
        """
        if not leftover_ingredients:
            return "Please specify your leftover ingredients."

        recipe_names = [r["name"] for r in leftover_recipes[:3]]
        recipe_text = ", ".join(recipe_names) if recipe_names else "various recipes"

        prompt = f"""{get_agent_instructions()}

A user has these leftover ingredients: {', '.join(leftover_ingredients)}

Suggest creative, practical ways to use these leftovers. 
Consider these potential recipes from our database: {recipe_text}

Provide:
1. Top 3 recipe suggestions with brief descriptions
2. Quick leftover snack ideas (under 15 minutes)
3. Storage tips for these ingredients
4. Combination ideas to reduce waste

Keep the response friendly and encouraging. Use simple English."""

        return self.generate(prompt)

    def get_ingredient_info(self, ingredient: str) -> str:
        """
        Get nutritional and cooking information about a specific ingredient.

        Args:
            ingredient: Ingredient name.

        Returns:
            AI-generated information about the ingredient.
        """
        prompt = f"""{get_agent_instructions()}

Tell me about this ingredient in cooking: {ingredient}

Provide:
1. Brief description and common uses
2. Nutritional highlights  
3. Best cooking methods
4. What dishes it works best in
5. How to store it properly
6. Common substitutes

Keep it concise, informative, and helpful."""

        return self.generate(prompt)

    # -------------------------
    # Context Building Helpers
    # -------------------------

    def _build_recipe_context(self, recipes: List[Dict[str, Any]]) -> str:
        """
        Build a formatted context string from retrieved recipes for the AI prompt.

        Args:
            recipes: List of recipe dicts from RAG retrieval.

        Returns:
            Formatted string with recipe details.
        """
        context_parts = []
        for i, recipe in enumerate(recipes[:5], 1):  # Use top 5
            ingredients = ", ".join(recipe.get("ingredients", []))
            instructions = " → ".join(recipe.get("instructions", [])[:4])  # First 4 steps
            tips = "; ".join(recipe.get("cooking_tips", [])[:2])
            subs = str(recipe.get("substitutions", {}))
            match_pct = recipe.get("match_percentage", 0)

            context_parts.append(
                f"RECIPE {i}: {recipe.get('name', '')} ({recipe.get('cuisine', '')})\n"
                f"  Ingredient Match: {match_pct}%\n"
                f"  Diet: {', '.join(recipe.get('diet', []))}\n"
                f"  Difficulty: {recipe.get('difficulty', '')} | "
                f"Time: {recipe.get('prep_time', 0) + recipe.get('cook_time', 0)} min\n"
                f"  Calories: {recipe.get('calories', 0)} | "
                f"Protein: {recipe.get('protein', 0)}g | "
                f"Fat: {recipe.get('fat', 0)}g | "
                f"Carbs: {recipe.get('carbohydrates', 0)}g\n"
                f"  Ingredients: {ingredients}\n"
                f"  Steps: {instructions}\n"
                f"  Tips: {tips}\n"
                f"  Substitutions: {subs}\n"
                f"  Serving: {recipe.get('serving_suggestions', '')}\n"
                f"  Storage: {recipe.get('storage_tips', '')}\n"
            )

        return "\n".join(context_parts)

    def _generate_extra_suggestions(
        self,
        user_ingredients: List[str],
        other_recipes: List[Dict[str, Any]]
    ) -> str:
        """Generate a brief summary of other recipe alternatives."""
        if not other_recipes:
            return ""

        suggestions = []
        for recipe in other_recipes[:3]:
            match = recipe.get("match_percentage", 0)
            suggestions.append(
                f"• **{recipe['name']}** ({recipe.get('cuisine', '')}) — "
                f"{match}% match, {recipe.get('difficulty', '')} difficulty, "
                f"{recipe.get('prep_time', 0) + recipe.get('cook_time', 0)} min total"
            )

        return "\n".join(suggestions)

    def _fallback_response(self, error_msg: str) -> str:
        """
        Return a helpful fallback response when AI is unavailable.

        Args:
            error_msg: Technical error description.

        Returns:
            User-friendly fallback message.
        """
        return (
            f"⚠️ AI Service Note: {error_msg}\n\n"
            "However, I can still show you recipes based on your ingredients! "
            "The recipe cards below show the best matches from our database. "
            "Please configure your IBM Watsonx.ai credentials in the .env file "
            "for personalized AI-generated cooking instructions."
        )
