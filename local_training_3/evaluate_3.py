import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def generate_response(model, tokenizer, instruction):
    prompt = f"Instruction: {instruction}\nInput: \nOutput:"
    inputs = tokenizer(prompt, return_tensors="pt")
    
    outputs = model.generate(
        **inputs, 
        max_new_tokens=150, # Jumlah token baru yang ingin dihasilkan
        pad_token_id=tokenizer.eos_token_id
    )
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Path model
BASE_MODEL_PATH = "./gpt2"
UPDATED_MODEL_PATH = "./output_client_3/update_model"

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
test_instruction = "Give me a creative idea for a computer science project."

print("--- TESTING MODEL SEBELUM DILATIH (BASE) ---")
base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_PATH)
print(generate_response(base_model, tokenizer, test_instruction))

print("\n--- TESTING MODEL SESUDAH LATIHAN LOKAL (UPDATED) ---")
updated_model = AutoModelForCausalLM.from_pretrained(UPDATED_MODEL_PATH)
print(generate_response(updated_model, tokenizer, test_instruction))