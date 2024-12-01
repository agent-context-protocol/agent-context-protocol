import json
import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel

# Load the JSON file
with open('external_env_details/brief_details.json', 'r') as file:
    api_data = json.load(file)

# Extract the descriptions
descriptions = [api_data[key]['Use'] for key in api_data]

# Load pre-trained model and tokenizer
model_name = 'sentence-transformers/all-MiniLM-L6-v2'  # Using DistilBERT model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)
print('Model loaded successfully.')

# Generate embeddings
def get_embeddings(texts):
    try:
        inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
        embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        return embeddings
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise

embeddings = get_embeddings(descriptions)

# Initialize FAISS index
dimension = embeddings.shape[1]  # Dimension of the embeddings
index = faiss.IndexFlatL2(dimension)

print('FAISS index initialized.')

# Add embeddings to the FAISS index
try:
    index.add(embeddings)
except Exception as e:
    print(f"Error adding embeddings to FAISS index: {e}")
    raise

# Save the FAISS index to a file
try:
    faiss.write_index(index, 'faiss_index.index')
    print("FAISS index has been saved successfully.")
except Exception as e:
    print(f"Error saving FAISS index: {e}")
    raise
