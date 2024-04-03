from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import numpy as np
from pymongo import MongoClient
import certifi
from panns_inference import AudioTagging
from datetime import datetime
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile
from dotenv import load_dotenv

load_dotenv()

connection_string = os.getenv('MONGO_CONNECTION_STRING')

client = MongoClient(connection_string, tlsCAFile=certifi.where())
db = client['audio']
mongodb_sounds_collection = db['sounds']
mongodb_results_collection = db['results']

model = AudioTagging(checkpoint_path=None, device='cpu')  

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)
def normalize(v):
    norm = np.linalg.norm(v)
    return v if norm == 0 else v / norm

def get_embedding(audio_data):
    input_array = np.array(audio_data, dtype=np.int16)
    scaled_array = np.interp(input_array, (-32768, 32767), (-1, 1))
    query_audio = scaled_array[None, :]
    _, emb = model.inference(query_audio)
    return normalize(emb[0])

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

@app.post("/process-audio/")
async def process_audio(file: UploadFile = File(...)):
    content = await file.read() 

    audio_data = np.frombuffer(content, dtype=np.int16)  
    emb = get_embedding(audio_data)  
    results = knnbeta_search(emb)  
    insert_mongo_results(results)  
    
    return JSONResponse(content={"results": results})
