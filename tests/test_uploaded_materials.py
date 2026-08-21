import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from werkzeug.datastructures import FileStorage

from services.uploaded_materials import save_uploaded_image


def image_upload(name="sample.png", mime="image/png"):
    buffer = BytesIO()
    Image.new("RGB", (120, 80), "#35c8aa").save(buffer, "PNG")
    buffer.seek(0)
    return FileStorage(stream=buffer, filename=name, content_type=mime)


def rotated_jpeg_upload():
    buffer = BytesIO()
    image = Image.new("RGB", (120, 80), "#35c8aa")
    exif = image.getexif()
    exif[274] = 6  # 90 degrees clockwise for correct display
    image.save(buffer, "JPEG", exif=exif)
    buffer.seek(0)
    return FileStorage(
        stream=buffer,
        filename="phone-photo.jpg",
        content_type="image/jpeg",
    )


class UploadedMaterialsTests(unittest.TestCase):
    def test_saves_valid_image_as_safe_png(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "services.uploaded_materials.MATERIAL_DIR", Path(tmp)
        ):
            saved = save_uploaded_image(image_upload(), "photo")
            self.assertTrue(saved.endswith(".png"))
            with Image.open(saved) as image:
                self.assertEqual(image.size, (120, 80))

    def test_rejects_wrong_mime_type(self):
        upload = FileStorage(stream=BytesIO(b"not an image"), filename="x.txt", content_type="text/plain")
        self.assertEqual(save_uploaded_image(upload), "")

    def test_applies_phone_exif_orientation_before_saving(self):
        with tempfile.TemporaryDirectory() as tmp, patch(
            "services.uploaded_materials.MATERIAL_DIR", Path(tmp)
        ):
            saved = save_uploaded_image(rotated_jpeg_upload(), "photo")
            with Image.open(saved) as image:
                self.assertEqual(image.size, (80, 120))
                self.assertNotIn(274, image.getexif())


if __name__ == "__main__":
    unittest.main()
