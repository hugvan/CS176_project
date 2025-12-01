import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import streamlit as st
import easyocr
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Set page config
st.set_page_config(page_title="EasyOCR Test", layout="wide")

st.title("🔍 EasyOCR Test App")
st.write("Upload an image to see how EasyOCR detects text")

# Initialize EasyOCR reader (cached so it only loads once)
@st.cache_resource
def load_reader():
    with st.spinner("Loading EasyOCR model... (this takes ~30 seconds first time)"):
        reader = easyocr.Reader(['en'], gpu=False)
    return reader

reader = load_reader()

# File uploader
uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # Load image
    image = Image.open(uploaded_file)
    
    # Convert to numpy array for EasyOCR
    image_np = np.array(image)
    
    # Create two columns for before/after
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Image")
        st.image(image, use_container_width=True)
    
    # Run OCR
    with st.spinner("Running OCR..."):
        results = reader.readtext(image_np)
    
    # Draw bounding boxes on image
    image_with_boxes = image.copy()
    draw = ImageDraw.Draw(image_with_boxes)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Display results
    with col2:
        st.subheader("Detected Text (with bounding boxes)")
        
        for (bbox, text, confidence) in results:
            # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            # Convert to flat list for polygon
            points = [tuple(point) for point in bbox]
            
            # Draw rectangle
            draw.polygon(points, outline='red', width=3) # type: ignore
            
            # Draw text label
            draw.text(points[0], text[:20], fill='red', font=font) # type: ignore
        
        st.image(image_with_boxes, use_container_width=True)
    
    # Show detected text in a table
    st.subheader("📝 Detected Text Details")
    
    if results:
        for i, (bbox, text, confidence) in enumerate(results):
            with st.expander(f"Text #{i+1}: {text[:50]}{'...' if len(text) > 50 else ''}"):
                st.write(f"**Full Text:** {text}")
                st.write(f"**Confidence:** {confidence:.2%}")
                st.write(f"**Bounding Box:** {bbox}")
    else:
        st.info("No text detected in the image")
    
    # Show raw data
    with st.expander("🔧 Raw OCR Output"):
        st.json(results)

else:
    st.info("👆 Upload an image to get started!")
    
    st.markdown("""
    ### How to use:
    1. Click "Browse files" above
    2. Select a screenshot or image with text
    3. Wait for OCR processing (~5-10 seconds)
    4. See detected text with bounding boxes!
    
    ### What EasyOCR returns:
    Each detected text region returns:
    - **Bounding box** - 4 corner coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    - **Text** - The detected string
    - **Confidence** - How confident the model is (0-1)
    """)

# Installation instructions in sidebar
with st.sidebar:
    st.header("📦 Installation")
    st.code("""
# Install required packages
pip install streamlit easyocr pillow numpy

# Run the app
streamlit run app.py
    """, language="bash")
    
    st.header("ℹ️ About EasyOCR")
    st.write("""
    - Deep learning based OCR
    - ~500MB model download (first time)
    - 80+ languages supported
    - Good accuracy (80-90%)
    - Returns bounding boxes automatically
    """)
