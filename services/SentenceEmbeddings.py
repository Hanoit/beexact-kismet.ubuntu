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

torch.cuda.is_available = lambda: False
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress the specific FutureWarning from transformers related to `clean_up_tokenization_spaces`
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

# Optionally, reduce Hugging Face's logging verbosity to suppress other warnings
hf_logging.set_verbosity_error()

# Assuming `model` is an instance of `SentenceTransformer`
model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")  # Ensure to use the correct model

# Initialize a lock for thread safety
model_lock = threading.Lock()

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
        # Remove punctuation (optional, since non-alphanumeric characters are already replaced)
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


def find_provider(ssid, providers_data, threshold=0.75):
    """
    Finds the most similar provider to the given SSID based on textual similarity.
    Compares the entire SSID string with each provider's name and aliases combined.
    Calculates the similarity for each provider individually.

    Args:
        ssid (str): The SSID to compare.
        providers_data (list of dict): List of provider data to compare against. Each item should be a dictionary
                                       containing 'provider_name' (str) and 'alias' (list of str) keys.
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
            # logger.warning("SSID is empty after preprocessing.")
            return None, -1, 0

        with model_lock:
            # Encode the entire SSID
            ssid_embedding = model.encode(ssid_processed, convert_to_tensor=True, show_progress_bar=False)

        best_match = None
        best_index = -1
        best_similarity = 0

        for i, provider_data in enumerate(providers_data):
            # Combine provider_name and aliases into one string for comparison
            provider_name = provider_data.provider_name
            try:
                alias_data = json.loads(provider_data.alias)
                alias_list = ' '.join([alias for alias in alias_data if alias])
            except Exception as e:
                logger.error(f"Error decoding JSON from alias provider: {e}")
                continue

            combined_text = preprocess_text(f"{provider_name} {alias_list}".strip())

            if not combined_text:
                logger.warning(f"Combined text for provider {provider_name} is empty after preprocessing. Skipping...")
                continue
            with model_lock:
                # Encode the combined provider name and aliases
                provider_embedding = model.encode(combined_text, convert_to_tensor=True, show_progress_bar=False)

            # Calculate similarity
            similarity = util.cos_sim(ssid_embedding, provider_embedding).item()

            if similarity >= threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = provider_data.provider_name
                best_index = i

        return best_match, best_index, best_similarity

    except Exception as e:
        logger.error(f"An error occurred during provider matching: {e}", exc_info=True)
        return None, -1, 0