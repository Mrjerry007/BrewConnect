import os

SECRET_KEY                  = os.getenv("SECRET_KEY", "brewconnect-dev-secret-change-in-prod")
ALGORITHM                   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365 * 10 # 10 years (effectively never expires)

DATABASE_URL                = "sqlite:///./data/brewconnect.db"
DISTANCE_WEIGHT             = 0.4          # 40% proximity
INTEREST_WEIGHT             = 0.6          # 60% interest compatibility
MAX_RADIUS_KM               = 2.0
ACTIVE_SESSION_TIMEOUT_MIN  = 30