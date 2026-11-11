from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextIteratorStreamer, GenerationConfig
import torch
from threading import Thread
from dotenv import load_dotenv
from pathlib import Path
import os
from langchain_llm_app import get_optimal_GPU

ROOT = Path(__file__).resolve().parent.parent.parent

load_dotenv(f"{ROOT}/.env")

hf_token = os.environ['HF_TOKEN']

class LocalMechanicalModel:
    def __init__(self, model_id:str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B") -> None:
        print(f"Loading model - {model_id}")
        quantized_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
            bnb_4bit_quant_type="nf4"
        )
        device = get_optimal_GPU()
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        load_kwargs = {
                    "torch_dtype":torch.float16 if device != "cpu" else torch.float32,
                    "trust_remote_code": True,
                    "use_cache":False,
                    "token": hf_token,
                }
        if device == "cuda":
            load_kwargs.update({
                "quantization_config": quantized_config, 
                "device_map": "auto"})
        else:
            load_kwargs.update({
                "torch_dtype":torch.float16 if device == "mps" else torch.float32,
                "device_map": {"": device}
                })
        self.model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
        self.generation_config = GenerationConfig(
            temperature = 0.6,
            top_p = 0.9,
            max_new_tokens = 4096,
            do_sample = True,
            eos_token_id = self.tokenizer.eos_token_id,
            pad_token_id = self.tokenizer.pad_token_id,
            repetition_penalty=1.1
        )

    def generate_response(self, messages:list, system_prompt:str = ""):

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role":"system", "content": system_prompt})

        formatted_messages.extend(messages)

        input_text = self.tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True
        )

        generation_kawrgs = dict(
            **inputs,
            streamer = streamer,
            generation_config=self.generation_config
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kawrgs)
        thread.start()

        for new_text in streamer:
            yield new_text

