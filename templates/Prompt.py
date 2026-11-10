import streamlit as st

col1, col2, col3 = st.columns(3)
col1.metric("Revenue", "$12K", "8%")
col2.metric("Users", "1,204", "12%")
col3.metric("Latency", "42ms", "-3%")


left, right = st.columns([2, 1])
left.write("This column is twice as wide.")
right.write("This column is narrower.")


grid = st.grid(4)
with grid.cell(column_span="all"):
    st.markdown("**Featured**")
    st.caption("Trailing 30 days")
grid.metric("Revenue", "$1.2M", "+8%")
grid.metric("Pipeline", "$4.8M", "+12%")
grid.metric("Retention", "96%", "-0.4%")
grid.metric("Retention", "96%", "-0.4%")