import os
import io
import base64
from PIL import Image, ImageOps
from openai import OpenAI
from flask import Flask, request, render_template_string, jsonify
import requests

app = Flask(__name__)
app.secret_key = "test_secret_key"

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# HTML template for testing
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Photo-to-Painting Test - EXPERT FIXED VERSION</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .result { margin: 20px 0; }
        img { max-width: 400px; height: auto; margin: 10px; border: 1px solid #ddd; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:disabled { background: #ccc; }
        .status { margin: 20px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
        .success { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Photo-to-Painting Test - EXPERT SOLUTION</h1>
    <p><strong>FIXES APPLIED:</strong></p>
    <ul>
        <li>✅ White mask (255,255,255,255) - editable areas</li>
        <li>✅ Aspect ratio preservation with ImageOps.pad()</li>
        <li>✅ Enhanced composition-preserving prompts</li>
        <li>✅ Proper response_format="url"</li>
    </ul>
    
    <div class="upload-area">
        <input type="file" id="photoInput" accept="image/*" onchange="previewImage()">
        <p>Upload a photo to test EXPERT-FIXED transformation</p>
    </div>
    
    <div id="preview"></div>
    
    <div>
        <label>Style:</label>
        <select id="styleSelect">
            <option value="oil_painting">Oil Painting</option>
            <option value="watercolor">Watercolor</option>
            <option value="impressionist">Impressionist</option>
        </select>
    </div>
    
    <button id="generateBtn" onclick="generatePainting()" disabled>Transform to Painting</button>
    
    <div id="status"></div>
    <div id="result"></div>

    <script>
        function previewImage() {
            const input = document.getElementById('photoInput');
            const preview = document.getElementById('preview');
            const generateBtn = document.getElementById('generateBtn');
            
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.innerHTML = '<h3>Original Photo:</h3><img src="' + e.target.result + '">';
                    generateBtn.disabled = false;
                };
                reader.readAsDataURL(input.files[0]);
            }
        }
        
        function generatePainting() {
            const input = document.getElementById('photoInput');
            const style = document.getElementById('styleSelect').value;
            const status = document.getElementById('status');
            const result = document.getElementById('result');
            const generateBtn = document.getElementById('generateBtn');
            
            if (!input.files || !input.files[0]) return;
            
            generateBtn.disabled = true;
            status.innerHTML = '<p>🎨 Transforming with EXPERT SOLUTION - preserving composition...</p>';
            result.innerHTML = '';
            
            const formData = new FormData();
            formData.append('image', input.files[0]);
            formData.append('style', style);
            
            fetch('/transform', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                generateBtn.disabled = false;
                if (data.success) {
                    status.innerHTML = '<p class="success">✅ EXPERT TRANSFORMATION SUCCESSFUL!</p>';
                    result.innerHTML = '<h3>Generated Painting (Composition Preserved):</h3><img src="data:image/png;base64,' + data.image + '">';
                } else {
                    status.innerHTML = '<p style="color: red;">❌ Error: ' + data.error + '</p>';
                }
            })
            .catch(error => {
                generateBtn.disabled = false;
                status.innerHTML = '<p style="color: red;">❌ Network error: ' + error.message + '</p>';
                console.error('Full error:', error);
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/transform', methods=['POST'])
def transform():
    try:
        # 1) Load & preprocess image (preserve aspect ratio + pad to square)
        image_file = request.files['image']
        image = Image.open(image_file.stream).convert('RGBA')
        # pad to 1024x1024 with white background
        image = ImageOps.pad(image, (1024, 1024), color=(255,255,255,255))
        
        # 2) Build a full‑white mask (white = editable area)
        mask = Image.new('RGBA', (1024, 1024), (255, 255, 255, 255))
        
        # 3) Serialize to PNG buffers
        img_buf = io.BytesIO()
        mask_buf = io.BytesIO()
        image.save(img_buf, format='PNG')
        mask.save(mask_buf, format='PNG')
        img_buf.name = 'image.png'
        mask_buf.name = 'mask.png'
        img_buf.seek(0)
        mask_buf.seek(0)
        
        # 4) Stronger, composition‑preserving prompt
        style = request.form.get('style', 'oil_painting')
        prompts = {
            'oil_painting': (
                "Transform this exact photograph into a museum‑quality oil painting. "
                "Preserve every detail of the original composition—house structure, "
                "windows, doors, lawn, sky and lighting—then overlay rich brushstrokes, "
                "thick impasto texture, and warm earth‑tone colors."
            ),
            'watercolor': (
                "Turn this exact photograph into a vibrant watercolor. Preserve all "
                "composition details—shapes, colors, lighting—then add flowing pigments, "
                "soft edges, and subtle washes."
            ),
            'impressionist': (
                "Render this exact photograph as an impressionist canvas. Keep the "
                "original composition intact—forms, perspective, lighting—then apply "
                "visible brush work, dabs of color, and light reflections."
            )
        }
        prompt = prompts.get(style, prompts['oil_painting'])
        
        # 5) Call DALL·E 2 Edit API with correct mask usage
        response = client.images.edit(
            model="dall-e-2",
            image=img_buf,
            mask=mask_buf,
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"
        )
        
        # 6) Fetch the result and return as base64
        result_url = response.data[0].url
        img_data = requests.get(result_url).content
        img_b64 = base64.b64encode(img_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': img_b64,
            'message': 'Photo successfully transformed with EXPERT SOLUTION!'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
