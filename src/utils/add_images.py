import os
import base64

def encode_image_to_base64(image_path):
    """Convert an image file to a base64 string for embedding in HTML."""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        return encoded_string

def get_image_html(image_path, alt_text, width=120, height=80):
    """Generate HTML for an embedded image with given alt text and size."""
    encoded_image = encode_image_to_base64(image_path)
    if encoded_image:
        mime_type = 'image/png'
        return (
            f'<img src="data:{mime_type};base64,{encoded_image}" '
            f'alt="{alt_text}" style="width: {width}px; height: {height}px; object-fit: contain;">'
        )
    return None

def get_marketplace_logos_html():
    """Generate HTML for all marketplace logos with transparent brand-tinted backgrounds and a soft glow."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, "../images")
    marketplace_images = [
        ("aws-logo.png", "AWS", "#FF9900", "rgba(255,153,0,0.18)", "#ffe0b2", "https://aws.amazon.com/marketplace"),
        ("azure-logo.png", "Azure", "#007FFF", "rgba(0,127,255,0.18)", "#b3c6ff", "https://azuremarketplace.microsoft.com/en-us/marketplace"),
        ("gcp-logo.png", "Google Cloud", "#4285F4", "rgba(66,133,244,0.18)", "#e3f0ff", "https://console.cloud.google.com/marketplace")
    ]
    logos_html = []
    for img_file, name, color, bg_rgba, glow, href in marketplace_images:
        img_path = os.path.join(images_dir, img_file)
        img_html = get_image_html(img_path, name, width=240, height=160)
        if img_html:
            card_html = (
                f'<a href="{href}" target="_blank" style="text-decoration: none;">'
                f'<div style="display: flex; flex-direction: column; align-items: center; margin: 0 24px;">'
                f'<div style="display: flex; align-items: center; justify-content: center; '
                f'background: {bg_rgba}; border: 3px solid {color}; border-radius: 22px; '
                f'box-shadow: 0 0 32px 0 {glow}, 0 2px 12px rgba(0,0,0,0.10); width: 260px; height: 120px; '
                f'margin-bottom: 16px;">'
                f'{img_html}'
                f'</div>'
                f'</div></a>'
            )
            logos_html.append(card_html)
    return (
        '<div style="display: flex; justify-content: center; align-items: flex-end; margin-bottom: 2.5rem;">'
        + "".join(logos_html) +
        '</div>'
    )

# Example usage:
if __name__ == "__main__":
    # Generate and print the HTML
    html_output = get_marketplace_logos_html()
    print(html_output)

 