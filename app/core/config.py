from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./room_reservations.db"
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    no_show_grace_minutes: int = 15
    user_max_active_reservations: int = 2   
    user_max_hours_per_day: int = 4         
    user_max_hours_per_reservation: int = 2 

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
