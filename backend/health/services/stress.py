import os
import joblib
import pandas as pd
from django.conf import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, "health", "services", "stress.pkl")
model = joblib.load(MODEL_PATH)

FEATURE_COLUMNS = ["snr", "rr", "bt", "lm", "bo", "rem", "sh", "hr"]

LABELS = {
    0: "Very Low",
    1: "Low",
    2: "Moderate",
    3: "High",
    4: "Severe"
}

SCORE_MAP = {
    0: 15,
    1: 35,
    2: 55,
    3: 75,
    4: 95
}


def predict_stress(features_dict):
    """
    Takes validated feature dictionary
    Returns prediction class
    """

    # Create DataFrame with correct column order
    df = pd.DataFrame([[features_dict[col] for col in FEATURE_COLUMNS]],
                      columns=FEATURE_COLUMNS)

    prediction = model.predict(df)[0]

    return prediction

def stressService(user, additional_data):
    """
    Main service function used by views.
    Returns:
        stress_level (str)
        stress_score (int)
    """

    features = {}

    for col in FEATURE_COLUMNS:
        value = additional_data.get(col)

        if value is None:
            raise ValueError(f"Missing required feature: {col}")

        try:
            features[col] = float(value)
        except ValueError:
            raise ValueError(f"Invalid value for {col}")

    prediction = predict_stress(features)

    stress_level = LABELS.get(prediction, "Unknown")
    stress_score = SCORE_MAP.get(prediction, 50)


    return {
        "stress_level": stress_level,
        "stress_score": stress_score
    }