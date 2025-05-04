# Image Cloner Backend

A Flask API that accepts a base64 image + prompt and returns clone images using Upload.io + Replicate InstantID.

## Endpoints

POST /clone  
Body:
```json
{
  "image_base64": "data:image/jpeg;base64,...",
  "prompt": "a person in a tuxedo"
}
