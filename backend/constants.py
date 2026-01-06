### Simulation constants

# Time between simulation ticks in seconds (sent to frontend for animation timing)
TICK_INTERVAL_SECONDS = 2.5

# Player walking speed in meters per tick
WALKING_SPEED = 75.0

# Determine acceptable distance to hole for complete in meters
HOLE_COMPLETION_DISTANCE = 1.5

# Determine player to ball distance for shot to be taken in meters
SHOT_TAKING_DISTANCE = 1.0

# Number of ticks for greenkeeper to place a flag
FLAG_PLACEMENT_DURATION_TICKS = 3

# Number of ticks before a hole needs flag service
HOLE_SERVICE_INTERVAL_TICKS = 180.0

# TODO: Is this used?
# Distance in meters greenkeeper maintains from hole when idle
GREENKEEPER_IDLE_DISTANCE_METERS = 35.0

# Safety distance in meters
GREENKEEPER_SAFETY_DISTANCE_METERS = 50.0

# Safety distance in meters
GROUP_SAFETY_DISTANCE_METERS = 250.0

# Base maximum distance for a club in meters
BASE_MAX_DISTANCE = 260.0

# Number of steps to evaluate for shot options
NUMBER_OF_POWER_STEPS_TO_VALIDATE = 10
NUMBER_OF_DIRECTION_STEPS_TO_VALIDATE = 10

# Club distance multipliers - Higher is longer distance
CLUB_MULTIPLIERS = {
    "driver": 1.0,
    "iron": 0.7,
    "wedge": 0.45,
    "putter": 0.15,
}

# Changes the distance based on the lie - Higher is further
LIE_MULTIPLIERS_DISTANCE = {
    "green": 0.15,
    "fairway": 0.9,
    "tee": 1.0,
    "rough": 0.75,
    "bunker": 0.5,
}

# Changes the utility based on the lie - Higher is worse
LIE_MULTIPLIERS_UTILITY = {
    "green": 0.1,
    "fairway": 0.5,
    "tee": 2.0,
    "rough": 3.0,
    "bunker": 4.0,
    "water": 5.0,
}

# Ticks between wind condition updates
WIND_UPDATE_TICKER_INTERVAL = 1

# Wind effect factor in percentage effect per m/s of wind speed
WIND_EFFECT_FACTOR = 0.02

# Distance required in order to spawn a new group from the tee in meters
MIN_DISTANCE_FROM_TEE_TO_SPAWN_NEW_GROUP = 50.0

# Utility penalty for shots taken from another hole's features
WRONG_HOLE_UTILITY_PENALTY = 1000.0
