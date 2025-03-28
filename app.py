import streamlit as st
import io
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf2docx import Converter
import docx
from docx.shared import Inches
import os

# Initialize session state
if 'font_name' not in st.session_state:
    st.session_state['font_name'] = 'Helvetica'  # Default font
if 'font_size' not in st.session_state:
    st.session_state['font_size'] = 12
if 'text_color' not in st.session_state:
    st.session_state['text_color'] = 'black'
if 'added_elements' not in st.session_state:
    st.session_state['added_elements'] = []  # Store added text elements and their properties

# Function to convert PDF to DOCX (Preserving formatting as much as possible)
def convert_pdf_to_docx(pdf_path, docx_path):
    try:
        cv = Converter(pdf_path)
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
        existing_pdf = PdfReader(pdf_path)
        page = existing_pdf.pages[0]  # Assuming adding to the first page

        # Create a PDF canvas to write on
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Register fonts if needed (e.g., for custom fonts)
        # pdfmetrics.registerFont(TTFont('CustomFont', 'path/to/custom_font.ttf'))  #Example custom font
        can.setFont(font_name, font_size)
        can.setFillColor(color)

        can.drawString(x * inch, (letter[1] - y) * inch, text) #Inverted Y coordinate
        can.save()

        # Move to the beginning of the buffer
        packet.seek(0)
        new_pdf = PdfReader(packet)

        # Merge the new text with the existing PDF
        page.merge_page(new_pdf.pages[0])

        # Write the modified PDF to a new file
        output_pdf = PdfWriter()
        output_pdf.add_page(page)  #Only add the edited page
        for i in range(1,len(existing_pdf.pages)):
            output_pdf.add_page(existing_pdf.pages[i])

        with open(output_path, "wb") as f:
            output_pdf.write(f)
        return True

    except Exception as e:
        st.error(f"Error adding text to PDF: {e}")
        return False

# Streamlit App
st.title("PDF Editor and Converter")

# File Upload
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

if uploaded_file is not None:
    # Display PDF information (optional)
    pdf_reader = PdfReader(uploaded_file)
    num_pages = len(pdf_reader.pages)
    st.write(f"Number of pages: {num_pages}")

    # Editing Tools
    st.header("PDF Editing")

    # Font Style Selection
    font_options = ['Helvetica', 'Times-Roman', 'Courier', 'Symbol', 'ZapfDingbats']
    st.session_state['font_name'] = st.selectbox("Font", font_options, index=font_options.index(st.session_state['font_name']))

    st.session_state['font_size'] = st.number_input("Font Size", min_value=8, max_value=72, value=st.session_state['font_size'])
    st.session_state['text_color'] = st.color_picker("Text Color", value=st.session_state['text_color'])

    # Text Input and Positioning
    text_to_add = st.text_input("Text to Add")
    x_position = st.number_input("X Position (inches)", min_value=0.0, max_value=8.5, value=1.0)
    y_position = st.number_input("Y Position (inches from top)", min_value=0.0, max_value=11.0, value=1.0)

    if st.button("Add Text"):
        if text_to_add:
            st.session_state['added_elements'].append({
                'text': text_to_add,
                'x': x_position,
                'y': y_position,
                'font_name': st.session_state['font_name'],
                'font_size': st.session_state['font_size'],
                'color': st.session_state['text_color']
            })
        else:
            st.warning("Please enter text to add.")

    # Apply Edits and Download
    if st.button("Apply Edits and Download PDF"):
        if st.session_state['added_elements']:
            try:
                # Save the uploaded PDF to a temporary file
                pdf_path = "temp.pdf"
                with open(pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                output_path = "edited.pdf"
                success = True

                for element in st.session_state['added_elements']:
                    success = add_text_to_pdf(pdf_path, output_path, element['text'], element['x'], element['y'], element['font_name'], element['font_size'], element['color'])
                    if not success:
                        break #Stop applying if one fails


                if success:
                    with open(output_path, "rb") as f:
                        edited_pdf_bytes = f.read()
                    st.download_button(
                        label="Download Edited PDF",
                        data=edited_pdf_bytes,
                        file_name="edited.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.error("Failed to apply all edits.  See error messages above.")


                # Clean up temporary file
                os.remove(pdf_path)
                if os.path.exists(output_path):
                    os.remove(output_path)  # Clean up the edited file too
                st.session_state['added_elements'] = [] # clear edits
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

        else:
            st.warning("No edits to apply. Add text first.")



    # PDF to DOCX Conversion
    st.header("PDF to DOCX Conversion")
    if st.button("Convert to DOCX"):
        try:
            # Save the uploaded PDF to a temporary file
            pdf_path = "temp.pdf"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            docx_path = "converted.docx"
            if convert_pdf_to_docx(pdf_path, docx_path):
                with open(docx_path, "rb") as f:
                    docx_bytes = f.read()

                st.download_button(
                    label="Download DOCX",
                    data=docx_bytes,
                    file_name="converted.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

            # Clean up temporary file
            os.remove(pdf_path)
            if os.path.exists(docx_path):
                os.remove(docx_path)

        except Exception as e:
            st.error(f"Conversion error: {e}")
