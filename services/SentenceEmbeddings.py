import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import json
import warnings
from transformers import logging as hf_logging
import re
import string
import threading
import logging
import torch
from sentence_transformers import SentenceTransformer, util
from functools import lru_cache
import numpy as np

torch.cuda.is_available = lambda: False
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress the specific FutureWarning from transformers related to `clean_up_tokenization_spaces`
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# Optionally, reduce Hugging Face's logging verbosity to suppress other warnings
hf_logging.set_verbosity_error()

# Global model instance - loaded once
_model = None
_model_lock = threading.Lock()


def get_model():
    """Get or create the global model instance."""
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                logger.info("Loading SentenceTransformer model...")
                _model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
                logger.info("SentenceTransformer model loaded successfully")
    return _model


# Cache for provider embeddings
_provider_embeddings_cache = {}
_provider_cache_lock = threading.Lock()


def preprocess_text(text, non_alphanumeric=False, remove_digits=False):
    """
    Preprocesses the input text by:
    1. Converting to lowercase.
    2. Replacing non-alphanumeric characters (e.g., underscores, hyphens) with spaces.
    3. Removing digits.
    4. Removing punctuation.

    Args:
        text (str): The text to preprocess.

    Returns:
        str: A preprocessed string.
    """
    if not is_mac_address(text):
        # Convert to lowercase
        text = text.lower()
        # Replace non-alphanumeric characters (e.g., underscores, hyphens) with spaces
        if non_alphanumeric:
            text = re.sub(r'[\W_]+', ' ', text)
        # Remove digits
        if remove_digits:
            text = re.sub(r'\d+', '', text)
        # Remove punctuation (optional, since non_alphanumeric characters are already replaced)
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.strip()
    else:
        return None


def is_mac_address(text):
    """
    Checks if the given text is a MAC address.

    Args:
        text (str): The text to check.

    Returns:
        bool: True if the text matches the MAC address pattern, False otherwise.
    """
    mac_regex = r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
    return re.match(mac_regex, text) is not None


def get_provider_embeddings(providers_data):
    """
    Get or create embeddings for all providers. Uses caching for performance.
    
    Args:
        providers_data: List of provider data objects
        
    Returns:
        tuple: (embeddings_tensor, provider_names_list)
    """
    global _provider_embeddings_cache
    
    # Create a cache key based on provider data
    cache_key = hash(tuple(sorted([p.provider_name for p in providers_data])))
    
    with _provider_cache_lock:
        if cache_key in _provider_embeddings_cache:
            return _provider_embeddings_cache[cache_key]
    
    # Process all providers at once
    provider_texts = []
    provider_names = []
    
    for provider_data in providers_data:
        provider_name = provider_data.provider_name
        try:
            alias_data = json.loads(provider_data.alias)
            alias_list = ' '.join([alias for alias in alias_data if alias])
        except Exception as e:
            logger.error(f"Error decoding JSON from alias provider: {e}")
            alias_list = ""
        
        combined_text = preprocess_text(f"{provider_name} {alias_list}".strip())
        if combined_text:
            provider_texts.append(combined_text)
            provider_names.append(provider_name)
    
    if not provider_texts:
        return torch.empty(0, 384), []
    
    # Encode all providers in a single batch
    model = get_model()
    with _model_lock:
        embeddings = model.encode(provider_texts, convert_to_tensor=True, show_progress_bar=False)
    
    result = (embeddings, provider_names)
    
    # Cache the result
    with _provider_cache_lock:
        _provider_embeddings_cache[cache_key] = result
    
    return result


def find_provider(ssid, providers_data, threshold=0.75):
    """
    Finds the most similar provider to the given SSID based on textual similarity.
    Optimized version that uses batch processing and caching.

    Args:
        ssid (str): The SSID to compare.
        providers_data (list of dict): List of provider data to compare against.
        threshold (float): The similarity threshold to determine if a match is found.

    Returns:
        tuple: A tuple containing:
            - The most similar provider (str) or None if no match is found.
            - The index of the most similar provider (int) or -1 if no match is found.
            - The similarity score (float) of the most similar provider or 0 if no match is found.
    """

    try:
        # Preprocess the SSID
        ssid_processed = preprocess_text(ssid, non_alphanumeric=True, remove_digits=True)
        if not ssid_processed:
            return None, -1, 0

        # Get provider embeddings (cached)
        provider_embeddings, provider_names = get_provider_embeddings(providers_data)
        
        if len(provider_embeddings) == 0:
            return None, -1, 0

        # Encode the SSID
        model = get_model()
        with _model_lock:
            ssid_embedding = model.encode([ssid_processed], convert_to_tensor=True, show_progress_bar=False)

        # Calculate similarities for all providers at once
        similarities = util.cos_sim(ssid_embedding, provider_embeddings).squeeze()
        
        # Find the best match
        best_similarity, best_index = torch.max(similarities, dim=0)
        best_similarity = best_similarity.item()
        best_index = best_index.item()
        
        if best_similarity >= threshold:
            best_match = provider_names[best_index]
            return best_match, best_index, best_similarity
        else:
            return None, -1, 0

    except Exception as e:
        logger.error(f"An error occurred during provider matching: {e}", exc_info=True)
        return None, -1, 0


def clear_cache():
    """Clear the provider embeddings cache."""
    global _provider_embeddings_cache
    with _provider_cache_lock:
        _provider_embeddings_cache.clear()
