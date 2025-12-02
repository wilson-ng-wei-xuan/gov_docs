import streamlit as st
#import asyncio
from src.utils.s3_functions import *
from src.retrieval.bedrock_retrieval import * 

def set_stage(stage):
    if stage ==1:
        st.session_state.stage = [1]
    else:
        list_stage = st.session_state.stage
        list_stage.append(stage)
        st.session_state.stage = list_stage
   

def st_bedrock():
    kbId = "JDXZVLLGLX"
    if 'stage' not in st.session_state:
        st.session_state.stage = []
    ## Initialize
    # region <--------- Streamlit App Header --------->
    st.title('Bedrock RAG')
    # endregion <--------- Streamlit App Header --------->
    # Display disclaimer message (Edit where necessary)
    st.warning("""**Please read the following before proceeding:**
   
• This application is currently in **Beta version** and supports data classified up to **Restricted and Sensitive (Normal)**. 
        
• This application is under active testing and your activites will be logged to improve your experience.
        
• By using this application, you acknowledge that you recognise the possibility of AI generating inaccurate or wrong responses, and you take full responsibility over how you use the generated output.""")
    
    data_source_ids = get_data_source_id(kbId)
    data_source_mapping = {}
    bots = []
    for data_source in data_source_ids:
        data_source_uri = get_data_source_uri(kbId, data_source) 
        bot = data_source_uri.split("/")[-2]
        data_source_mapping[bot] = data_source
        s3_bucket_folder = '/'.join(data_source_uri.split("/")[:-2])
        bots.append(bot)

    bot_name_selected = st.selectbox("Select your bot.", bots)

    file = st.file_uploader("File Uploading", type=['pdf', 'doc', 'docx','txt', 'md', 'html'], accept_multiple_files=False, label_visibility="visible")
    
    data_source_uri = s3_bucket_folder + "/" + bot_name_selected

    if file:
        try:
            upload_to_s3(file, data_source_uri)
            st.write("Uploaded file.")
            start_ingestion_job(kbId, data_source_mapping[bot])
        except:
            st.write("Upload fail")

    s3_files = list_files_bucket(data_source_uri)

    st.write("Files in s3:")
    for file in s3_files:
        st.write(file)
    
    st.divider()
    text_input = st.text_input("Insert query")
    st.button('Get Chunks', on_click=set_stage, args=(1,))
    if text_input:
        if 1 in st.session_state.stage:
            context = retrieve(text_input, kbId, data_source_uri, numberOfResults=3)
            st.subheader("Returned context")
            for content in context["retrievalResults"]:
                st.write(content['content']['text'])
                st.divider()
            with st.expander(f"Retrieved content"):
                st.write(f"{context}")

if __name__ == '__main__':
    # region <--------- Streamlit App Configuration --------->
    st.set_page_config(
        layout="centered",
        page_title="Tablebot",
        page_icon="🏗️"
    )

    # endregion <--------- Streamlit App Configuration --------->
    # Time to refresh page

    st_bedrock()

    # Display application built from launchpad message
    st.caption(
        "🛠️ Built from [LaunchPad](https://go.gov.sg/launchpad)"
        )