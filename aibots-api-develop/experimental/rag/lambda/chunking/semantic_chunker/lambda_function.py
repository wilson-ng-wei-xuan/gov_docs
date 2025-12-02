from langchain_community.embeddings import BedrockEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import json

def semantic_chunker(text):
    """
    returns:
        docs (list of langchain object): chunks
    """
    embeddings = BedrockEmbeddings(
        region_name="ap-southeast-1",
        model_id = 'cohere.embed-english-v3'
    )
    if type(text)==list:
        text = '\n'.join(text)
    text_splitter = SemanticChunker(embeddings)
    docs = text_splitter.create_documents([text])
    list_of_chunks = [doc.page_content for doc in docs]
    return list_of_chunks

def lambda_handler(event, context):
    
    # Event body is a list of chunks with metadata
    documents = event["body"]
    df_json_with_metadata = []
    if len(documents)<=5:
        for doc in documents:
            # For each existing chunk, re-chunk based on semantic chunker
            list_of_text = doc["text"]
            chunks = semantic_chunker(''.join(list_of_text))

            # Re-populate the data with appropriate chunks
            for chunk in chunks:
                doc["text"] = chunk
                df_json_with_metadata.append(doc)
    
        return {
            'statusCode': 200,
            'body': json.dumps([df_json_with_metadata]), # TODO
            'headers': {
                'Content-Type': 'application/json',
            }
        }
