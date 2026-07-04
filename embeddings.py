"""
=============================================================
Recipe Preparation Agent - Embeddings Module
=============================================================
Handles sentence embeddings using Sentence Transformers
(all-MiniLM-L6-v2) for semantic similarity search.
=============================================================
"""

import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from config import Config

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """
    Manages text embedding generation using Sentence Transformers.
    Uses all-MiniLM-L6-v2 for efficient, high-quality embeddings.
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        """Singleton pattern to avoid reloading the model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.model_name = Config.EMBEDDING_MODEL
        self.model = None
        self._load_model()
        self._initialized = True

    def _load_model(self):
        """Load the Sentence Transformer model."""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Embedding model load failed: {e}")

    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text string.

        Args:
            text: Input text to embed.

        Returns:
            numpy array of shape (embedding_dim,)
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0]

    def embed_texts(self, texts: list) -> np.ndarray:
        """
        Generate embeddings for a list of texts (batch processing).

        Args:
            texts: List of text strings to embed.

        Returns:
            numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            raise ValueError("Cannot embed empty list.")
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings

    def embed_recipe(self, recipe: dict) -> np.ndarray:
        """
        Generate a combined embedding for a recipe dict
        by combining key recipe fields into a rich text representation.

        Args:
            recipe: Recipe dictionary with standard fields.

        Returns:
            numpy array embedding
        """
        # Combine relevant fields for a rich semantic representation
        ingredients_text = ", ".join(recipe.get("ingredients", []))
        instructions_text = " ".join(recipe.get("instructions", []))
        tags_text = ", ".join(recipe.get("tags", []))
        diet_text = ", ".join(recipe.get("diet", []))

        combined = (
            f"Recipe: {recipe.get('name', '')}. "
            f"Cuisine: {recipe.get('cuisine', '')}. "
            f"Diet: {diet_text}. "
            f"Ingredients: {ingredients_text}. "
            f"Difficulty: {recipe.get('difficulty', '')}. "
            f"Tags: {tags_text}. "
            f"Instructions: {instructions_text[:300]}"
        )
        return self.embed_text(combined)

    def embed_query(self, ingredients: list, cuisine: str = "", diet: str = "") -> np.ndarray:
        """
        Generate embedding for a user query based on their available ingredients.

        Args:
            ingredients: List of available ingredients.
            cuisine: Preferred cuisine (optional).
            diet: Dietary preference (optional).

        Returns:
            numpy array embedding
        """
        query = f"Recipe using ingredients: {', '.join(ingredients)}."
        if cuisine:
            query += f" Cuisine: {cuisine}."
        if diet:
            query += f" Dietary preference: {diet}."
        return self.embed_text(query)

    @property
    def embedding_dim(self) -> int:
        """Return the embedding dimension size."""
        if self.model is None:
            return 384  # Default for all-MiniLM-L6-v2
        return self.model.get_sentence_embedding_dimension()
