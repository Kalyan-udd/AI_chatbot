from sentence_transformers import SentenceTransformer
import torch
from pypdf import PdfReader
from rag import MODEL
from pdf2image import convert_from_bytes
import pytesseract
import io


class EmbeddingPDFs:
    def __init__(self, model_name:str = MODEL,  device:str = "cpu") -> None:
        print(f"loading model {model_name}...")
        self.device = device
        self.model = SentenceTransformer(model_name, device=self.device)

    def extraction(self, file_bytes:bytes, file_name:str = "unknown.pdf"):
        pdf_stream = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_stream)
        documents = []
        doc_title = file_name
        if reader.metadata and reader.metadata.title:
            doc_title = reader.metadata.title.strip() or file_name
        for i, page in enumerate(reader.pages):
            text = page.extract_text()

            if not text or len(text.strip())<10:
                images = convert_from_bytes(
                    file_bytes,
                    first_page=i+1,
                    last_page=i+1,
                )
                if images:
                    text = pytesseract.image_to_string(image=images[0])
            if text and text.strip():
                documents.append({
                    "content": text,
                    "source": doc_title,
                    "page_number": i+1
                })
        if not documents:
            raise ValueError(
                f"No text could be extracted from '{file_name}'. "
                "The document may be heavily encrypted, password-protected, or blank."
            )
        return documents

    def manual_chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 150):
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
            
        return chunks

    def chunking(self, pages:list[dict], chunk_size:int = 800, overlap:int = 150):
        all_chunks = []
        for page in pages:
            page_text = page['content']
            page_source = page['source']
            page_num = page['page_number']

            text_slices = self.manual_chunk_text(page_text, chunk_size=chunk_size, overlap=overlap)

            for chunk in text_slices:
                all_chunks.append({
                    "content":chunk,
                    "metadata": {
                        "source":page_source,
                        "page_num":page_num
                    }
                })

        return all_chunks
    
    def generate_embeddings(self, chunks:list[dict], batch_size:int = 32):

        text = [chunk['content'] for chunk in chunks]
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        embeddings = self.model.encode(
            text,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True
        ).tolist()
        embedded_dataset = []
        for i, chunk in enumerate(chunks):
            embedded_dataset.append({
                "content":chunk['content'],
                "embedding": embeddings[i],
                "metadata":chunk['metadata']
            })
        return embedded_dataset