"""
=============================================================
Recipe Preparation Agent - RAG (Retrieval-Augmented Generation)
=============================================================
Implements the RAG pipeline:
  1. Load recipe JSON datasets
  2. Generate embeddings using Sentence Transformers
  3. Store/retrieve from FAISS vector index
  4. Retrieve top-K matching recipes for a user query
=============================================================
"""

import os
import json
import logging
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional

from config import Config
from embeddings import EmbeddingEngine

logger = logging.getLogger(__name__)


class RecipeRAG:
    """
    RAG pipeline for recipe retrieval using FAISS vector store.
    Loads recipe data, embeds it, and retrieves semantically
    similar recipes based on user ingredient queries.
    """

    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.faiss_index = None
        self.recipe_metadata: List[Dict[str, Any]] = []
        self.index_path = Config.FAISS_INDEX_PATH
        self.metadata_path = Config.RECIPE_METADATA_PATH
        self.recipes_dir = Config.RECIPES_DIR
        self.top_k = Config.TOP_K_RESULTS

        # Initialize: load or build the FAISS index
        self._initialize()

    # -------------------------
    # Initialization
    # -------------------------

    def _initialize(self):
        """Initialize RAG: load existing index or build new one."""
        if self._index_exists():
            logger.info("Loading existing FAISS index...")
            self._load_index()
        else:
            logger.info("Building new FAISS index from recipe data...")
            recipes = self._load_all_recipes()
            if recipes:
                self._build_index(recipes)
            else:
                logger.warning("No recipes found to build index.")

    def _index_exists(self) -> bool:
        """Check if a saved FAISS index and metadata exist and are up-to-date."""
        if not (os.path.exists(self.index_path) and os.path.exists(self.metadata_path)):
            return False

        if self._is_index_stale():
            logger.info("Existing FAISS index is stale compared to recipe files.")
            return False

        return True

    def _is_index_stale(self) -> bool:
        """Return True when recipe files have changed since the index was built."""
        try:
            index_mtime = os.path.getmtime(self.index_path)
            metadata_mtime = os.path.getmtime(self.metadata_path)
            last_index_mtime = max(index_mtime, metadata_mtime)

            recipe_files = self._get_recipe_files()
            if not recipe_files:
                return False

            latest_recipe_mtime = max(
                os.path.getmtime(os.path.join(self.recipes_dir, filename))
                for filename in recipe_files
            )
            return latest_recipe_mtime > last_index_mtime
        except OSError as e:
            logger.warning(f"Could not check recipe file timestamps: {e}")
            return False

    def _get_recipe_files(self) -> List[str]:
        return sorted(
            f for f in os.listdir(self.recipes_dir)
            if f.lower().endswith(".json")
        )

    # -------------------------
    # Recipe Loading
    # -------------------------

    def _load_all_recipes(self) -> List[Dict[str, Any]]:
        """
        Load all recipe JSON files from the recipes directory.

        Returns:
            Combined list of all recipe dicts.
        """
        all_recipes = []
        recipe_files = sorted(
            f for f in os.listdir(self.recipes_dir)
            if f.lower().endswith(".json")
        )

        if not recipe_files:
            logger.warning(f"No recipe JSON files found in {self.recipes_dir}")

        for filename in recipe_files:
            filepath = os.path.join(self.recipes_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    recipes = json.load(f)
                    if isinstance(recipes, list):
                        all_recipes.extend(recipes)
                        logger.info(f"Loaded {len(recipes)} recipes from {filename}")
                    else:
                        logger.warning(f"Skipped {filename}: JSON root is not a list")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading {filename}: {e}")

        logger.info(f"Total recipes loaded: {len(all_recipes)}")
        return all_recipes

    def reload_recipes(self):
        """Force reload and rebuild the FAISS index from recipe files."""
        logger.info("Reloading all recipes and rebuilding FAISS index...")
        recipes = self._load_all_recipes()
        if recipes:
            self._build_index(recipes)
            logger.info("FAISS index rebuilt successfully.")
        return len(recipes)

    # -------------------------
    # FAISS Index Operations
    # -------------------------

    def _build_index(self, recipes: List[Dict[str, Any]]):
        """
        Build a FAISS index from recipe embeddings.

        Args:
            recipes: List of recipe dictionaries.
        """
        logger.info(f"Generating embeddings for {len(recipes)} recipes...")

        # Generate rich text representations for embedding
        texts = []
        for recipe in recipes:
            ingredients_text = ", ".join(recipe.get("ingredients", []))
            instructions_text = " ".join(recipe.get("instructions", []))[:200]
            diet_text = ", ".join(recipe.get("diet", []))
            tags_text = ", ".join(recipe.get("tags", []))
            text = (
                f"Recipe: {recipe.get('name', '')}. "
                f"Cuisine: {recipe.get('cuisine', '')}. "
                f"Dietary: {diet_text}. "
                f"Ingredients: {ingredients_text}. "
                f"Difficulty: {recipe.get('difficulty', '')}. "
                f"Tags: {tags_text}. "
                f"Summary: {instructions_text}"
            )
            texts.append(text)

        # Generate embeddings in batch
        embeddings = self.embedding_engine.embed_texts(texts)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Build FAISS IndexFlatIP (Inner Product = cosine after normalization)
        embedding_dim = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(embedding_dim)
        self.faiss_index.add(embeddings.astype(np.float32))

        # Store metadata
        self.recipe_metadata = recipes

        # Save to disk
        self._save_index()
        logger.info(f"FAISS index built with {self.faiss_index.ntotal} vectors.")

    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            faiss.write_index(self.faiss_index, self.index_path)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.recipe_metadata, f, ensure_ascii=False, indent=2)
            logger.info("FAISS index and metadata saved to disk.")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _load_index(self):
        """Load FAISS index and metadata from disk."""
        try:
            self.faiss_index = faiss.read_index(self.index_path)
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.recipe_metadata = json.load(f)
            logger.info(f"FAISS index loaded: {self.faiss_index.ntotal} vectors, {len(self.recipe_metadata)} recipes.")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            # If loading fails, rebuild from scratch
            recipes = self._load_all_recipes()
            if recipes:
                self._build_index(recipes)

    # -------------------------
    # Retrieval
    # -------------------------

    def retrieve_recipes(
        self,
        ingredients: List[str],
        cuisine: str = "any",
        diet: str = "any",
        difficulty: str = "any",
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant recipes for given ingredients.

        RAG Pipeline:
        1. Generate embedding for user query
        2. Search FAISS index for nearest neighbors
        3. Apply metadata filters (cuisine, diet, difficulty)
        4. Return top-K recipes with match info

        Args:
            ingredients: List of available ingredients.
            cuisine: Preferred cuisine filter.
            diet: Dietary preference filter.
            difficulty: Difficulty filter.
            top_k: Number of results to return.

        Returns:
            List of matching recipe dicts with match percentages.
        """
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            logger.warning("FAISS index is empty. Rebuilding...")
            self.reload_recipes()
            if self.faiss_index is None:
                return []

        k = top_k or self.top_k

        # Step 1: Generate query embedding
        query_embedding = self.embedding_engine.embed_query(ingredients, cuisine, diet)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_embedding)

        # Step 2: Search FAISS — retrieve more than needed to allow filtering
        search_k = min(k * 4, self.faiss_index.ntotal)
        scores, indices = self.faiss_index.search(query_embedding, search_k)

        # Step 3: Collect results with metadata filters
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.recipe_metadata):
                continue

            recipe = self.recipe_metadata[idx]

            # Apply cuisine filter
            if cuisine and cuisine.lower() != "any":
                if recipe.get("cuisine", "").lower() != cuisine.lower():
                    continue

            # Apply diet filter
            if diet and diet.lower() != "any":
                recipe_diets = [d.lower() for d in recipe.get("diet", [])]
                recipe_ingredients = [i.lower() for i in recipe.get("ingredients", [])]

                if diet.lower() == "vegetarian":
                    # Treat vegetarian as excluding egg-based recipes in this app.
                    if any(egg in ing for ing in recipe_ingredients for egg in ["egg", "eggs"]):
                        continue
                    if "non vegetarian" in recipe_diets:
                        continue
                elif diet.lower() == "vegan":
                    # Exclude animal-derived ingredients from vegan results.
                    animal_terms = ["egg", "eggs", "milk", "cheese", "butter", "yogurt", "cream", "honey", "gelatin"]
                    if any(term in ing for ing in recipe_ingredients for term in animal_terms):
                        continue
                elif diet.lower() not in recipe_diets:
                    continue

            # Apply difficulty filter
            if difficulty and difficulty.lower() != "any":
                if recipe.get("difficulty", "").lower() != difficulty.lower():
                    continue

            # Calculate ingredient match
            recipe_ings = [i.lower() for i in recipe.get("ingredients", [])]
            user_ings = [i.lower() for i in ingredients]
            matched = []
            missing = []
            for r_ing in recipe_ings:
                if any(u_ing in r_ing or r_ing in u_ing for u_ing in user_ings):
                    matched.append(r_ing)
                else:
                    missing.append(r_ing)

            match_pct = (len(matched) / len(recipe_ings) * 100) if recipe_ings else 0

            results.append({
                **recipe,
                "similarity_score": float(score),
                "match_percentage": round(match_pct, 1),
                "matched_ingredients": matched,
                "missing_ingredients": missing,
                "total_time": recipe.get("prep_time", 0) + recipe.get("cook_time", 0)
            })

            if len(results) >= k:
                break

        # Sort by combined score (similarity + ingredient match)
        results.sort(
            key=lambda r: (r["match_percentage"] * 0.5 + r["similarity_score"] * 50),
            reverse=True
        )

        logger.info(f"RAG retrieved {len(results)} recipes for query: {ingredients}")
        return results

    def get_recipe_by_id(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific recipe by its ID."""
        for recipe in self.recipe_metadata:
            if recipe.get("id") == recipe_id:
                return recipe
        return None

    def get_all_recipes(self) -> List[Dict[str, Any]]:
        """Return all recipes in the knowledge base."""
        return self.recipe_metadata

    def get_recipes_by_cuisine(self, cuisine: str) -> List[Dict[str, Any]]:
        """Filter recipes by cuisine."""
        return [
            r for r in self.recipe_metadata
            if r.get("cuisine", "").lower() == cuisine.lower()
        ]

    def get_popular_recipes(self, limit: int = 6) -> List[Dict[str, Any]]:
        """Return a curated set of popular recipes for the homepage."""
        # Return a mix of cuisines and difficulties
        popular_ids = [
            "indian_001", "italian_001", "chinese_001",
            "indian_003", "italian_002", "breakfast_001"
        ]
        popular = []
        for pid in popular_ids:
            r = self.get_recipe_by_id(pid)
            if r:
                popular.append(r)

        # Fill with any remaining if needed
        if len(popular) < limit:
            for r in self.recipe_metadata:
                if r["id"] not in popular_ids:
                    popular.append(r)
                if len(popular) >= limit:
                    break

        return popular[:limit]

    def get_leftover_suggestions(self, leftover_ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Suggest recipes for using leftover ingredients.

        Args:
            leftover_ingredients: List of leftover ingredient names.

        Returns:
            Top matching recipes using those leftovers.
        """
        return self.retrieve_recipes(leftover_ingredients, top_k=3)

    @property
    def total_recipes(self) -> int:
        """Return total number of recipes in the knowledge base."""
        return len(self.recipe_metadata)
