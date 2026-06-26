import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from datasets import load_dataset
import os

MODEL_PATH = "./gpt2" 
DATASET_FILE = "dataset_client_1.json"
OUTPUT_DIR = "./output_client_1"

# 1. Load Model & Tokenizer 
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
tokenizer.pad_token = tokenizer.eos_token # GPT-2 tidak punya pad token bawaan

model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)

# 2. Load & Preprocess Dataset
def tokenize_function(examples):
    texts = [f"Instruction: {i}\nInput: {inp}\nOutput: {o}" 
             for i, inp, o in zip(examples['instruction'], examples['input'], examples['output'])]
    
    # Tokenisasi teks
    tokenized = tokenizer(texts, truncation=True, padding="max_length", max_length=128)
    tokenized["labels"] = tokenized["input_ids"].copy()
    
    return tokenized

dataset = load_dataset('json', data_files=DATASET_FILE, split='train')
tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 4. Training
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=4,
    num_train_epochs=1, # 1 epoch untuk latihan lokal, bisa disesuaikan
    logging_steps=10,
    save_strategy="no", # Simpan manual
    learning_rate=5e-5,
    weight_decay=0.01,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

trainer.train()

# 5. Simpan Update Model (Gradien/Bobot Baru)
model.save_pretrained(f"{OUTPUT_DIR}/update_model")
print(f"--- Training Selesai. Update model disimpan di {OUTPUT_DIR}/update_model ---")