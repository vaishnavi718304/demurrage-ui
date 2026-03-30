# ============================================================
# export_model.py
# 
# Run this cell in Automation_Desicion.ipynb AFTER training.
# It exports your real RandomForest model and feature list.
#
# Steps:
# 1. Open Automation_Desicion.ipynb in Colab
# 2. Run all cells so the model is trained
# 3. Copy and paste this entire file as a new cell at the bottom
# 4. Run it — it will download 2 files to your computer:
#       - demurrage_model.joblib
#       - model_features.json
# 5. Upload both files to backend/model/ in your GitHub repo
# ============================================================

import joblib
import json

# Save the trained model
joblib.dump(model, "demurrage_model.joblib")
print("✅ Model saved: demurrage_model.joblib")

# Save the exact feature column list the model was trained on
with open("model_features.json", "w") as f:
    json.dump(num_cols, f, indent=2)
print("✅ Features saved: model_features.json")
print("   Features:", num_cols[:8], "...")

# Download both files to your computer
from google.colab import files
files.download("demurrage_model.joblib")
files.download("model_features.json")

print("\n📁 After downloading, upload both files to:")
print("   backend/model/demurrage_model.joblib")
print("   backend/model/model_features.json")