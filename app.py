import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import streamlit as st
import easyocr
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import re

# Set page config
st.set_page_config(page_title="SmartBlur", layout="wide")

st.title("🔍 SmartBlur")
st.write("Upload an image - click on detected text regions to blur/unblur them")

# Initialize EasyOCR reader
@st.cache_resource
def load_reader():
    with st.spinner("Loading EasyOCR model... (this takes ~30 seconds first time)"):
        reader = easyocr.Reader(['en'], gpu=False)
    return reader

reader = load_reader()

# Personal information detection patterns
def detect_sensitive_info(text):
    """Detect if text contains sensitive personal information"""
    text_lower = text.lower()
    
    # Email pattern
    if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.?[A-Z|a-z]{2,}\b', text):
        return True, "Email"
    
    # Phone number patterns
    phone_patterns = [
        r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',
        r'\b\d{10,11}\b',
        r'\+\d{1,3}\s?\d{8,12}\b',
        r'\(\d{3}\)\s*\d{3}\b',
        r'\b\d{4}\b',
        r'\b\d{3}-\d{3}\b',
    ]
    for pattern in phone_patterns:
        if re.search(pattern, text):
            return True, "Phone"
    
    # SSN pattern
    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', text):
        return True, "SSN"
    if re.search(r'\b\d{3}-\d{2}\b', text) or re.search(r'\b\d{2}-\d{4}\b', text):
        return True, "SSN"
    
    # Credit card pattern
    if re.search(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', text):
        return True, "Credit Card"
    if re.search(r'\b\d{4}\s+\d{4}\b', text):
        return True, "Credit Card"
    
    # Address indicators
    address_keywords = ['street', 'st.', 'avenue', 'ave.', 'ave ', 'road', 'rd.', 
                        ' drive ', 'dr.', 'boulevard', 'blvd.', 'blvd ', ' lane ', 'ln.',
                        'apartment', 'apt.', ' apt ', 'suite', 'ste.',  'court', 'ct.', 
                        'place', 'pl.', 'circle', 'cir.', 'parkway', 'pkwy']
    if any(keyword in text_lower for keyword in address_keywords):
        return True, "Address"
    
    if re.search(r'\b\d{1,5}\s+[A-Z][a-z]+(\s+[A-Z][a-z]+)*\b', text):
        return True, "Address"
    
    if re.search(r'\b\d{5}(-\d{4})?\b', text):
        return True, "Address"
    
    if re.search(r'\b[A-Z][a-z]+,\s*[A-Z]{2}\s+\d{5}\b', text):
        return True, "Address"
    
    # Check custom patterns
    if 'custom_patterns' in st.session_state:
        for pattern_data in st.session_state.custom_patterns:
            if pattern_data['enabled']:
                try:
                    if re.search(pattern_data['pattern'], text, re.IGNORECASE):
                        return True, f"Custom: {pattern_data['name']}"
                except re.error:
                    pass  # Skip invalid patterns
    
    return False, None

def blur_region(image, bbox, blur_strength=25):
    """Blur a specific region of the image"""
    x_coords = [point[0] for point in bbox]
    y_coords = [point[1] for point in bbox]
    
    x_min, x_max = int(min(x_coords)), int(max(x_coords))
    y_min, y_max = int(min(y_coords)), int(max(y_coords))
    
    x_min = max(0, x_min)
    y_min = max(0, y_min)
    x_max = min(image.width, x_max)
    y_max = min(image.height, y_max)
    
    region = image.crop((x_min, y_min, x_max, y_max))
    blurred_region = region.filter(ImageFilter.GaussianBlur(radius=blur_strength))
    
    result_image = image.copy()
    result_image.paste(blurred_region, (x_min, y_min))
    
    return result_image

def create_annotated_image(image, results, blurred_indices):
    """Create image with numbered bounding boxes"""
    img_copy = image.copy()
    draw = ImageDraw.Draw(img_copy)
    
    try:
        font = ImageFont.truetype("Arial.ttf", 24)
        small_font = ImageFont.truetype("Arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    for i, (bbox, text, confidence) in enumerate(results):
        points = [tuple(point) for point in bbox]
        
        # Color based on whether it's blurred
        if i in blurred_indices:
            color = 'red'
            status = "BLURRED"
        else:
            is_sensitive, info_type = detect_sensitive_info(text)
            if is_sensitive:
                color = 'orange'
                status = info_type
            else:
                color = 'green'
                status = "Safe"
        
        # Draw bounding box
        draw.polygon(points, outline=color, width=3)
        
        # Draw number in circle
        x, y = points[0]
        circle_radius = 20
        draw.ellipse([x-circle_radius, y-circle_radius, x+circle_radius, y+circle_radius], 
                     fill=color, outline='white', width=2)
        
        # Draw number
        number_text = str(i + 1)
        bbox_text = draw.textbbox((x, y), number_text, font=font)
        text_width = bbox_text[2] - bbox_text[0]
        text_height = bbox_text[3] - bbox_text[1]
        draw.text((x - text_width//2, y - text_height//2), number_text, fill='white', font=font)
        
        # Draw status label
        draw.text((x + 25, y - 10), status, fill=color, font=small_font) # type: ignore
    
    return img_copy

# Initialize session state
if 'blurred_indices' not in st.session_state:
    st.session_state.blurred_indices = set()
if 'ocr_results' not in st.session_state:
    st.session_state.ocr_results = None
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
if 'auto_detect_applied' not in st.session_state:
    st.session_state.auto_detect_applied = False
if 'custom_patterns' not in st.session_state:
    st.session_state.custom_patterns = []

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    blur_strength = st.slider("Blur Strength", 5, 50, 25, 5)
    
    st.subheader("Auto-detect on upload:")
    auto_blur_emails = st.checkbox("Emails", value=True)
    auto_blur_phones = st.checkbox("Phone Numbers", value=True)
    auto_blur_ssn = st.checkbox("SSN", value=True)
    auto_blur_cards = st.checkbox("Credit Cards", value=True)
    auto_blur_addresses = st.checkbox("Addresses", value=True)
    auto_blur_custom = st.checkbox("Custom Patterns", value=True)
    
    st.markdown("---")
    
    # Custom Patterns Section
    st.subheader("🔧 Custom Patterns")
    
    with st.expander("Add Custom Pattern"):
        pattern_name = st.text_input("Pattern Name", placeholder="e.g., Employee ID", key="pattern_name_input")
        pattern_regex = st.text_input("Regex Pattern", placeholder="e.g., EMP-\\d{4}-\\d{4}", key="pattern_regex_input")
        
        col_add, col_test = st.columns(2)
        
        with col_add:
            if st.button("Add Pattern", use_container_width=True):
                if pattern_name and pattern_regex:
                    try:
                        # Test if regex is valid
                        re.compile(pattern_regex)
                        st.session_state.custom_patterns.append({
                            'name': pattern_name,
                            'pattern': pattern_regex,
                            'enabled': True
                        })
                        st.success(f"✅ Added: {pattern_name}")
                        # Reset auto-detect so new pattern is applied
                        st.session_state.auto_detect_applied = False
                        st.rerun()
                    except re.error as e:
                        st.error(f"❌ Invalid regex: {e}")
                else:
                    st.warning("Please fill both fields")
        
        with col_test:
            test_text = st.text_input("Test text", placeholder="Test your pattern", key="test_text_input")
            if test_text and pattern_regex:
                try:
                    if re.search(pattern_regex, test_text, re.IGNORECASE):
                        st.success("✅ Match!")
                    else:
                        st.info("No match")
                except re.error:
                    st.error("Invalid regex")
    
    # Display existing custom patterns
    if st.session_state.custom_patterns:
        st.write("**Active Custom Patterns:**")
        
        patterns_to_remove = []
        
        for i, pattern in enumerate(st.session_state.custom_patterns):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                enabled = st.checkbox(
                    f"**{pattern['name']}**",
                    value=pattern['enabled'],
                    key=f"pattern_enabled_{i}"
                )
                st.caption(f"`{pattern['pattern']}`")
                st.session_state.custom_patterns[i]['enabled'] = enabled
            
            with col2:
                if st.button("🗑️", key=f"delete_pattern_{i}"):
                    patterns_to_remove.append(i)
        
        # Remove patterns after iteration
        for i in reversed(patterns_to_remove):
            st.session_state.custom_patterns.pop(i)
            st.session_state.auto_detect_applied = False
            st.rerun()
    else:
        st.info("No custom patterns added yet")
    
    st.markdown("---")
    st.info("🎯 **How to use:**\n\n1. Upload image\n2. Auto-detection marks sensitive info\n3. Click number buttons to toggle blur\n4. Download result")

# File uploader
uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # Check if new file uploaded - reset state
    if st.session_state.uploaded_image != uploaded_file.name:
        st.session_state.uploaded_image = uploaded_file.name
        st.session_state.blurred_indices = set()
        st.session_state.ocr_results = None
        st.session_state.auto_detect_applied = False
    
    # Load image
    image = Image.open(uploaded_file)
    
    # Run OCR only if not already done
    if st.session_state.ocr_results is None:
        image_np = np.array(image)
        with st.spinner("Running OCR..."):
            results = reader.readtext(image_np)
        st.session_state.ocr_results = results
    else:
        results = st.session_state.ocr_results
    
    # Auto-detect sensitive info on first load
    if not st.session_state.auto_detect_applied:
        for i, (bbox, text, confidence) in enumerate(results):
            is_sensitive, info_type = detect_sensitive_info(text)
            
            should_blur = False
            if is_sensitive:
                if info_type.startswith("Custom:") and auto_blur_custom: # type: ignore
                    should_blur = True
                elif info_type == "Email" and auto_blur_emails:
                    should_blur = True
                elif info_type == "Phone" and auto_blur_phones:
                    should_blur = True
                elif info_type == "SSN" and auto_blur_ssn:
                    should_blur = True
                elif info_type == "Credit Card" and auto_blur_cards:
                    should_blur = True
                elif info_type == "Address" and auto_blur_addresses:
                    should_blur = True
            
            if should_blur:
                st.session_state.blurred_indices.add(i)
        
        st.session_state.auto_detect_applied = True
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📍 Detected Text")
        annotated_image = create_annotated_image(image, results, st.session_state.blurred_indices)
        st.image(annotated_image, use_container_width=True)
        
        st.caption("🔴 Red = Blurred | 🟠 Orange = Sensitive (unblurred) | 🟢 Green = Safe")
    
    with col2:
        st.subheader("🖼️ Preview")
        
        # Generate preview with blurred regions
        preview_image = image.copy()
        for i in st.session_state.blurred_indices:
            bbox = results[i][0]
            preview_image = blur_region(preview_image, bbox, blur_strength)
        
        st.image(preview_image, use_container_width=True)
        
        # Download button
        from io import BytesIO
        buf = BytesIO()
        preview_image.save(buf, format="PNG")
        st.download_button(
            label="📥 Download Redacted Image",
            data=buf.getvalue(),
            file_name="redacted_image.png",
            mime="image/png"
        )
        
        st.metric("Items Blurred", len(st.session_state.blurred_indices))
    
    # Interactive text selection area
    st.markdown("---")
    st.subheader("🎯 Click to Toggle Blur")
    
    # Display all detected text as clickable buttons in a grid
    cols_per_row = 4
    for row_start in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for idx, col_idx in enumerate(range(row_start, min(row_start + cols_per_row, len(results)))):
            with cols[idx]:
                bbox, text, confidence = results[col_idx]
                is_sensitive, info_type = detect_sensitive_info(text)
                
                # Determine button appearance
                if col_idx in st.session_state.blurred_indices:
                    button_type = "primary"
                    prefix = "🔴"
                    status = "BLURRED"
                elif is_sensitive:
                    button_type = "secondary"
                    prefix = "🟠"
                    status = info_type if info_type else "Sensitive"
                else:
                    button_type = "secondary"
                    prefix = "🟢"
                    status = "Safe"
                
                # Create button label
                text_preview = text[:20] + "..." if len(text) > 20 else text
                button_label = f"{prefix} #{col_idx + 1}\n{text_preview}\n({status})"
                
                # Button click toggles blur
                if st.button(button_label, key=f"toggle_{col_idx}", 
                           type=button_type, use_container_width=True):
                    if col_idx in st.session_state.blurred_indices:
                        st.session_state.blurred_indices.remove(col_idx)
                    else:
                        st.session_state.blurred_indices.add(col_idx)
                    st.rerun()
    
    # Bulk actions
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        if st.button("🔴 Blur All Sensitive", use_container_width=True):
            for i, (bbox, text, confidence) in enumerate(results):
                is_sensitive, _ = detect_sensitive_info(text)
                if is_sensitive:
                    st.session_state.blurred_indices.add(i)
            st.rerun()
    
    with col_b:
        if st.button("🟢 Unblur All", use_container_width=True):
            st.session_state.blurred_indices = set()
            st.rerun()
    
    with col_c:
        if st.button("🔄 Reset to Auto-Detect", use_container_width=True):
            st.session_state.blurred_indices = set()
            st.session_state.auto_detect_applied = False
            st.rerun()

else:
    st.info("👆 Upload an image to get started!")
    
    st.markdown("""
    ### 🛡️ How This Works:
    
    1. **Upload** an image with text
    2. **Auto-detection** marks sensitive information (based on sidebar settings)
    3. **Click numbered buttons** below the image to toggle blur for each text region
    4. **Preview updates** in real-time
    5. **Download** your redacted image!
    
    ### 🎯 Features:
    - 🔴 Red numbers = Currently blurred
    - 🟠 Orange numbers = Detected as sensitive (not blurred)
    - 🟢 Green numbers = Safe content
    - Click any number to toggle blur on/off
    - Bulk actions: Blur all sensitive, Unblur all, or Reset
    - 🔧 **Custom regex patterns** for specific use cases
    
    ### 🔍 Auto-Detects:
    - 📧 Email addresses
    - 📱 Phone numbers (all formats)
    - 🆔 Social Security Numbers
    - 💳 Credit card numbers
    - 🏠 Street addresses
    - 🔧 Custom patterns you define
    """)

st.markdown("---")
st.caption("⚠️ Always review results before sharing. This tool provides basic privacy protection.")

st.markdown("""
<style>
    @import url('https://tetunori.github.io/fluent-emoji-webfont/dist/FluentEmojiFlat.css');

    *:not(span[data-testid="stIconMaterial"]) {
        font-family: -apple-system, BlinkMacSystemFont, 'Fluent Emoji Flat', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)