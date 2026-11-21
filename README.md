# Local AI Chatbot with RAG

A fully local, privacy-focused AI chatbot built from scratch using Hugging Face `transformers`, **ChromaDB**, and **Streamlit**. Everything runs directly on your machine—no external servers, cloud APIs, or heavy orchestration frameworks like LangChain required.

## Architecture & Tech Stack

- **LLM (Text Generation):** `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`
- **Embedding Model (RAG):** `Qwen/Qwen3-Embedding-0.6B`
- **Vector Database:** ChromaDB (local persistent storage)
- **Inference Engine:** Pure PyTorch & Hugging Face `transformers`
- **User Interface:** Streamlit

## Prerequisites

- Python 3.10 or higher
- A Hugging Face account and Access Token (free) to download the model weights on first run

## Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/Kalyan-udd/AI_chatbot.git](https://github.com/Kalyan-udd/AI_chatbot.git)
   cd your-repo-name
   ```

2. **Install dependencies:**
   All required libraries are listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

## Setting Up Hugging Face Authentication (Beginner-Friendly)

To download the models from Hugging Face automatically, you need to save your Hugging Face token as an environment variable (`HF_TOKEN`). You do not need to write any code to do this.

### Step 1: Get Your Token
1. Log in to [huggingface.co](https://huggingface.co/).
2. Click your profile picture (top right) → **Settings** → **Access Tokens**.
3. Click **Create new token**, select **Read** access, give it a name, and copy the token (it starts with `hf_...`).

### Step 2: Add the Token to Your System

#### Option A: Windows (No Coding Required)
1. Press the **Windows Key**, type **Environment Variables**, and click **"Edit the system environment variables"**.
2. Click the **Environment Variables...** button near the bottom right.
3. Under **User variables** (the top box), click **New...**.
4. Set **Variable name** to `HF_TOKEN` and paste your `hf_...` token into **Variable value**.
5. Click **OK** on all windows, then restart your terminal.

#### Option B: Using a `.env` File (Windows / macOS / Linux)
1. Open the project folder in your file explorer or text editor (like Notepad or VS Code).
2. Create a new plain text file named exactly `.env` (with the dot at the front and no `.txt` extension).
3. Paste the following line inside and save the file:
   ```env
   HF_TOKEN=hf_your_copied_token_here
   ```

## Running the App

Start the Streamlit web interface from your terminal:

```bash
streamlit run app.py
```

Once launched, open the local URL shown in your terminal (usually `http://localhost:8501`) in your browser. On the first launch, the models will download and cache locally on your computer.