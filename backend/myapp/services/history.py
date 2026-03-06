from datetime import datetime
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client['unified_persona_db']
health_collection = db['health_agent']

def save_health_output(user_id, decision, recommendation, stress_score):
    record = {
        "timestamp": datetime.now(),
        "user_id": user_id,
        "agent_type": "health",
        "decision": decision,
        "recommendation": recommendation,
        "stress_score": stress_score
    }
    health_collection.insert_one(record)

def get_health_history(user_id):
    return list(health_collection.find({"user_id": user_id}).sort("timestamp", 1))