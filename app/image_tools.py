import re
import datetime
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

# Hardcoded project and bucket to prevent project-number mismatch on Agent Platform runtime
PROJECT_ID = "qwiklabs-gcp-03-2f3e1ba5c32a"
BUCKET_NAME = "zoonow-assets-qwiklabs-gcp-03-2f3e1ba5c32a"

_storage_client: Optional[storage.Client] = None
_genai_client: Optional[genai.Client] = None


def get_storage_client() -> storage.Client:
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
    return _genai_client


def generate_animal_badge_image(
    animal_name: str,
    prompt_context: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, Any]:
    """Generate a visual encounter badge or illustration for a Toronto Zoo animal using gemini-3.1-flash-lite-image.

    The generated image is saved as an artifact in the local Playground session and uploaded
    directly to the public Google Cloud Storage bucket for web embedding.

    Args:
        animal_name: Name of the animal (e.g., 'Arctic Fox', 'Amur Tiger', 'Polar Bear').
        prompt_context: Optional style or scene context (e.g., 'resting on snowy rocks', 'spotter explorer badge').
        tool_context: Tool context injected by the ADK runtime.

    Returns:
        A dictionary containing the public HTTPS URL, artifact filename, and status.
    """
    clean_name = animal_name.strip()
    scene_detail = prompt_context or "spotter badge with modern nature illustration style"
    prompt = (
        f"A beautiful, high quality illustrated badge of a {clean_name} at the Toronto Zoo. "
        f"{scene_detail}. Vibrant colors, clean edges, nature reserve aesthetic."
    )

    client = get_genai_client()
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )
    except Exception as e:
        return {"error": f"Failed to generate image with gemini-3.1-flash-lite-image: {str(e)}"}

    # Extract image bytes from inline_data parts
    image_bytes = None
    mime_type = "image/jpeg"
    for candidate in response.candidates:
        if not candidate.content or not candidate.content.parts:
            continue
        for part in candidate.content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break
        if image_bytes:
            break

    if not image_bytes:
        return {"error": "Model response did not contain image data."}

    # Generate consistent filename
    safe_slug = re.sub(r"[^a-z0-9]+", "_", clean_name.lower()).strip("_")
    timestamp_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    ext = "png" if "png" in mime_type else "jpg"
    filename = f"{safe_slug}_{timestamp_str}.{ext}"

    # 1. Save artifact for Playground Artifacts panel
    if tool_context is not None:
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(
                filename=filename,
                artifact=artifact_part,
                custom_metadata={"animal": clean_name, "model": "gemini-3.1-flash-lite-image"},
            )
        except Exception as e:
            print(f"Warning: Failed to save artifact in tool_context: {e}")

    # 2. Upload image bytes directly to public GCS bucket
    try:
        storage_client = get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"images/{filename}")
        blob.upload_from_string(image_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}"
    except Exception as e:
        return {"error": f"Failed to upload image to Google Cloud Storage: {str(e)}"}

    return {
        "success": True,
        "animal": clean_name,
        "filename": filename,
        "public_url": public_url,
        "message": f"Generated image for {clean_name}. Uploaded to Cloud Storage and saved to session artifacts.",
    }
