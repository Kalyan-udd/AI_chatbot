import streamlit as st
from data.databases import DatabaseManipulation

db = DatabaseManipulation()

def render_chat_history():
    with st.sidebar:
        st.title("History")

        if st.button("New Chat", use_container_width=True):
            new_chat = db.create_session("New chat")
            st.session_state.current_session_id = new_chat
            st.session_state.messages = []
            st.rerun()

        st.divider()

        all_sessions = db.get_all_sessions()
        
        if not all_sessions:
            st.caption("No chat history yet.")
            return
        
        for sess in all_sessions:
            is_active = sess["session_id"] == st.session_state.get("current_session_id")
            
            col1, col2 = st.columns([0.8, 0.2])
            
            with col1:
                button_type = "primary" if is_active else "secondary"
                if st.button(sess["title"], key=f"switch_{sess['session_id']}", type=button_type, use_container_width=True):
                    st.session_state.current_session_id = sess["session_id"]
                    st.session_state.messages = db.load_messages(sess["session_id"])
                    st.rerun()
                    
            with col2:
                if st.button(":material/delete:",key=f"del_{sess['session_id']}", use_container_width=True):
                    db.delete_session(sess["session_id"])
                    
                    remaining_sessions = db.get_all_sessions()
                    if remaining_sessions:
                        st.session_state.current_session_id = remaining_sessions[0]["session_id"]
                        st.session_state.messages = db.load_messages(st.session_state.current_session_id)
                    else:
                        # INSTANT FALLBACK: Create a fresh session if all were deleted
                        new_session_id = db.create_session("New chat")
                        st.session_state.current_session_id = new_session_id
                        st.session_state.messages = []
                    st.rerun()