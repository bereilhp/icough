import pyaudio
import numpy as np
from pymongo import MongoClient
import certifi
from panns_inference import AudioTagging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
connection_string = os.getenv('MONGO_CONNECTION_STRING')

client = MongoClient(connection_string, tlsCAFile=certifi.where())
db = client['audio']
mongodb_sounds_collection = db['sounds']
mongodb_results_collection = db['results']

model = AudioTagging(checkpoint_path=None, device='cpu')  

RECORD_SECONDS = 1
SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

def normalize(v):
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm

def get_embedding(audio_data):
    input_array = np.array(audio_data, dtype=np.int16)
    scaled_array = np.interp(input_array, (-32768, 32767), (-1, 1))
    query_audio = scaled_array[None, :]
    _, emb = model.inference(query_audio)
    return normalize(emb[0])

# MongoDB insert functions
def insert_mongo_results(results):
    entry = {"sensor": "Laptop", "data_time": datetime.now(), "results": results}
    mongodb_results_collection.insert_one(entry)

def knnbeta_search(embedding):
    query_vector = embedding.tolist()
    search_query = [
        {"$search": {"knnBeta": {"vector": query_vector, "path": "emb", "k": 3}}},
        {"$project": {"_id": 0, "audio": 1, "score": {"$meta": "searchScore"}}}
    ]
    return list(mongodb_sounds_collection.aggregate(search_query))

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
num_devices = info.get('deviceCount')

for i in range(num_devices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    if device_info['maxInputChannels'] > 0:
        print(f"Device {i}: {device_info['name']}")

input_device = int(input("Which input device do you want to use? "))
stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE, input_device_index=input_device)

try:
    print("Listening...")
    while True:
        frames = []
        for _ in range(int(SAMPLE_RATE / CHUNK_SIZE * RECORD_SECONDS)):
            frames.append(stream.read(CHUNK_SIZE, exception_on_overflow=False))
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        emb = get_embedding(audio_data)
        results = knnbeta_search(emb)
        insert_mongo_results(results)
        print(results)
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
