from functools import lru_cache

from google.cloud import firestore
from google.cloud.firestore_v1.client import Client

from mem_resolve_app.config import get_settings


@lru_cache
def get_firestore_client() -> Client:
    """Create and cache the Firestore client.

    Locally, Google Application Default Credentials are used.

    On GCP, the runtime service account is used automatically.

    If FIRESTORE_EMULATOR_HOST is configured, the Google Firestore
    library automatically connects to the local emulator.
    """
    settings = get_settings()

    return firestore.Client(
        project=settings.google_cloud_project,
        database=settings.firestore_database,
    )