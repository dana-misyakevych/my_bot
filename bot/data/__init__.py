import json
from pathlib import Path

data_path = Path(__file__).parent

with open(f'{data_path}/stores_info.json') as file_obj:
    stores_info = json.load(file_obj)

