import chromadb
from pathlib import Path
import uuid
from rag.embedding import EmbeddingPDFs

RAG = Path(__file__).resolve().parent

class VectorDB:
    def __init__(self) -> None:
        self.chroma_client = chromadb.PersistentClient(path=f"{RAG}/vector_db")
        self.collection = self.chroma_client.get_or_create_collection(name="local_pdf_rag")

    def store_dataset_in_chroma(self,dataset:list[dict])->str:
        ids = []
        embeddings = []
        contents = []
        metadatas = []

        for i, item in enumerate(dataset):
            ids.append(str(uuid.uuid4()))
            embeddings.append(item['embedding'])
            contents.append(item['content'])
            metadatas.append(item['metadata'])

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
        return "successfully stored the data into vector database."

    def query_vector_database(self, user_query:str, embedder:EmbeddingPDFs, top_k:int=3):

        formatted_query = (
            "Instruct: Given a user question, retrieve relevant passages from the uploaded documents that answer the question.\n"
            f"Query: {user_query.strip()}"
        )

        query_embedding = embedder.model.encode(formatted_query, normalize_embeddings=True).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        retrieved_chunks = []

        documents = results.get("documents")
        metadatas = results.get("metadatas")
        distances = results.get("distances")
        if documents is None or not documents or documents[0] is None:
            return []
        if metadatas is None or not metadatas or metadatas[0] is None:
            return []
        if distances is None or not distances or distances[0] is None:
            return []
        
        for doc, meta, distance in zip(documents[0], metadatas[0], distances[0]):
            retrieved_chunks.append({
                "content": doc,
                "metadata": meta,
                "distance": distance,
            })

        return retrieved_chunks
    def delete_file_from_database(self, file_name: str) -> str:
        self.collection.delete(
            where={"source": file_name}
        )
        return f"Successfully deleted all chunks associated with '{file_name}' from ChromaDB."
    
    def get_all_stored_files(self) -> list[str]:
        data = self.collection.get(include=["metadatas"])
        metadatas = data.get("metadatas", [])
        if not metadatas:
            return []
        sources = set()
        for meta in metadatas:
            if meta and isinstance(meta, dict) and "source" in meta:
                sources.add(meta["source"])
                
        return sorted(list(sources))