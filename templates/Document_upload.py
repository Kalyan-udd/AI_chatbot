import streamlit as st
from rag.embedding import EmbeddingPDFs
from rag.vector_db import VectorDB

st.set_page_config(page_title="Local RAG File processor", layout="centered")

st.title(" Local File embedding pipeline.", icon=":material/files:")
st.write(" Upload a PDF to process it entirely in memory, chunk it smartly, and generate 1024-dimensioned embeddings.")

@st.cache_resource
def Initialising_model():
    return EmbeddingPDFs()

@st.cache_resource
def Initialising_vector_db():
    return VectorDB()

vector_db = Initialising_vector_db()

st.sidebar.title("📁 Document Manager")
st.sidebar.write("Manage your indexed documents here.")

stored_files = vector_db.get_all_stored_files()

if stored_files:
    st.sidebar.markdown(f"**Indexed Files ({len(stored_files)}):**")
    for file_name in stored_files:
        # Create a layout with columns for file name and delete button
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.text(file_name)
        with col2:
            # Unique key ensures button clicks don't conflict across files
            if st.button("🗑️", key=f"del_{file_name}", help=f"Delete {file_name}"):
                vector_db.delete_file_from_database(file_name)
                st.sidebar.success(f"Deleted!")
                st.rerun()  # Refresh app to update the sidebar list immediately
else:
    st.sidebar.info("No files stored in the database yet.")

with st.spinner("Loading embedding model into memory...."):
    embedder = Initialising_model()
st.success("embedding model and database ready!")



uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file is not None:
    pdf_name = uploaded_file.name
    pdf_bytes = uploaded_file.read()

    if st.button("Upload"):
        with st.spinner("extracting text, chunking, and generating embeddings and saving to vector database."):

            pages = embedder.extraction(pdf_bytes, file_name=pdf_name)
            chunks = embedder.chunking(pages=pages)
            dataset = embedder.generate_embeddings(chunks=chunks)
            status_message = vector_db.store_dataset_in_chroma(dataset=dataset)

        st.success("upload successful")
        st.rerun()

        st.subheader("🔍 Preview First Chunk & Metadata")
        st.json({
            "content": dataset[0]["content"][:300] + "...",  # Truncate for display
            "metadata": dataset[0]["metadata"],
            "embedding_dimensions": len(dataset[0]),
            "vector_sample": dataset[0] # Show first 5 dimensions
        })
        st.session_state["embedded_dataset"] = dataset

st.divider()

st.subheader("🧠 Semantic Search over Vector Database")
st.write("Ask a question to find the most relevant chunks stored in your ChromaDB collection.")

user_query = st.text_input("Enter your query or question:")

if user_query:
    with st.spinner("Searching vector database..."):
        # Query your VectorDB class
        results = vector_db.query_vector_database(user_query, embedder, top_k=3)
        
    if results:
        st.success(f"Found {len(results)} relevant chunks:")
        for i, res in enumerate(results):
            # Format metadata details safely
            source_file = res['metadata'].get('source', 'Unknown File')
            page_num = res['metadata'].get('page_num') or res['metadata'].get('page_number', 'N/A')
            distance_score = res['distance']
            
            with st.expander(f"Result {i+1} | Source: {source_file} (Page {page_num}) | Distance: {distance_score:.4f}"):
                st.write(res["content"])
    else:
        st.warning("No relevant chunks found in the database. Try uploading a PDF or refining your query.")