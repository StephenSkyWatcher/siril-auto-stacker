from PIL import Image
import numpy as np

def get_luminance_value(img_path):
    # 0 - 100
    img = np.array(Image.open(img_path))
    mean_rgb = np.mean(img.reshape(-1, 3), axis=0)
    luminance = np.sum(mean_rgb * [0.2126, 0.7152, 0.0722])
    return round((luminance/255) * 100)