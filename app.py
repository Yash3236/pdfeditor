import streamlit as st
import io
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import colorsys  # Import for color conversion

# Optional imports for DOCX conversion
try:
    import pdf2docx
    DOCX_CONVERSION_AVAILABLE = True
except ImportError:
    DOCX_CONVERSION_AVAILABLE = False

# Helper function to convert any color format to hex
def to_hex_color(color):
    """Converts a color (name, hex, RGB tuple) to a hex code."""
    if isinstance(color, str):
        # Check if it's already a hex code
        if color.startswith('#'):
            return color
        # Try to convert named color to hex (basic support)
        try:
            import matplotlib.colors  # Requires matplotlib
            hex_color = matplotlib.colors.to_hex(color)  # Convert color name to hex
            return hex_color
        except ImportError:
            st.warning("matplotlib is recommended for converting color names to hex codes.")
            return '#000000'  # Default to black if matplotlib is not available
        except ValueError: #matplotlib couldn't parse
           st.warning(f"Invalid color name: {color}.  Using black instead.")
           return '#000000'
    elif isinstance(color, tuple) or isinstance(color, list):
        # Assume it's an RGB tuple (0-1 range)
        r, g, b = color
        return '#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255))
    else:
        st.warning(f"Unexpected color format: {color}.  Using black instead.")
        return '#000000'  # Default to black for unknown formats



# Initialize session state
def initialize_session_state():
    default_states = {
        'font_name': 'Helvetica',
        'font_size': 12,
        'text_color': '#000000',  # Default to black hex code
        'added_elements': []
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Function to convert PDF to DOCX (Preserving formatting as much as possible)
def convert_pdf_to_docx(pdf_path, docx_path):
    if not DOCX_CONVERSION_AVAILABLE:
        st.warning("DOCX conversion requires additional dependencies (pdf2docx and opencv).")
        return False
    
    try:
        cv = pdf2docx.Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)  # Convert all pages
        cv.close()
        return True
    except Exception as e:
        st.error(f"Error converting PDF to DOCX: {e}")
        return False

# Function to add text to PDF
def add_text_to_pdf(pdf_path, output_path, text, x, y, font_name, font_size, color):
    try:
        # Load the PDF
        existing_pdf = PdfReader(open(pdf_path, 'rb'))
        output_pdf = PdfWriter()

        # Create a PDF canvas to write on
        for page_num in range(len(existing_pdf.pages)):
            page = existing_pdf.pages[page_num]
            
            # Create a new PDF with Reportlab for the text
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)

            # Set font and color
            can.setFont(font_name, font_size)

            # *FORCE* hex conversion
            hex_color = to_hex_color(color)
            can.setFillColor(hex_color)

            # Add text (only to the first page)
            if page_num == 0:
                can.drawString(x * inch, (letter[1] - y) * inch, text)
            
            can.save()

            # Move to the beginning of the buffer
            packet.seek(0)
            new_pdf = PdfReader(packet)

            # Merge the new text with the existing PDF page
            page.merge_page(new_pdf.pages[0])
            output_pdf.add_page(page)

        # Write the modified PDF to a new file
        with open(output_path, "wb") as f:
            output_pdf.write(f)
        return True

    except Exception as e:
        st.error(f"Error adding text to PDF: {e}")
        return False

