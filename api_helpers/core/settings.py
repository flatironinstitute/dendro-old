from pydantic import BaseModel
import os

# Note: BaseSettings is no longer a part of pydantic package, and I didn't want to add a dependency on pydantic-settings
# So I'm using BaseModel instead


class Settings(BaseModel):
    # General app config
    MONGO_URI: str = os.environ.get("MONGO_URI")
    
    PUBNUB_SUBSCRIBE_KEY: str = os.environ.get("VITE_PUBNUB_SUBSCRIBE_KEY")
    PUBNUB_PUBLISH_KEY: str = os.environ.get("PUBNUB_PUBLISH_KEY")
    
    GITHUB_CLIENT_ID: str = os.environ.get("VITE_GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = os.environ.get("GITHUB_CLIENT_SECRET")
    
    DEFAULT_COMPUTE_RESOURCE_ID: str = os.environ.get("VITE_DEFAULT_COMPUTE_RESOURCE_ID")

    OUTPUT_BUCKET_URI: str = os.environ.get("OUTPUT_BUCKET_URI")
    OUTPUT_BUCKET_CREDENTIALS: str = os.environ.get("OUTPUT_BUCKET_CREDENTIALS")
    OUTPUT_BUCKET_BASE_URL: str = os.environ.get("OUTPUT_BUCKET_BASE_URL")

def get_settings():
    return Settings()