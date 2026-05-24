import json
import random
from datasets import load_dataset

def split_non_iid_alpaca(total_samples=5000, num_clients=5):
    # Memuat dataset Alpaca
    dataset = load_dataset("tatsu-lab/alpaca", split='train')
    
    # Mengambil subset agar pelatihan di lab tidak terlalu berat
    all_data = list(dataset)
    random.shuffle(all_data)
    sampled_data = all_data[:total_samples]

    proportions = [0.10, 0.15, 0.20, 0.25, 0.30]
    
    start_idx = 0
    for i, prop in enumerate(proportions):
        num_samples = int(total_samples * prop)
        client_data = sampled_data[start_idx : start_idx + num_samples]
        
        file_name = f"dataset_client_{i+1}.json"
        with open(file_name, 'w') as f:
            json.dump(client_data, f, indent=4)
        
        start_idx += num_samples

if __name__ == "__main__":
    split_non_iid_alpaca(total_samples=10000, num_clients=5)