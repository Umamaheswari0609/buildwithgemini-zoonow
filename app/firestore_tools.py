import datetime
import math
from typing import Optional, Dict, Any, List
from google.cloud import firestore

# Project ID hardcoded as string to prevent project-number mismatch on Agent Platform runtime
PROJECT_ID = "qwiklabs-gcp-03-2f3e1ba5c32a"

_db: Optional[firestore.Client] = None

def get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def list_animals(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """List animals from the Toronto Zoo catalog along with their real-time visibility status.

    Args:
        status_filter: Optional filter by status, e.g. 'Available Now', 'Possibly Available', 'Not Currently Visible'.

    Returns:
        A list of animal records including current availability status, confidence, and exhibit location.
    """
    db = get_db()
    docs = db.collection("animals").stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if status_filter:
            if status_filter.lower() not in data.get("current_status", "").lower():
                continue
        results.append({
            "id": data.get("id"),
            "name": data.get("name"),
            "species": data.get("species"),
            "pavilion": data.get("pavilion"),
            "current_status": data.get("current_status"),
            "confidence": data.get("confidence"),
            "last_confirmed_visible": data.get("last_confirmed_visible"),
            "recent_visibility_reports": data.get("recent_visibility_reports", 0),
            "recent_not_visible_reports": data.get("recent_not_visible_reports", 0),
            "official_status": data.get("official_status"),
            "exhibit_location": data.get("exhibit_location")
        })
    return results


def get_animal_details(animal_id_or_name: str) -> Dict[str, Any]:
    """Retrieve detailed real-time availability and exhibit information for a specific animal.

    Args:
        animal_id_or_name: ID or name of the animal (e.g. 'arctic_fox', 'tiger', 'Gorilla').

    Returns:
        Detailed dictionary of the animal's status, reports, pavilion, and visitor tips.
    """
    db = get_db()
    clean_id = animal_id_or_name.strip().lower().replace(" ", "_")
    doc_ref = db.collection("animals").document(clean_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()

    # Fallback search by name substring
    for item in db.collection("animals").stream():
        data = item.to_dict()
        if animal_id_or_name.lower() in data.get("name", "").lower():
            return data

    return {"error": f"Animal '{animal_id_or_name}' not found in Toronto Zoo catalog."}


def report_animal_sighting(animal_id_or_name: str, visible: bool, note: Optional[str] = None) -> Dict[str, Any]:
    """Submit a real-time visitor report for whether an animal is currently visible at its exhibit.

    Args:
        animal_id_or_name: ID or name of the animal (e.g. 'arctic_fox', 'tiger').
        visible: True if the visitor sees the animal right now, False if not visible.
        note: Optional note or comment from visitor (e.g. 'Swam underwater', 'Hiding behind rock').

    Returns:
        Status update confirmation with updated visibility counts and current status.
    """
    db = get_db()
    animal = get_animal_details(animal_id_or_name)
    if "error" in animal:
        return animal

    animal_id = animal["id"]
    doc_ref = db.collection("animals").document(animal_id)

    # Record sighting report in reports subcollection
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    db.collection("reports").add({
        "animal_id": animal_id,
        "visible": visible,
        "timestamp": now_iso,
        "note": note or ""
    })

    # Update animal counters and status
    visible_count = animal.get("recent_visibility_reports", 0)
    not_visible_count = animal.get("recent_not_visible_reports", 0)

    if visible:
        visible_count += 1
        new_status = "Available Now"
        new_confidence = "High"
        last_confirmed = now_iso
    else:
        not_visible_count += 1
        if visible_count == 0 or not_visible_count > visible_count:
            new_status = "Not Currently Visible"
            new_confidence = "High"
        else:
            new_status = "Possibly Available"
            new_confidence = "Medium"
        last_confirmed = animal.get("last_confirmed_visible")

    update_payload = {
        "recent_visibility_reports": visible_count,
        "recent_not_visible_reports": not_visible_count,
        "current_status": new_status,
        "confidence": new_confidence,
        "last_confirmed_visible": last_confirmed
    }
    doc_ref.update(update_payload)

    return {
        "success": True,
        "animal": animal["name"],
        "reported_visible": visible,
        "updated_status": new_status,
        "confidence": new_confidence,
        "recent_visible_reports": visible_count,
        "recent_not_visible_reports": not_visible_count,
        "message": f"Thank you! Your report for {animal['name']} has been recorded and updated community availability."
    }


def toggle_watchlist_alert(animal_id_or_name: str, enable: bool = True, visitor_id: str = "visitor_default") -> Dict[str, Any]:
    """Subscribe or unsubscribe to 'Notify Me When Available' alerts for an animal.

    Args:
        animal_id_or_name: ID or name of the animal to watch (e.g. 'arctic_fox', 'Polar Bear').
        enable: True to turn alerts ON, False to turn alerts OFF.
        visitor_id: Identifier for the visitor or session (defaults to 'visitor_default').

    Returns:
        Confirmation status, current animal availability, and notification preference details.
    """
    db = get_db()
    animal = get_animal_details(animal_id_or_name)
    if "error" in animal:
        return animal

    animal_id = animal["id"]
    watch_doc_id = f"{visitor_id}_{animal_id}"
    watch_ref = db.collection("watchlist").document(watch_doc_id)

    if enable:
        watch_ref.set({
            "visitor_id": visitor_id,
            "animal_id": animal_id,
            "animal_name": animal["name"],
            "enabled": True,
            "subscribed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        return {
            "success": True,
            "alert_enabled": True,
            "animal": animal["name"],
            "current_status": animal.get("current_status"),
            "message": f"🔔 Watchlist alert enabled! We will notify you when the {animal['name']} is reported visible."
        }
    else:
        watch_ref.delete()
        return {
            "success": True,
            "alert_enabled": False,
            "animal": animal["name"],
            "message": f"🔕 Watchlist alert removed for {animal['name']}."
        }

