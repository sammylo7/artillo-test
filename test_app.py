import os
import io
import base64
from PIL import Image
from openai import OpenAI
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

app = Flask(__name__)
app.secret_key = "test_secret_key"

# Set OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')

# HTML template for testing
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Photo-to-Painting Test</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
        .result { margin: 20px 0; }
        img { max-width: 400px; height: auto; margin: 10px; border: 1px solid #ddd; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:disabled { background: #ccc; }
        .status { margin: 20px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }
    </style>
</head>
<body>
    <h1>Photo-to-Painting Test</h1>
    <p>This test will verify if DALL-E 2 Edit API works on external hosting infrastructure.</p>
    
    <div class="upload-area">
        <input type="file" id="photoInput" accept="image/*" onchange="previewImage()">
        <p>Upload a photo to test transformation</p>
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
            status.innerHTML = '<p>Transforming photo to painting... This may take 20-30 seconds.</p>';
            result.innerHTML = '';
            
            const formData = new FormData();
            formData.append('image', input.files[0]);
            formData.append('style', style);
            
            fetch('/transform', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                generateBtn.disabled = false;
                if (data.success) {
                    status.innerHTML = '<p style="color: green;">✅ Transformation successful!</p>';
                    result.innerHTML = '<h3>Generated Painting:</h3><img src="data:image/png;base64,' + data.image + '">';
                } else {
                    status.innerHTML = '<p style="color: red;">❌ Error: ' + data.error + '</p>';
                }
            })
            .catch(error => {
                generateBtn.disabled = false;
                status.innerHTML = '<p style="color: red;">❌ Network error: ' + error.message + '</p>';
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
        # Get uploaded image
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'})
        
        image_file = request.files['image']
        style = request.form.get('style', 'oil_painting')
        
        # Convert to PIL Image
        image = Image.open(image_file.stream)
        
        # Resize and convert to RGBA
        image = image.convert('RGBA')
        image = image.resize((1024, 1024))
        
        # Create mask (full white mask for complete transformation)
        mask = Image.new('L', (1024, 1024), 255)
        
        # Convert images to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        mask_buffer = io.BytesIO()
        mask.save(mask_buffer, format='PNG')
        mask_buffer.seek(0)
        
        # Style prompts
        style_prompts = {
            'oil_painting': 'Convert this photograph into an oil painting with thick brushstrokes, rich colors, and painterly texture',
            'watercolor': 'Transform this into a watercolor painting with flowing pigments and soft edges',
            'impressionist': 'Create an impressionist painting with visible brushwork and light effects'
        }
        
        prompt = style_prompts.get(style, style_prompts['oil_painting'])
        
        # Call DALL-E 2 Edit API
        response = client.images.edit(
            image=img_buffer,
            mask=mask_buffer,
            prompt=prompt,
            n=1,
            size="1024x1024",
            model="dall-e-2"
        )
        
        # Get the generated image URL
        image_url = response['data'][0]['url']
        
        # Download the image and convert to base64
        import requests
        img_response = requests.get(image_url)
        img_base64 = base64.b64encode(img_response.content).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': img_base64,
            'message': 'Photo successfully transformed to painting!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
