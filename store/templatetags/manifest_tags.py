import json
from django import template
import os
from pathlib import Path

register = template.Library()

BASE_DIR = Path(__file__).resolve().parent.parent

file_dir = os.path.join(BASE_DIR, "static/frontend/manifest.json")
@register.simple_tag
def get_from_manifest(filename):
    with open(file_dir) as manifest_file:
        manifest = json.load(manifest_file)
        file_path = manifest.get(filename)
        if file_path:
            # Remove the 'auto/' prefix from the file path
            file_path = file_path.replace('auto/', '')
        return file_path or filename