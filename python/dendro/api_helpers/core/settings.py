from typing import Optional
import os

# Note: BaseSettings is no longer a part of pydantic package, and I didn't want to add a dependency on pydantic-settings
# So I'm using BaseModel instead


class Settings:
    def __init__(self) -> None:
        # General app config
        self.MONGO_URI: Optional[str] = os.environ.get("MONGO_URI")

        self.PUBNUB_SUBSCRIBE_KEY: Optional[str] = os.environ.get("VITE_PUBNUB_SUBSCRIBE_KEY")
        self.PUBNUB_PUBLISH_KEY: Optional[str] = os.environ.get("PUBNUB_PUBLISH_KEY")

        self.GITHUB_CLIENT_ID: Optional[str] = os.environ.get("VITE_GITHUB_CLIENT_ID")
        self.GITHUB_CLIENT_SECRET: Optional[str] = os.environ.get("GITHUB_CLIENT_SECRET")

        self.DEFAULT_COMPUTE_RESOURCE_ID: Optional[str] = os.environ.get("VITE_DEFAULT_COMPUTE_RESOURCE_ID")

        self.OUTPUT_BUCKET_URI: Optional[str] = os.environ.get("OUTPUT_BUCKET_URI")
        self.OUTPUT_BUCKET_CREDENTIALS: Optional[str] = os.environ.get("OUTPUT_BUCKET_CREDENTIALS")
        self.OUTPUT_BUCKET_BASE_URL: Optional[str] = os.environ.get("OUTPUT_BUCKET_BASE_URL")

def get_settings():
    return Settings()
