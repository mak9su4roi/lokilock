from pydantic import AnyUrl, BaseSettings


class Settings(BaseSettings):
    lock_id: str
    verification_service_url: AnyUrl

settings = Settings()