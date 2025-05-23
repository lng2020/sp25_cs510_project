import json
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config.es_config as es_config

es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=("elastic", es_config.KEY),
    verify_certs=False,
    ssl_show_warn=False
)

base_folder = "data/raw/website"

# Get subfolders that match existing indices
existing_indices = es.indices.get_alias().keys()
subfolders = []
for index in existing_indices:
    if index.startswith("webpages_"):
        folder_name = index.replace("webpages_", "")
        folder_path = os.path.join(base_folder, folder_name)
        if os.path.exists(folder_path):
            subfolders.append(folder_name)

if not subfolders:
    print("No matching folders found")
    exit()

print(f"Found {len(subfolders)} folders to process")

for subfolder in subfolders:
    index_name = f"webpages_{subfolder}"
    json_folder = os.path.join(base_folder, subfolder)
    json_files = [f for f in os.listdir(json_folder) if f.endswith('.json')]
    
    print(f"\nProcessing: {subfolder}")
    print(f"Found {len(json_files)} JSON files")
    
    total_docs = 0
    for json_file in tqdm(json_files, desc=f"Importing {subfolder}"):
        file_path = os.path.join(json_folder, json_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                pages = json.load(f)
            
            actions = []
            for page in pages:
                doc = {
                    "_index": index_name,
                    "_source": {
                        "title": page.get("title", ""),
                        "url": page.get("url", ""),
                        "anchor_texts": page.get("anchor_texts", []),
                        "content": page.get("content", ""),
                        "outlinks": page.get("outlinks", [])
                    }
                }
                actions.append(doc)
            
            if actions:
                helpers.bulk(es, actions)
                total_docs += len(actions)
                
        except Exception as e:
            print(f"\nError processing {json_file}: {str(e)}")
    
    print(f"\nCompleted {subfolder}: {total_docs} documents imported")

print("\nAll folders processed!")