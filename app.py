from flask import Flask, request, jsonify
import requests
import time
import base64

app = Flask(__name__)

# ✅ Replace with your actual keys
UPLOADIO_API_KEY = "YOUR_UPLOADIO_API_KEY"
UPLOADIO_ACCOUNT_ID = "YOUR_UPLOADIO_ACCOUNT_ID"
REPLICATE_API_TOKEN = "YOUR_REPLICATE_API_TOKEN"
MODEL_VERSION = "e5acb36c13151e51600c089b56702b0ee51e209fdf8f03d179e45f1651b8d161"

@app.route("/clone", methods=["POST"])
def clone_face():
    data = request.json
    image_base64 = data.get("image_base64")
    prompt = data.get("prompt", "a portrait")

    if not image_base64:
        return jsonify({"error": "Missing image_base64"}), 400

    # Step 1: Upload image to Upload.io
    image_bytes = base64.b64decode(image_base64.split(",")[-1])
    upload_res = requests.post(
        f"https://api.upload.io/v2/accounts/{UPLOADIO_ACCOUNT_ID}/uploads/binary",
        headers={"Authorization": f"Bearer {UPLOADIO_API_KEY}"},
        files={"file": ("image.jpg", image_bytes, "image/jpeg")}
    )
    if not upload_res.ok:
        return jsonify({"error": "Upload.io failed"}), 500

    image_url = upload_res.json().get("fileUrl")

    # Step 2: Start prediction on Replicate
    replicate_res = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers={
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "version": MODEL_VERSION,
            "input": {
                "image": image_url,
                "prompt": prompt
            }
        }
    )
    prediction = replicate_res.json()
    prediction_id = prediction.get("id")
    if not prediction_id:
        return jsonify({"error": "Replicate call failed", "details": prediction}), 500

    # Step 3: Poll until done
    while True:
        poll_res = requests.get(
            f"https://api.replicate.com/v1/predictions/{prediction_id}",
            headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"}
        )
        poll_data = poll_res.json()
        status = poll_data["status"]
        if status in ["succeeded", "failed", "canceled"]:
            break
        time.sleep(3)

    if status != "succeeded":
        return jsonify({"error": "Generation failed", "details": poll_data}), 500

    return jsonify({"clones": poll_data["output"]})
