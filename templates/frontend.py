import streamlit as st

pg = st.navigation([st.Page("Dashboard.py"), st.Page("Document_upload.py", title="Upload Files")])

pg.run()