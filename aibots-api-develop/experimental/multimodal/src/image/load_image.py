import base64
from PIL import Image
from io import BytesIO
from torchvision import models, transforms
from transformers import ViTModel, ViTFeatureExtractor
from sklearn.cluster import KMeans
import base64
import numpy as np

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def decode_base64_frame(base64_str):
    image_data = base64.b64decode(base64_str)
    image = Image.open(BytesIO(image_data))
    return image

def preprocess_image(image):
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return preprocess(image).unsqueeze(0) 

def embed_features(image, feature_extractor, vit_model):
    inputs = feature_extractor(images=image, return_tensors="pt")
    outputs = vit_model(**inputs)
    embeddings = outputs.last_hidden_state 

    return embeddings

def embed_images(base64Frames):
    video_embeddings = []
    feature_extractor = ViTFeatureExtractor.from_pretrained('google/vit-base-patch16-224-in21k')
    vit_model = ViTModel.from_pretrained('google/vit-base-patch16-224-in21k')
    for base64_frame in base64Frames:
        image = decode_base64_frame(base64_frame)
        preprocessed_image = preprocess_image(image)

        embeddings = embed_features(image, feature_extractor, vit_model)
        video_embeddings.append(embeddings.reshape(-1).detach().numpy())
    return np.array(video_embeddings)

def cluster_images(video_embeddings, base64Frames):
    kmeans =  KMeans(n_clusters=10, random_state=42)
    kmeans.fit(video_embeddings)

    # Find cluster centres
    cluster_centers = kmeans.cluster_centers_
    distances = np.linalg.norm(video_embeddings[:, np.newaxis] - cluster_centers, axis=2)

    # Find the index of the closest point to each cluster center
    closest_indices = np.argmin(distances, axis=0)

    return [base64Frames[idx] for idx in closest_indices]

