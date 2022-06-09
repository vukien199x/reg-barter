from pathlib import Path
from PIL import Image


def convert_image_to_webp(path_file: str):
    path = Path(path_file)
    destination = path.with_suffix(".webp")
    image = Image.open(path)
    image.save(destination, format="webp")
    return destination
