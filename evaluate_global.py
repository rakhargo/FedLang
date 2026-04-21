from transformers import GPT2LMHeadModel, GPT2Tokenizer
from safetensors.torch import load_file
import torch

def generate_response(model, tokenizer, instruction):
    prompt = f"Instruction: {instruction}\nInput: \nOutput:"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    # Generate dengan sedikit penalti repetisi agar hasil lebih natural
    outputs = model.generate(
        **inputs, 
        max_new_tokens=50,
        pad_token_id=tokenizer.eos_token_id,
        no_repeat_ngram_size=2,
        do_sample=True,
        top_k=50,
        top_p=0.95
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def main():
    model_name = "gpt2"
    merged_model_path = "global_model_updated.safetensors"
    
    print("--- LOADING GLOBAL MODEL ---")
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    model = GPT2LMHeadModel.from_pretrained(model_name)
    
    # 1. Memuat state_dict dari safetensors
    state_dict = load_file(merged_model_path)
    
    # 2. PERBAIKAN: Tangani Weight Tying untuk GPT-2
    # Jika lm_head.weight tidak ada, gunakan bobot dari transformer.wte
    if "lm_head.weight" not in state_dict and "transformer.wte.weight" in state_dict:
        print("  [Note] Mengikat kembali bobot lm_head.weight dari transformer.wte.weight")
        state_dict["lm_head.weight"] = state_dict["transformer.wte.weight"]
    
    # 3. Muat ke dalam model
    model.load_state_dict(state_dict)
    
    test_instruction = "Give me a creative idea for a computer science project."
    
    print("\n--- TESTING MERGED GLOBAL MODEL (ROUND 1) ---")
    result = generate_response(model, tokenizer, test_instruction)
    print(result)

if __name__ == "__main__":
    main()