# SmartBlur - Privacy Redaction Tool
Vaughn Aquino, Aeron Penaflorida

A web-based application built with Streamlit that automatically detects and blurs sensitive information in images using OCR (Optical Character Recognition) technology.

##  Features

- **Automatic Detection**: Uses EasyOCR to extract text from images
- **Smart Recognition**: Detects emails, phone numbers, SSNs, credit cards, and addresses
- **Custom Patterns**: Add your own regex patterns for specific use cases
- **Interactive Interface**: Click-to-toggle blur for manual control
- **Real-time Preview**: See changes instantly before downloading
- **Bulk Actions**: Blur all sensitive items or reset with one click

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download

```bash
git clone https://github.com/hugvan/CS176_project.git
cd CS176_project
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install streamlit easyocr pillow numpy
```

**Package Details:**
- `streamlit` (1.28+) - Web application framework
- `easyocr` (1.7+) - OCR engine for text detection
- `pillow` (10.0+) - Image processing library
- `numpy` (1.24+) - Numerical computing

### Step 4: First Run Setup

On first run, EasyOCR will download model files (~500MB). This happens automatically and only once.

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## Usage Guide

### Basic Workflow

1. **Upload an Image**
   - Click "Browse files" or drag-and-drop
   - Supports PNG, JPG, JPEG formats
   - OCR processing takes 5-10 seconds

2. **Review Auto-Detection**
   - Sensitive information is automatically marked
   - 🔴 Red boxes = Currently blurred
   - 🟠 Orange boxes = Detected as sensitive (not blurred)
   - 🟢 Green boxes = Safe content

3. **Manual Adjustment**
   - Click numbered buttons below the image
   - Toggle blur on/off for each text region
   - Preview updates in real-time

4. **Download Result**
   - Click "📥 Download Redacted Image"
   - Saves as PNG with selected regions blurred

### Sidebar Settings

#### Blur Strength
- Adjust blur intensity (5-50)
- Higher values = more blur
- Default: 25 (recommended)

#### Auto-Detect Options
Enable/disable automatic detection for:
- ✅ Email addresses
- ✅ Phone numbers
- ✅ Social Security Numbers (SSN)
- ✅ Credit card numbers
- ✅ Street addresses
- ✅ Custom patterns

### Custom Regex Patterns

Add patterns for organization-specific sensitive data:

1. **Click "Add Custom Pattern"**
2. **Enter Pattern Name**: e.g., "Employee ID"
3. **Enter Regex Pattern**: e.g., `EMP-\d{4}-\d{4}`
4. **Test Pattern**: Use test field to verify
5. **Click "Add Pattern"**

**Example Patterns:**

```regex
EMP-\d{4}              → Employee IDs (EMP-1234)
\$\d+\.\d{2}           → Dollar amounts ($123.45)
CONF-[A-Z0-9]{8}       → Confidential codes
[A-Z]{2}\d{6}          → License plates (AB123456)
Case #\d{4}-\d{4}      → Case numbers (Case #2024-0001)
```

**Pattern Management:**
- ✅ Enable/disable with checkbox
- 🗑️ Delete unwanted patterns
- Patterns persist during session

### Bulk Actions

- **🔴 Blur All Sensitive**: Auto-blur everything detected
- **🟢 Unblur All**: Remove all blurs
- **🔄 Reset to Auto-Detect**: Return to initial state

---

## Model Details

### OCR Engine: EasyOCR

**Architecture:**
- **Detection Model**: CRAFT (Character Region Awareness for Text detection)
- **Recognition Model**: CRNN (Convolutional Recurrent Neural Network)
- **Language**: English (can be extended to 80+ languages)

**Performance:**
- **Accuracy**: ~80-90% on clear, well-lit images
- **Speed**: 5-10 seconds per image (CPU mode)
- **Model Size**: ~500MB download (one-time)

**How It Works:**

1. **Text Detection**
   - CRAFT model identifies text regions
   - Returns bounding box coordinates for each word
   - Format: `[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]`

2. **Text Recognition**
   - CRNN extracts actual text from each region
   - Returns text string + confidence score (0-1)

3. **Pattern Matching**
   - Regex patterns scan detected text
   - Identifies sensitive information types
   - Custom patterns checked first (highest priority)

4. **Blurring**
   - Gaussian blur applied to sensitive regions
   - Adjustable blur radius (5-50 pixels)
   - Preserves original image quality for non-sensitive areas

### Detection Patterns

**Built-in Patterns:**

| Type | Pattern | Example |
|------|---------|---------|
| Email | `[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z\|a-z]{2,}` | john.doe@example.com |
| Phone | Multiple formats | (555) 123-4567, 555-123-4567 |
| SSN | `\d{3}-\d{2}-\d{4}` | 123-45-6789 |
| Credit Card | `\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}` | 4111-1111-1111-1111 |
| Address | Keyword + pattern matching | 123 Main Street |

---

## ⚠️ Limitations

### Current Limitations

1. **OCR Accuracy**
   - Struggles with handwriting (~40-50% accuracy)
   - Poor performance on low-resolution images
   - Requires clear contrast between text and background
   - May miss text at angles >15 degrees

2. **Pattern Detection**
   - Relies on regex patterns (not semantic understanding)
   - May miss unconventional formats
   - False positives possible (e.g., phone-like number sequences)
   - Cannot detect context (e.g., "My SSN is..." without the number)

3. **Security**
   - Basic privacy protection only
   - Not suitable for legal/compliance requirements
   - Manual review always recommended
   - No encryption of uploaded images

4. **Language Support**
   - Currently English only
   - International phone/address formats may not be detected

### Known Issues

- **Split text**: Phone numbers split across lines may not be detected
- **Stylized fonts**: Decorative fonts reduce accuracy
- **Dark images**: Low-light images have poor OCR results

---

## 🚧 Future Improvements

### Short-term 

- [ ] **Batch Processing**: Upload and process multiple images
- [ ] **Export Settings**: Save custom patterns for reuse
- [ ] **Undo/Redo**: Step backward through changes
- [ ] **PDF Support**: Direct PDF upload and processing

### Long-term

- [ ] **Advanced Detection**:
  - Named Entity Recognition (NER) for names
  - Date of birth detection
  - Driver's license numbers
  - Passport numbers
  
- [ ] **Other Blur Options**:
  - Pixelation instead of blur
  - Black box redaction
  - Custom blur shapes

- [ ] **UI Enhancements**:
  - Zoom in/out on image
  - Click directly on image regions (via custom component)
  - Drag-to-select multiple regions
  - Keyboard shortcuts

---

## 🙏 Acknowledgments

- **EasyOCR**: Open-source OCR library by JaidedAI
- **Streamlit**: Framework for rapid app development
- **Pillow**: Python Imaging Library
- **CS 176**: Computer Vision course at UP Diliman

---

## 🔒 Privacy Notice

**Important**: This tool processes images locally during your session. However:
- Images are not permanently stored on the server
- EasyOCR downloads happen once (model files only)
- No data is sent to external services except initial model download
- Always review results before sharing sensitive documents
- For highly sensitive data, use this tool offline or deploy locally

**This tool is NOT a substitute for professional data security solutions.**
