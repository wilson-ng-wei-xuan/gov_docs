import streamlit as st
#import asyncio
from src.parsing.parsing import *
from src.retrieval.opensearch_retrieval import *
from src.utils.embed import BedRockEmbedder
import os
import tempfile

#from dotenv import load_dotenv
#load_dotenv()


def set_stage(stage):
    if stage ==1:
        st.session_state.stage = [1]
    else:
        list_stage = st.session_state.stage
        list_stage.append(stage)
        st.session_state.stage = list_stage


def examplebot():
    ## Initialize
    # region <--------- Streamlit App Header --------->
    st.title('Opensearch')
    # endregion <--------- Streamlit App Header --------->
    host =  os.getenv('OPENSEARCH_HOST')
    embedder = BedRockEmbedder()
    
    if 'stage' not in st.session_state:
        st.session_state.stage = []
    file = st.file_uploader("File Uploading", type=['pdf', 'doc', 'docx','txt', 'html', 'xlsx', 'csv', 'ppt', 'pptx'], accept_multiple_files=False, label_visibility="visible")
    bot_name= st.text_input("Select your bot.")
    if file:
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, file.name)
        with open(path, "wb") as f:
            f.write(file.getvalue())
        if file.name[-3:] == 'csv':
            docs = parse_csv(path)
        elif file.name[-4:] == 'xlsx':
            docs = parse_excel(path)
        else:
            docs = parse_doc(path, chunk_size = 2000)

        ## TO DO STORE IN OPENSEARCH
        docs['embeddings'] = embedder.create_embeddings(docs['text'])
        file_indexer = FileIndexer(host, bot_name)
        response = file_indexer.push_to_index(docs)
        st.write(response)
        
    st.divider()
    text_input = st.text_input("Insert query")
    
    st.button('Get Chunks', on_click=set_stage, args=(1,))
    chunks = []
    if text_input:
        if 1 in st.session_state.stage:
            # Retrieve chunks from vectorDB
            file_indexer = FileIndexer(host, bot_name)
            query_vector = embedder.create_embeddings(text_input)
            results = file_indexer.query(text_input,query_vector)
            for result in results:
                st.write(result['_source']['text'])
            
        st.write(f"Top 3 Chunks: ")
        for n,chunk in enumerate(chunks):
            st.write(f"Chunk {n}: ")
            st.write(chunk)

if __name__ == '__main__':
    # region <--------- Streamlit App Configuration --------->
    st.set_page_config(
        layout="centered",
        page_title="Opensearch with custom chunking",
        page_icon="🏗️"
    )

    # endregion <--------- Streamlit App Configuration --------->
    # Time to refresh page

    examplebot()

    # Display application built from launchpad message
    st.caption(
        "🛠️ Built from [LaunchPad](https://go.gov.sg/launchpad)"
        )