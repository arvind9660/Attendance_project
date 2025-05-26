import os
from django.conf import settings

def st_record(folder_path):
    full_path = os.path.join(settings.MEDIA_ROOT, folder_path)
    try:
        return [f for f in os.listdir(full_path) if f.lower().endswith(('.jpg', '.png', '.gif'))]
    except FileNotFoundError:
        return []
