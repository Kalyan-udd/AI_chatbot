
import os


os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import streamlit as st
from models.llm import LocalMechanicalModel
from data.databases import DatabaseManipulation
from render_history import render_chat_history
from formatting import sanitize_latex_output
from rag.RAG_prompt import RAGPrompt

st.set_page_config(page_title="Kalyan'sAI", layout="centered")
st.title("GEN AI", icon=":material/domino_mask:")
st.markdown("your local AI companion.")

db = DatabaseManipulation()

all_sessions = db.get_all_sessions()
valid_session_ids = [s["session_id"] for s in all_sessions]

# 1. CRITICAL: If current_session_id is already set and exists in DB, respect it!
if "current_session_id" in st.session_state and st.session_state.current_session_id in valid_session_ids:
    if "messages" not in st.session_state:
        st.session_state.messages = db.load_messages(st.session_state.current_session_id)
else:
    # 2. Otherwise (on first boot or if ID is stale), pick the latest or create one
    if all_sessions:
        st.session_state.current_session_id = all_sessions[0]["session_id"]
        st.session_state.messages = db.load_messages(st.session_state.current_session_id)
    else:
        new_id = db.create_session("New chat")
        st.session_state.current_session_id = new_id
        st.session_state.messages = []

render_chat_history()

if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def LoadAssistant():
    return LocalMechanicalModel()

@st.cache_resource
def Rag_prompt():
    return RAGPrompt()

model = LoadAssistant()

rag_prompt = Rag_prompt()


for message in st.session_state.messages:
    with st.chat_message(message['role']):
        formatted_text = sanitize_latex_output(message['content'])
        st.markdown(formatted_text)

if prompt := st.chat_input("Ask a Mechanical engineering question (e.g., thermodynamics, beam bending)..."):
    active_id = str(st.session_state.current_session_id)
    # Check if this is the first message (i.e., title is still the default)
    current_sessions = db.get_all_sessions()
    current_sess = next((s for s in current_sessions if s["session_id"] == st.session_state.current_session_id), None)
    
    if current_sess and current_sess["title"] == "New chat":
        new_title = prompt[:30] + ("..." if len(prompt) > 30 else "")
        with db.get_connection() as conn:
            conn.execute("UPDATE sessions SET title = ? WHERE session_id = ?", (new_title, active_id))
            conn.commit()

    st.session_state.messages.append({"role":"user", "content":prompt})

    with st.chat_message("user"):
        st.markdown(prompt)
    
    db.save_message(active_id, "user", prompt)

    with st.chat_message("assistant"):
        system_instructions = rag_prompt.build_rag_message(user_prompt=prompt, threshold_distance=1.5)
        
        # Elegant placeholder for the hidden thinking state
        thinking_placeholder = st.empty()
        thinking_placeholder.caption("Thinking...")
        
        answer_container = st.empty()
        full_response = ""
        
        # Stream response from the local model
        for chunk in model.generate_response(st.session_state.messages, system_prompt=system_instructions):
            full_response += chunk
            
            # Check if thinking has concluded
            if "</think>" in full_response:
                thinking_placeholder.empty() # Clear the thinking indicator
                parts = full_response.split("</think>", 1)
                
                if len(parts) > 1:
                    final_answer = parts[1].strip()
                    answer_container.markdown(sanitize_latex_output(final_answer) + "▌")
            else:
                # Keep answer_container completely empty while reasoning occurs
                pass
                
        # Final cleanup pass ensuring content is written without think tags
        if "</think>" in full_response:
            parts = full_response.split("</think>", 1)
            response = parts[1].strip()
            answer_container.markdown(response)
        else:
            # Fallback if the model didn't use think tags at all
            thinking_placeholder.empty()
            response = full_response.strip()
            answer_container.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        db.save_message(active_id, "assistant", response)
        st.rerun()