# Main Streamlit App
def main():
    # Initialize session state
    initialize_session_state()

    st.title("PDF Editor")

    # File Upload
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        input_pdf_path = None  # Initialize outside the try block
        output_pdf_path = None
        docx_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_input_pdf:
                input_pdf_path = temp_input_pdf.name
                temp_input_pdf.write(uploaded_file.getbuffer())

            # Display PDF information
            if input_pdf_path:  # Only proceed if input_pdf_path is valid
                try:
                    pdf_reader = PdfReader(open(input_pdf_path, 'rb'))
                    num_pages = len(pdf_reader.pages)
                    st.write(f"Number of pages: {num_pages}")

                    # Editing Tools
                    st.header("PDF Editing")

                    # Font Style Selection
                    font_options = ['Helvetica', 'Times-Roman', 'Courier', 'Symbol', 'ZapfDingbats']
                    st.session_state['font_name'] = st.selectbox(
                        "Font",
                        font_options,
                        index=font_options.index(st.session_state['font_name'])
                    )

                    st.session_state['font_size'] = st.number_input(
                        "Font Size",
                        min_value=8,
                        max_value=72,
                        value=st.session_state['font_size']
                    )
                    st.session_state['text_color'] = st.color_picker(
                        "Text Color",
                        value=st.session_state['text_color']  # Use session state value
                    )

                    # Text Input and Positioning
                    text_to_add = st.text_input("Text to Add")
                    x_position = st.number_input("X Position (inches)", min_value=0.0, max_value=8.5, value=1.0)
                    y_position = st.number_input("Y Position (inches from top)", min_value=0.0, max_value=11.0, value=1.0)

                    if st.button("Add Text"):
                        if text_to_add:
                            # Convert the color to hex *before* storing it
                            hex_color = to_hex_color(st.session_state['text_color'])
                            st.session_state['added_elements'].append({
                                'text': text_to_add,
                                'x': x_position,
                                'y': y_position,
                                'font_name': st.session_state['font_name'],
                                'font_size': st.session_state['font_size'],
                                'color': hex_color  # Store hex code
                            })
                        else:
                            st.warning("Please enter text to add.")

                    # Apply Edits and Download
                    if st.button("Apply Edits and Download"):
                        if st.session_state['added_elements']:
                            try:
                                # Create temporary output PDF
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_output_pdf:
                                    output_pdf_path = temp_output_pdf.name

                                success = True
                                for element in st.session_state['added_elements']:
                                    if input_pdf_path and output_pdf_path:
                                        success = add_text_to_pdf(
                                            input_pdf_path,
                                            output_pdf_path,
                                            element['text'],
                                            element['x'],
                                            element['y'],
                                            element['font_name'],
                                            element['font_size'],
                                            element['color']
                                        )
                                        if not success:
                                            break
                                    else:
                                        st.error("Input or Output PDF path is invalid.")
                                        success = False
                                        break  # Exit the loop

                                if success:
                                    if output_pdf_path:
                                        # PDF Download
                                        with open(output_pdf_path, "rb") as f:
                                            edited_pdf_bytes = f.read()
                                        st.download_button(
                                            label="Download Edited PDF",
                                            data=edited_pdf_bytes,
                                            file_name="edited.pdf",
                                            mime="application/pdf"
                                        )

                                        # Optional DOCX Conversion
                                        if DOCX_CONVERSION_AVAILABLE:
                                            # Create a temporary DOCX file
                                            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_docx:
                                                docx_path = temp_docx.name

                                            if convert_pdf_to_docx(output_pdf_path, docx_path):
                                                with open(docx_path, "rb") as f:
                                                    docx_bytes = f.read()
                                                st.download_button(
                                                    label="Download DOCX (Optional)",
                                                    data=docx_bytes,
                                                    file_name="converted.docx",
                                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                                )
                                            else:
                                                st.error("DOCX conversion failed.")


                                    else:
                                        st.error("Output PDF path is invalid during download.")


                                    # Clear added elements
                                    st.session_state['added_elements'] = []

                                else:
                                    st.error("Failed to apply all edits. See error messages above.")

                            except Exception as e:
                                st.error(f"An unexpected error occurred during apply edits: {e}")



                        else:
                            st.warning("No edits to apply. Add text first.")
                except Exception as e:
                   st.error(f"Error during processing of PDF content: {e}")
            else:
               st.error("Failed to create temporary PDF file.")


        except Exception as e:
            st.error(f"Error during file upload and processing: {e}")


        finally:  # Ensure cleanup happens even if errors occur
            # Clean up temporary files (moved inside the main if block and with error handling)
            if input_pdf_path:
                try:
                    os.unlink(input_pdf_path)
                except Exception as e:
                    st.warning(f"Could not delete temporary file: {input_pdf_path}.  Error: {e}")
            if output_pdf_path:
                try:
                    os.unlink(output_pdf_path)
                except Exception as e:
                    st.warning(f"Could not delete temporary file: {output_pdf_path}. Error: {e}")
            if docx_path and DOCX_CONVERSION_AVAILABLE:
                try:
                    os.unlink(docx_path)
                except Exception as e:
                    st.warning(f"Could not delete temporary file: {docx_path}.  Error: {e}")


if __name__ == "__main__":
    main()
