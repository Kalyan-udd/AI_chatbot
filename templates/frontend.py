import streamlit as st

pg = st.navigation(pages=[st.Page("Dashboard.py", icon=":material/empty_dashboard:"), st.Page("Prompt.py")])



pg.run()

