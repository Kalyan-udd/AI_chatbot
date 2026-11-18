
from rag.embedding import EmbeddingPDFs
from rag.vector_db import VectorDB

class RAGPrompt:
    def __init__(self) -> None:
        self.vector_db = VectorDB()
        self.embedder = EmbeddingPDFs()

    def build_rag_message(self, user_prompt:str, top_k:int = 5, threshold_distance:float = 0.65):

        raw_chunks = self.vector_db.query_vector_database(
            user_query=user_prompt,
            embedder=self.embedder,
            top_k=top_k
        )

        relevent_messages = [c for c in raw_chunks if c['distance']<= threshold_distance]

        if relevent_messages:
            context_blocks = []
            for idx, chunk in enumerate(relevent_messages, start=1):
                source = chunk["metadata"].get("source", "unknown")
                page = chunk["metadata"].get("page_num", "N/A")
                context_blocks.append(
                    f"[Source {idx}: {source} | Page {idx}: {page}.]\n{chunk["content"]}"
                )

            formatted_context = "\n\n----\n\n".join(context_blocks)
        else:
            formatted_context = "No relevent documents were found in the database."

        system_prompt = (
            "Any context injected will be referring to the user only so use You, Your..."
            f"Retrieved Content: \n {formatted_context}"
        )

        return system_prompt