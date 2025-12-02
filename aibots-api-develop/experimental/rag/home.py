import streamlit as st

if __name__ == '__main__':
    # region <--------- Streamlit App Configuration --------->
    st.set_page_config(
        layout="centered",
        page_title="HomePage",
        page_icon="🏗️"
    )

    # endregion <--------- Streamlit App Configuration --------->
    # Time to refresh page

    #brewbytes()
    st.title("Bots Prototypes")

    # Display application built from launchpad message
    st.caption(
        "🛠️ Built from [LaunchPad](https://go.gov.sg/launchpad)"
        )