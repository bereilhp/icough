import pyaudio
import numpy as np
from pymongo import MongoClient
import certifi
from panns_inference import AudioTagging
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

connection_string = os.getenv('MONGO_CONNECTION_STRING')

client = MongoClient(connection_string, tlsCAFile=certifi.where())

db = client['iCough']
mongodb_sounds_collection = db['sounds']
mongodb_results_collection = db['results']

model = AudioTagging(checkpoint_path=None, device='cpu')

RECORD_SECONDS = 1

SAMPLE_RATE = 44100
CHUNK_SIZE = 1024

def normalize(v):
    norm = np.linalg.norm(v)
    if norm == 0:
            return v
    return v / norm

def get_embedding (audio_data):
    input_array = np.array(audio_data, dtype=np.int16)
    scaled_array = np.interp(input_array, (-32768, 32767), (-1, 1))
    a = scaled_array
    query_audio = a[None, :]
    _, emb = model.inference(query_audio)
    normalized_v = normalize(emb[0])
    return normalized_v

def insert_mongo_results(results, mongodb_results_collection):
    entry = {"sensor":"Laptop","data_time":datetime.now(),"results":results}
    mongodb_results_collection.insert_one(entry)

def insert_mongo_sounds(audio_name,embedding,audio_file, mongodb_sounds_collection):
    entry = {"audio":audio_name,"emb":embedding,"audio_file":audio_file}
    mongodb_sounds_collection.insert_one(entry)

def knnbeta_search(embedding, mongodb_sounds_collection):
    query_vector = embedding.tolist()

    search_query = [
        {
            "$search": {
                "knnBeta": {
                    "vector": query_vector,
                    "path": "emb",
                    "k": 3
                }
            }
        },
        {
            "$project": {
            "_id": 0,
            "audio": 1,
            "audio_file": 1,
            "score": { "$meta": "searchScore" }
            }
        }
    ]

    results = mongodb_sounds_collection.aggregate(search_query)

    return results

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
num_devices = info.get('deviceCount')

for i in range(num_devices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    if device_info['maxInputChannels'] > 0:
        print(f"Device {i}: {device_info['name']}")

input_device = input("Which input device do you want to use?")

print(input_device)

audio = pyaudio.PyAudio()

audio_description_dictionary = [
    {
      "audio": "Healthy",
      "description": "Cough does not show signs of concern."
    },
    {
      "audio": "Visit a Doctor",
      "description": "Cough might be of concern. Consider consulting a healthcare professional."
    },
    {
      "audio": "Emergency",
      "description": "Cough indicates severe symptoms. Seek immediate medical attention."
    }
]


for audio_description in audio_description_dictionary:
    input(f"Get ready to record '{audio_description['audio']}' - press enter when ready")

    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK_SIZE,input_device_index=int(input_device))

    for j in range(1):
        stream.start_stream()
        frames = []
        for i in range(0, int((SAMPLE_RATE / CHUNK_SIZE) * RECORD_SECONDS)):
            data = stream.read(CHUNK_SIZE)
            frames.append(data)
        stream.stop_stream()

        audio_data = np.frombuffer(b"".join(frames), dtype=np.int16)

        emb = get_embedding(audio_data)

        insert_mongo_sounds(f"{audio_description['audio']}", emb.tolist(), f"{j}", mongodb_sounds_collection)
    stream.close()
    print('Recorded successfully')


audio.terminate()
