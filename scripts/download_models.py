#!/usr/bin/env python3
"""
Script to pre-download FastEmbed models for Docker containers.
This reduces startup time by downloading models during image build.
"""

import os
from fastembed import TextEmbedding

def download_fastembed_models():
    """Download FastEmbed models specified in config."""
    models_to_download = [
        "BAAI/bge-small-en-v1.5",
        "BAAI/bge-base-en-v1.5",
        "sentence-transformers/all-MiniLM-L6-v2"
    ]
    
    for model_name in models_to_download:
        print(f"Downloading model: {model_name}")
        try:
            # This will download and cache the model
            embedding_model = TextEmbedding(model_name=model_name)
            print(f"✓ Successfully downloaded: {model_name}")
        except Exception as e:
            print(f"✗ Failed to download {model_name}: {e}")

if __name__ == "__main__":
    download_fastembed_models()