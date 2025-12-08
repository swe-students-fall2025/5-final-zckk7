from pymongo import MongoClient
from werkzeug.security import generate_password_hash

MONGO_URI = "mongodb+srv://gz:1234@cluster0.fv25oph.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.smart_apartment_db

db.users.drop()
db.users.insert_many([
    {
        "first_name": "Admin",
        "last_name": "User",
        "username": "admin",
        "password": generate_password_hash("admin123"),
        "role": "admin"
    },
    {
        "first_name": "Alex",
        "last_name": "Smith",
        "username": "resident1",
        "password": generate_password_hash("resident123"),
        "role": "resident"
    }
])
print("Sample users created!")
print("   Admin: username='admin', password='admin123', name='Admin User'")
print("   Resident: username='resident1', password='resident123', name='Alex Smith'")

db.community_posts.drop()
db.community_posts.insert_many([
    {
        "title": "Extra lasagna leftovers",
        "category": "Food",
        "author": "Marina Chen (B-204)",
        "time": "15m ago",
        "description": "Made way too much for dinner party. Still warm, has mushrooms and spinach. Container in fridge by mailroom.",
        "price": "Free",
        "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=800"
    },
    {
        "title": "Moving Sale: IKEA desk chair",
        "category": "Furniture",
        "author": "James Park (C-412)",
        "time": "3h ago",
        "description": "Used it for 2 years, still works fine. Some scratches on the armrests but wheels are good. Moving end of month.",
        "price": "$35",
        "image": "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=800"
    },
    {
        "title": "Need drill for bookshelf",
        "category": "Help",
        "author": "You (A-101)",
        "time": "Yesterday",
        "description": "Anyone have a cordless drill I can borrow for like 20 minutes? Just need to hang one thing.",
        "price": None,
        "image": None
    },
    {
        "title": "Free moving boxes",
        "category": "Other",
        "author": "Lisa Wong (D-105)",
        "time": "2 days ago",
        "description": "Got a bunch of clean boxes from my move. Various sizes. Help yourself, they're in the recycling area.",
        "price": "Free",
        "image": None
    }
])

db.packages.drop()
db.packages.insert_many([
    {
        "carrier": "Amazon",
        "tracking": "#TRK-8899",
        "location": "Locker A-05",
        "status": "ready",
        "arrival": "Today, 10:30 AM"
    },
    {
        "carrier": "USPS",
        "tracking": "#9405511899223197428490",
        "location": "Front Desk",
        "status": "processing",
        "arrival": "Yesterday"
    },
    {
        "carrier": "FedEx",
        "tracking": "#1234567890",
        "location": "Delivered",
        "status": "picked_up",
        "arrival": "Oct 20"
    }
])

db.sensors.drop()
db.sensors.insert_one({
    "room": "A-101",
    "temperature": 23,
    "humidity": 47,
    "smoke": "normal",
    "maintenance_pending": 1
})

print("Database setup complete!")