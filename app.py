import streamlit as st
from PIL import Image
import io
import os

def compress_image(image, quality):
    """Compresses a PIL Image object.

    Args:
        image: PIL Image object.
        quality: Compression quality (0-100).

    Returns:
        A BytesIO object containing the compressed image.
    """
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
    img_byte_arr = io.BytesIO(img_byte_arr.getvalue()) #Reset read pointer to the beginning
    return img_byte_arr


def crop_image(image, x1, y1, x2, y2):
    """Crops a PIL Image object.

    Args:
        image: PIL Image object.
        x1: Left coordinate of the crop box.
        y1: Top coordinate of the crop box.
        x2: Right coordinate of the crop box.
        y2: Bottom coordinate of the crop box.

    Returns:
        A PIL Image object containing the cropped image.
    """
    return image.crop((x1, y1, x2, y2))


def resize_image(image, width, height):
    """Resizes a PIL Image object.

    Args:
        image: PIL Image object.
        width: Desired width.
        height: Desired height.

    Returns:
        A PIL Image object containing the resized image.
    """
    return image.resize((width, height))


def main():
    st.title("Image Compressor, Cropper, and Resizer")

    uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        original_size = len(uploaded_file.getvalue())  # Size in bytes
        st.image(image, caption="Original Image", use_column_width=True)
        st.write(f"Original Size: {original_size / 1024:.2f} KB")


        # Compression Options
        st.header("Compression")
        quality = st.slider("Compression Quality (0-100)", min_value=1, max_value=100, value=75)
        compressed_buffer = compress_image(image, quality)
        compressed_size = len(compressed_buffer.getvalue())
        compression_ratio = (1 - (compressed_size / original_size)) * 100

        st.write(f"Compressed Size: {compressed_size / 1024:.2f} KB")
        st.write(f"Compression Ratio: {compression_ratio:.2f}%")


        # Cropping Functionality
        st.header("Cropping")
        width, height = image.size
        x1 = st.number_input("Left X", min_value=0, max_value=width, value=0)
        y1 = st.number_input("Top Y", min_value=0, max_value=height, value=0)
        x2 = st.number_input("Right X", min_value=0, max_value=width, value=width)
        y2 = st.number_input("Bottom Y", min_value=0, max_value=height, value=height)

        if x1 < x2 and y1 < y2:
            cropped_image = crop_image(image, x1, y1, x2, y2)
            st.image(cropped_image, caption="Cropped Image", use_column_width=True)

            #Resizing

            st.header("Resizing")
            resize_width = st.number_input("Resize Width", min_value=1, max_value=width, value=width)
            resize_height = st.number_input("Resize Height", min_value=1, max_value=height, value=height)

            resized_image = resize_image(cropped_image, resize_width, resize_height)
            st.image(resized_image, caption="Resized Image", use_column_width=True)


            # Download Button
            st.header("Download")

            image_format = st.selectbox("Choose format to download", ("JPEG", "PNG"))

            if image_format == "JPEG":

                 download_buffer = io.BytesIO()
                 resized_image.save(download_buffer, format="JPEG", quality=quality)  # Use the slider value
                 download_buffer.seek(0)


                 st.download_button(
                    label="Download Modified Image",
                    data=download_buffer,
                    file_name="modified_image.jpeg",
                    mime="image/jpeg",
                 )

            elif image_format == "PNG":
                 download_buffer = io.BytesIO()
                 resized_image.save(download_buffer, format="PNG")
                 download_buffer.seek(0)

                 st.download_button(
                    label="Download Modified Image",
                    data=download_buffer,
                    file_name="modified_image.png",
                    mime="image/png",
                 )



        else:
            st.error("Invalid cropping coordinates. Ensure Left X < Right X and Top Y < Bottom Y.")


if __name__ == "__main__":
    main()
