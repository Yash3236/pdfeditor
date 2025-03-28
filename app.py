import streamlit as st
from PIL import Image
import io

def compress_image(image, quality):
    """Compresses a PIL Image object."""
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
    img_byte_arr.seek(0)
    return img_byte_arr

def crop_image(image, x1, y1, x2, y2):
    """Crops a PIL Image object."""
    return image.crop((x1, y1, x2, y2))

def resize_image(image, width=None, height=None, percentage=None, cm_width=None, cm_height=None, dpi=300, preserve_aspect_ratio=True):
    """Resizes a PIL Image object with flexible options."""
    original_width, original_height = image.size

    if percentage:
        width = int(original_width * (percentage / 100))
        height = int(original_height * (percentage / 100))
    elif width and height:
        pass  # Use provided pixel width and height
    elif cm_width and cm_height:
        width = int(cm_width * dpi / 2.54)  # Convert cm to pixels
        height = int(cm_height * dpi / 2.54) # cm to pixels
    else:
        raise ValueError("Provide either width/height (pixels), cm_width/cm_height (cm), or percentage for resizing.")

    if preserve_aspect_ratio:
        ratio = min(width / original_width, height / original_height)
        width = int(original_width * ratio)
        height = int(original_height * ratio)

    return image.resize((width, height), Image.LANCZOS)

def main():
    st.title("Advanced Image Editor")

    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        original_size = len(uploaded_file.getvalue())
        st.image(image, caption="Original Image", use_column_width=True)
        st.write(f"Original Size: {original_size / 1024:.2f} KB")

        # Compression
        st.header("Compression")
        quality = st.slider("Quality (1-100)", min_value=1, max_value=100, value=75)
        compressed_buffer = compress_image(image, quality)
        compressed_size = len(compressed_buffer.getvalue())
        compression_ratio = (1 - (compressed_size / original_size)) * 100
        st.write(f"Compressed Size: {compressed_size / 1024:.2f} KB")
        st.write(f"Compression Ratio: {compression_ratio:.2f}%")

        # Cropping
        st.header("Cropping")
        width, height = image.size
        x1 = st.number_input("Left X", min_value=0, max_value=width, value=0)
        y1 = st.number_input("Top Y", min_value=0, max_value=height, value=0)
        x2 = st.number_input("Right X", min_value=0, max_value=width, value=width)
        y2 = st.number_input("Bottom Y", min_value=0, max_value=height, value=height)

        if x1 < x2 and y1 < y2:
            cropped_image = crop_image(image, x1, y1, x2, y2)
            st.image(cropped_image, caption="Cropped Image", use_column_width=True)

            # Resizing
            st.header("Resizing")
            resize_option = st.radio("Resize Option", ["Pixels", "Centimeters", "Percentage"], index=0)
            preserve_aspect = st.checkbox("Preserve Aspect Ratio", value=True)

            dpi = st.number_input("DPI (Dots Per Inch)", min_value=1, max_value=1200, value=300)  # Default DPI

            try:
                if resize_option == "Pixels":
                    resize_width = st.number_input("Width (pixels)", min_value=1, max_value=width, value=width)
                    resize_height = st.number_input("Height (pixels)", min_value=1, max_value=height, value=height)
                    resized_image = resize_image(cropped_image, width=resize_width, height=resize_height, preserve_aspect_ratio=preserve_aspect)
                elif resize_option == "Centimeters":
                    cm_width = st.number_input("Width (cm)", min_value=0.1, max_value=width/ (dpi / 2.54), value=width / (dpi / 2.54)) #max value calculated
                    cm_height = st.number_input("Height (cm)", min_value=0.1, max_value=height/ (dpi / 2.54), value=height/ (dpi / 2.54)) #max value calculated

                    resized_image = resize_image(cropped_image, cm_width=cm_width, cm_height=cm_height, dpi=dpi, preserve_aspect_ratio=preserve_aspect)

                elif resize_option == "Percentage":
                    resize_percentage = st.number_input("Percentage (%)", min_value=1, max_value=500, value=100)
                    resized_image = resize_image(cropped_image, percentage=resize_percentage, preserve_aspect_ratio=preserve_aspect)
                else:
                    raise ValueError("Invalid resize option.")

                st.image(resized_image, caption="Resized Image", use_column_width=True)

            except ValueError as e:
                st.error(str(e))
                resized_image = cropped_image  # Use cropped image on error

            # Download
            st.header("Download")
            image_format = st.selectbox("Format", ["JPEG", "PNG"])
            if image_format == "JPEG":
                download_buffer = io.BytesIO()
                resized_image.save(download_buffer, format="JPEG", quality=quality)
                download_buffer.seek(0)
                st.download_button(
                    label="Download",
                    data=download_buffer,
                    file_name="modified_image.jpeg",
                    mime="image/jpeg"
                )
            elif image_format == "PNG":
                download_buffer = io.BytesIO()
                resized_image.save(download_buffer, format="PNG")
                download_buffer.seek(0)
                st.download_button(
                    label="Download",
                    data=download_buffer,
                    file_name="modified_image.png",
                    mime="image/png"
                )

        else:
            st.error("Invalid crop coordinates.")

if __name__ == "__main__":
    main()
