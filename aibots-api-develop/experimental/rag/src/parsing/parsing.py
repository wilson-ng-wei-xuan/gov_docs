from unstructured.chunking.title import chunk_by_title
from langchain_core.documents import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai.embeddings import OpenAIEmbeddings
import umap
from sklearn.cluster import HDBSCAN 
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd
import datetime
import os
from src.utils.embed import OpenAIEmbedder

#import os
#os.environ["OCR_AGENT"]="unstructured.partition.utils.ocr_models.paddle_ocr.OCRAgentPaddle"

##### Data Tables Parsing and Chunking #####

def apply_umap(embeddings, n_neighbors=15, min_dist=0.1, n_components=2):
    """
    Apply UMAP on a list of embeddings.

    Args:
    - embeddings (list of arrays): List of embeddings to be visualized.
    - n_neighbors (int): Number of neighbors to be considered by UMAP.
    - min_dist (float): Minimum distance between points in the embedded space.
    - n_components (int): Number of dimensions in the embedded space.

    Returns:
    - array: Embedded points in the reduced space.
    """
    umap_model = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist, n_components=n_components)
    embedded_points = umap_model.fit_transform(embeddings)
    return embedded_points

def clusterchunks(embeddings, min_cluster_size = 2):
    reduced_emb = apply_umap(embeddings)

    hdb = HDBSCAN(min_cluster_size=min_cluster_size, store_centers = 'medoid')
    hdb.fit(reduced_emb)
    medoids = hdb.medoids_
    similarities = cosine_similarity(medoids, reduced_emb)
    medoids_index = np.argmax(similarities, axis=1)
    labels = hdb.labels_
    return labels, medoids_index

def parse_csv(file_path, header = 0):
    df = pd.read_csv(file_path, header = header)
    df_json = df.to_dict(orient='records')
    df_json_with_metadata = []
    filename = file_path.split('/')[-1]
    last_update_date = get_last_modified_time(file_path)
    
    for row in df_json:
        df_json_with_metadata.append(
            {
            'text': f'File: {filename}, data: {str(row)}',
            "metadata": {
                "source": filename,
                "page_number": 0,
                "last_update_date": last_update_date
            }
        }
    )

    return df_json_with_metadata

def parse_excel(file_path, header = 0):
    xls = pd.ExcelFile(file_path)
    df_json_with_metadata = []
    last_update_date = get_last_modified_time(file_path)
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(file_path, header=header, sheet_name=sheet_name)
        df_json = df.to_dict(orient='records')
        for row in df_json:
            filename = file_path.split('/')[-1]
            df_json_with_metadata.append(
                {
                'text': f'File: {filename}, Sheet: {sheet_name}, data: {str(row)}',
                "metadata": {
                    "source": filename,
                    "page_number": sheet_name,
                    "last_update_date": last_update_date
                    }
                }
            )
    return df_json_with_metadata

"""
def create_docs_from_chunks(json_structured):
    emb = OpenAIEmbedder()
    embeddings = []
    for text in json_structured:
        embeddings.append(emb.create_embeddings(text))
    cluster_labels, medoids_index = clusterchunks(embeddings)
    docs=[]
    for num, text in enumerate(json_structured):
        data_docs = Document(
            page_content = text,
            metadata = {
                'cluster': int(cluster_labels[num]),
                'medoids': int(1) if num in medoids_index else int(0)
            }
        )
        docs.append(data_docs)
    return docs
"""

######## Non datatables parsing and chunking #######

def get_last_modified_time(file_path):
    # Get the timestamp of the last modification
    timestamp = os.path.getmtime(file_path)
    
    # Convert the timestamp to a datetime object
    last_modified_time = datetime.datetime.fromtimestamp(timestamp)
    
    # Format the datetime object to the desired format
    formatted_time = last_modified_time.strftime('%Y-%m-%dT%H:%M:%S')
    
    return formatted_time

def semantic_chunker(text):
    if type(text)==list:
        text = '\n'.join(text)
    text_splitter = SemanticChunker(OpenAIEmbeddings())
    docs = text_splitter.create_documents([text])
    return docs

def chunk_document(elements, chunk_size):
    if any(obj.category == "Title" for obj in elements) and (len(elements)>3):

        elements = chunk_by_title(
            elements,
            new_after_n_chars = chunk_size,
            #overlap = int(chunk_size*.10)
            )
        documents = []
        for element in elements:
            metadata = element.metadata.to_dict()
            del metadata["languages"]
            metadata["source"] = metadata["filename"]
            documents.append(Document(page_content=element.text, metadata=metadata))
    else:
        text = '\n'.join([el.text for el in elements])
        documents = semantic_chunker(text)
    return documents

def docs_to_json(docs, filename = None, last_modified = None):
    cleaned_json_list = []
    for doc in docs:
        page_number = str(doc.metadata["page_number"] if "page_number" in list(doc.metadata.keys()) else "")
        text = f"File name: {doc.metadata['filename']}, page: {page_number}\n{doc.page_content}"
        cleaned_json = {
            'text': text,
            "metadata": {
                "source": doc.metadata['filename'] if 'filename' in doc.metadata else filename,
                "page_number": page_number,
                "last_update_date": doc.metadata['last_modified'] if 'last_modified' in doc.metadata else last_modified
            }
        }
        cleaned_json_list.append(cleaned_json)
    return cleaned_json_list

def parse_doc(file_path, chunk_size):
    if file_path[-3:] == 'txt':
        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
            documents = semantic_chunker(file_content)
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
            return None
    else:
        if file_path[-3:] == 'pdf':    
            from unstructured.partition.pdf import partition_pdf
            elements = partition_pdf(
                filename=file_path,        
                pdf_infer_table_structure=True, 
                model_name="yolox"
            )
        if file_path[-3:] == 'doc':
            from unstructured.partition.doc import partition_doc
            elements = partition_doc(filename=file_path)
        if file_path[-4:] == 'docx':
            from unstructured.partition.docx import partition_docx
            elements = partition_docx(filename=file_path)
        if file_path[-3:] == 'ppt':
            from unstructured.partition.ppt import partition_ppt
            elements = partition_ppt(filename=file_path)
        if file_path[-4:] == 'pptx':
            from unstructured.partition.pptx import partition_pptx
            elements = partition_pptx(filename=file_path)
        if file_path[-4:] == 'html':
            from unstructured.partition.html import partition_html
            elements = partition_html(url=file_path)
        elements = [el for el in elements if el.category != "Header"]
        documents = chunk_document(elements, chunk_size)
    documents = docs_to_json(documents, file_path.split('/')[-1], get_last_modified_time(file_path))
    return documents