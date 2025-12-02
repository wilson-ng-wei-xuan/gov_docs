from sklearn.cluster import HDBSCAN
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ClusterArticles:
    def __init__(self, min_cluster_size=2):
        self.hdb = HDBSCAN(min_cluster_size=min_cluster_size, store_centers = 'medoid')
        self.processed =None
         
    def cluster_articles(self, vector_array):
            self.hdb.fit(vector_array)
            medoids = self.hdb.medoids_
            similarities = cosine_similarity(medoids, vector_array)
            most_similar_indices = np.argmax(similarities, axis=1)
            labels = self.hdb.labels_
            return labels, most_similar_indices
    
    def run_pipeline(self, df, vector_column = 'embeddings_ada'):
        if vector_column in df.columns:
            filterd_df = df[df[vector_column].str.len()>0]
            vector_array = np.array([np.array(x) for x in filterd_df[vector_column].values])
            
            # Cluster similar articles
            labels, most_similar_indices = self.cluster_articles(vector_array)

            # Annote dataframe
            df['label'] = labels
            df['rep_article'] = 0
            df.loc[most_similar_indices, 'rep_article']= 1
            self.processed = True

            return df