import streamlit as st
from src import chat
from src import image
from src import video
import tempfile
import os

def set_stage(stage):
    if stage ==1:
        st.session_state.stage = [1]
    else:
        list_stage = st.session_state.stage
        list_stage.append(stage)
        st.session_state.stage = list_stage

def multimodal_chat():
    ## Initialize
    st.title('MultiModal Chat')

    if 'stage' not in st.session_state:
        st.session_state.stage = []
    image_base64 = []
    transcribed_text = ""
    file = st.file_uploader("File Uploading", accept_multiple_files=False, label_visibility="visible")
    if file:
        temp_dir = tempfile.mkdtemp()
        path = os.path.join(temp_dir, file.name)
        with open(path, "wb") as f:
            f.write(file.getvalue())

        if file.name[-3:] in ['jpg', 'png']:
            image_base64 = [image.encode_image(path)]
        elif file.name[-3:] == 'mp3':
            transcribed_text = video.transcribe(path)
        elif file.name[-3:] in ['mkv']:
            base64Frames, audio_path = video.process_video(path, 1)
            transcribed_text = video.transcribe(audio_path)
            video_embeddings = image.embed_images(base64Frames)
            image_base64 = image.cluster_images(video_embeddings, base64Frames)
            st.write(f"Processed video, Number of clusters {len(image_base64)}, Number of frames {len(base64Frames)}")


    message = st.text_area("Your instruction")

    st.button('Get response', on_click=set_stage, args=(1,))

    if message:
        if 1 in st.session_state.stage:
            response = chat.chat(message, image_base64, transcribed_text) 
            st.write(response)

if __name__ == '__main__':
    # region <--------- Streamlit App Configuration --------->
    st.set_page_config(
        layout="wide",
        page_title="Multimodal Chat",
        page_icon="🏗️"
    )

    # endregion <--------- Streamlit App Configuration --------->
    # Time to refresh page
    
    multimodal_chat()
    
    # Display application built from launchpad message
    st.caption(
        "🛠️ Built from [LaunchPad](https://go.gov.sg/launchpad)"
        )