from flask import Flask, request, jsonify
import requests
import time
import base64

app = Flask(__name__)

# 🔐 Set your actual keys here or via environment variables
UPLOADIO_API_KEY = "secret_W23MT9SFRxVsWLhMDveTsMuysuHX"
UPLOADIO_ACCOUNT_ID = "W23MT9S"
REPLICATE_API_TOKEN = public_W23MT9S845nFTBpibnT3E5xWawMU""
MODEL_VERSION = "e5acb36c13151e51600c089b56702b0ee51e209fdf8f03d179e45f1651b8d161"

@app.route("/clone", methods=["POST"])
def clone_face():
    data = request.json
    image_base64 = data.get("image_base64")
    prompt = data.get("prompt", "a portrait")

    if not image_base64:
        return jsonify({"error": "Missing image_base64"}), 400

    try:
        # 🧼 Clean base64 input
        if "," in image_base64:
            image_base64 = image_base64.split(",")[-1]

        # ➕ Fix base64 padding
        missing_padding = len(image_base64) % 4
        if missing_padding:
            image_base64 += '=' * (4 - missing_padding)

        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        print("Base64 decode error:", str(e))
        return jsonify({"error": "Invalid base64 image data"}), 400

    # 📤 Upload to Upload.io
    try:
        upload_res = requests.post(
            f"https://api.upload.io/v2/accounts/{UPLOADIO_ACCOUNT_ID}/uploads/binary",
            headers={"Authorization": f"Bearer {UPLOADIO_API_KEY}"},
            files={"file": ("image.jpg", image_bytes, "image/jpeg")}
        )
        upload_data = upload_res.json()
        image_url = upload_data.get("fileUrl")

        if not image_url:
            print("Upload.io response:", upload_data)
            return jsonify({"error": "Image upload failed"}), 500
    except Exception as e:
        print("Upload.io error:", str(e))
        return jsonify({"error": "Image upload failed"}), 500

    # 🤖 Start Replicate prediction
    try:
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
            print("Replicate error:", prediction)
            return jsonify({"error": "Failed to start image generation"}), 500
    except Exception as e:
        print("Replicate start error:", str(e))
        return jsonify({"error": "Replicate request failed"}), 500

    # ⏳ Poll Replicate for result
    try:
        poll_url = f"https://api.replicate.com/v1/predictions/{prediction_id}"
        while True:
            poll_res = requests.get(poll_url, headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"})
            poll_data = poll_res.json()
            status = poll_data["status"]

            if status in ["succeeded", "failed", "canceled"]:
                break
            time.sleep(3)

        if status != "succeeded":
            print("Replicate final status:", poll_data)
            return jsonify({"error": "Image generation failed"}), 500

        return jsonify({"clones": poll_data["output"]})
    except Exception as e:
        print("Polling error:", str(e))
        return jsonify({"error": "Error polling Replicate"}), 500

