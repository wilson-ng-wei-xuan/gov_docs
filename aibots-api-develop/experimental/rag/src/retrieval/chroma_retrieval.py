from langchain_openai.embeddings import OpenAIEmbeddings

def store_structured_embeddings(documents):
    from langchain_community.vectorstores import Chroma
    embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")
    db = Chroma.from_documents(documents, embedding_function)
    return db

def retrieve_from_vectordb(db, query, k, trend = True):
    if trend:
        return db.get(where={'medoids':1})['documents']
    else:
        results = db.similarity_search(query, k=k)
        return [doc.page_content for doc in results]