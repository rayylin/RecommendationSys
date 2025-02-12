from pymongo import MongoClient

from config import mongo

# MongoDB connection string
MONGO_URI = mongo

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["testdb"]  # Create or connect to a database
collection = db["StoreInfo"]  

# Insert a document
data = {"_id":"Yv","name": "Yv", "age": 30, "city": "New York"}
insert_result = collection.insert_one(data)
print(f"Inserted document ID: {insert_result.inserted_id}")

# Read documents
print("Reading documents from MongoDB:")
for doc in collection.find():
    print(doc)

# Close the connection
client.close()