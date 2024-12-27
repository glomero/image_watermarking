from app import app
from flask import request, render_template, url_for # type: ignore
import os
import cv2
import numpy as np
from PIL import Image
from werkzeug.utils import secure_filename
import random
import string

# Add path to config
app.config['INITIAL_FILE_UPLOADS'] = r'C:\Users\Administrator\Desktop\Data Science Project\WaterMark\app\static\uploads'

# Ensure the upload folder exists
os.makedirs(app.config['INITIAL_FILE_UPLOADS'], exist_ok=True)

# Allowed extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        full_filename = 'image/white_bg.jpg'
        return render_template('index.html', full_filename=full_filename)

    if request.method == 'POST':
        # Check required fields
        image_upload = request.files.get('image_upload')
        if not image_upload or not allowed_file(image_upload.filename):
            return "Please upload a valid image (PNG/JPG).", 400
        
        option = request.form.get('options', 'text_mark')
        image = Image.open(image_upload)
        image_logo = np.array(image.convert('RGB'))
        h_image, w_image, _ = image_logo.shape

        # Random filename
        letters = string.ascii_lowercase
        name = ''.join(random.choice(letters) for _ in range(10)) + '.png'
        full_filename = os.path.join(app.config['INITIAL_FILE_UPLOADS'], name)

        if option == 'logo_watermark':
            logo_upload = request.files.get('logo_upload')
            if not logo_upload or not allowed_file(logo_upload.filename):
                return "Please upload a valid logo (PNG/JPG).", 400
            
            logo = Image.open(logo_upload)
            logo = np.array(logo.convert('RGB'))
            h_logo, w_logo, _ = logo.shape

            # Resize logo if needed
            if h_logo > h_image or w_logo > w_image:
                scale = min(h_image / h_logo, w_image / w_logo)
                logo = cv2.resize(logo, (int(w_logo * scale), int(h_logo * scale)))
                h_logo, w_logo, _ = logo.shape

            # Calculate position
            center_y, center_x = h_image // 2, w_image // 2
            top_y, left_x = center_y - h_logo // 2, center_x - w_logo // 2
            bottom_y, right_x = top_y + h_logo, left_x + w_logo

            # Add logo watermark
            roi = image_logo[top_y:bottom_y, left_x:right_x]
            result = cv2.addWeighted(roi, 1, logo, 1, 0)
            image_logo[top_y:bottom_y, left_x:right_x] = result

        else:
            # Text watermark
            text_mark = request.form.get('text_mark', 'Watermark')
            cv2.putText(image_logo, text=text_mark, org=(w_image - 150, h_image - 20), fontFace=cv2.FONT_HERSHEY_COMPLEX,
                        fontScale=0.7, color=(0, 0, 255), thickness=2)

        # Save and return updated image
        img = Image.fromarray(image_logo, 'RGB')
        img.save(full_filename)
        return render_template('index.html', full_filename=full_filename)
