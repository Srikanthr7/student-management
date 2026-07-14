import cloudinary
import cloudinary.uploader
import cloudinary.api

# ─── Step 1: Configure Cloudinary (inline credentials) ───────────────────────
cloudinary.config(
    cloud_name="dnxkhezeh",
    api_key="344713289558367",
    api_secret="O79yOlnUGNHLN6PYS6u3NOaBhFM",
    secure=True
)

# ─── Step 2: Upload a sample image ───────────────────────────────────────────
print("Uploading image...")

sample_url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"

upload_result = cloudinary.uploader.upload(sample_url)

secure_url = upload_result["secure_url"]
public_id  = upload_result["public_id"]

print(f"\n✅ Upload successful!")
print(f"   Public ID  : {public_id}")
print(f"   Secure URL : {secure_url}")

# ─── Step 3: Fetch image metadata ────────────────────────────────────────────
print("\nFetching image details...")

details = cloudinary.api.resource(public_id)

print(f"\n📋 Image Details:")
print(f"   Width      : {details['width']} px")
print(f"   Height     : {details['height']} px")
print(f"   Format     : {details['format']}")
print(f"   File size  : {details['bytes']} bytes")

# ─── Step 4: Generate a transformed URL ──────────────────────────────────────
# f_auto — Cloudinary automatically picks the best format for the viewer's
#           browser (e.g. WebP for Chrome, AVIF for supported browsers).
# q_auto — Cloudinary automatically selects the best quality level that
#           keeps the image looking good while reducing file size.
transformed_url = cloudinary.CloudinaryImage(public_id).build_url(
    fetch_format="auto",   # f_auto
    quality="auto"         # q_auto
)

print("\n🔗 Transformed image URL (f_auto + q_auto):")
print(f"   {transformed_url}")
print("\n🎉 Done! Click the link above to see the optimized version of the image.")
print("   Check how the format and file size compare to the original.")
