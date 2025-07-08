import numpy as np
from PIL import Image
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def generate_word_art_from_logo(image_path: str, text: str, output_path: str = "word_art.png"):
    # Load image and resize for better shape precision
    img = Image.open(image_path).convert("L")  # Convert to grayscale
    img = img.resize((800, 800), Image.LANCZOS)  # Resize for better resolution
    mask = np.array(img)

    # Create binary mask from white logo on black background
    threshold = 128
    binary_mask = np.where(mask > threshold, 255, 0).astype(np.uint8)
    inverted_mask = 255 - binary_mask  # WordCloud uses white as background

    # Repeat text to ensure it fills the shape
    print(f"Original text: {text}")
    text = text+ " "  # Add space to separate words
    repeated_text = text * 500  # You can adjust repetition as needed

    # Generate the word cloud
    wc = WordCloud(background_color="white", mode="RGB", max_words=1000,
                   mask=inverted_mask, contour_width=0, contour_color="black",
                   colormap="magma", prefer_horizontal=1.0).generate("just, do, it.")

    # Show and save
    plt.figure(figsize=(10, 10))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.show()
    print(f"Word art saved to: {output_path}")

# Example usage
if __name__ == "__main__":
    image_path = r"C:\Users\shash\Downloads\002-nike-logos-swoosh-white.jpg"  # The swoosh file you uploaded
    text = "just do it"
    generate_word_art_from_logo(image_path, text)
