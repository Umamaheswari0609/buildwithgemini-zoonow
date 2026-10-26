import datetime
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-2f3e1ba5c32a"

db = firestore.Client(project=PROJECT_ID)

ANIMALS = [
    {
        "id": "arctic_fox",
        "name": "Arctic Fox",
        "species": "Vulpes lagopus",
        "pavilion": "Tundra Trek",
        "exhibit_location": "Tundra Trek North Loop",
        "lat": 43.8215,
        "lng": -79.1842,
        "official_status": "Available",
        "current_status": "Not Currently Visible",
        "confidence": "High",
        "last_confirmed_visible": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=45)).isoformat(),
        "recent_visibility_reports": 5,
        "recent_not_visible_reports": 6,
        "description": "Thick white fur and active during cooler mornings. Often rests inside rocky den crevices during mid-day.",
    },
    {
        "id": "amur_tiger",
        "name": "Amur Tiger",
        "species": "Panthera tigris tigris",
        "pavilion": "Eurasia Wilds",
        "exhibit_location": "Eurasia Tiger Ridge",
        "lat": 43.8230,
        "lng": -79.1820,
        "official_status": "Available",
        "current_status": "Available Now",
        "confidence": "High",
        "last_confirmed_visible": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=3)).isoformat(),
        "recent_visibility_reports": 12,
        "recent_not_visible_reports": 0,
        "description": "Largest cat species, roaming near the shaded stream and grassy ridge.",
    },
    {
        "id": "western_lowland_gorilla",
        "name": "Western Lowland Gorilla",
        "species": "Gorilla gorilla gorilla",
        "pavilion": "African Rainforest",
        "exhibit_location": "African Rainforest Pavilion Indoors",
        "lat": 43.8185,
        "lng": -79.1865,
        "official_status": "Available",
        "current_status": "Available Now",
        "confidence": "High",
        "last_confirmed_visible": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)).isoformat(),
        "recent_visibility_reports": 9,
        "recent_not_visible_reports": 1,
        "description": "Family troop including silverback Charles, visible by indoor climbing structures and viewing glass.",
    },
    {
        "id": "polar_bear",
        "name": "Polar Bear",
        "species": "Ursus maritimus",
        "pavilion": "Tundra Trek",
        "exhibit_location": "Tundra Trek Underwater Viewing & Pool",
        "lat": 43.8222,
        "lng": -79.1850,
        "official_status": "Available",
        "current_status": "Possibly Available",
        "confidence": "Medium",
        "last_confirmed_visible": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=22)).isoformat(),
        "recent_visibility_reports": 4,
        "recent_not_visible_reports": 2,
        "description": "Often swimming in the 500,000-gallon pool or resting along the tundra gravel shores.",
    },
    {
        "id": "african_lion",
        "name": "African Lion",
        "species": "Panthera leo",
        "pavilion": "African Savanna",
        "exhibit_location": "Savanna Lion Koppie",
        "lat": 43.8198,
        "lng": -79.1880,
        "official_status": "Available",
        "current_status": "Possibly Available",
        "confidence": "Medium",
        "last_confirmed_visible": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=25)).isoformat(),
        "recent_visibility_reports": 3,
        "recent_not_visible_reports": 1,
        "description": "Pride pride basking on elevated heated rock outcroppings overlooking the savanna.",
    },
]

def seed():
    batch = db.batch()
    for item in ANIMALS:
        doc_ref = db.collection("animals").document(item["id"])
        batch.set(doc_ref, item)
    batch.commit()
    print(f"Seeded {len(ANIMALS)} animals to Firestore collection 'animals' (project: {PROJECT_ID}).")

if __name__ == "__main__":
    seed()
