import cv2
import numpy as np

# Read the input image
image = cv2.imread(r"G:\My Drive\Background\Naruto_2.jpg")

# Convert the image to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Threshold the grayscale image to get binary image
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)

# Check for horizontal lines
horizontal_kernel = np.ones((1, 10), np.uint8)
horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

# Check for vertical lines
vertical_kernel = np.ones((10, 1), np.uint8)
vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=1)

# Combine horizontal and vertical lines
lines = cv2.add(horizontal_lines, vertical_lines)

# Find contours of the lines
contours, hierarchy = cv2.findContours(lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Draw rectangles around the detected lines with thickness between 5 and 10 pixels
min_line_thickness = 5
max_line_thickness = 10
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    if min_line_thickness <= w <= max_line_thickness or min_line_thickness <= h <= max_line_thickness:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# Save the output image with detected lines
cv2.imwrite("output_image.jpg", image)

print("Detection complete. Result saved as output_image.jpg")
