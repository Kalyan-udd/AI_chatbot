import streamlit as st
from models.llm import LocalMechanicalModel

st.set_page_config(page_title="Kalyan'sAI", layout="centered")
st.title("Kalyan's-AI", icon=":material/domino_mask:")
st.markdown("your local AI companion.")


if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def LoadAssistant():
    return LocalMechanicalModel()

model = LoadAssistant()



for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input("Ask a Mechanical engineering question (e.g., thermodynamics, beam bending)..."):
    st.session_state.messages.append({"role":"user", "content":prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        system_instructions = ("")
        
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
                    answer_container.markdown(final_answer + "▌")
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