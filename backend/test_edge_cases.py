
import requests
import os

# Base URL of the Flask application
BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_upload_and_compare_different_images():
    """
    Test case for uploading two different images and expecting a non-identical result.
    """
    # Paths to the two different images
    image_path1 = os.path.abspath("D:/ezz/elkheta-compair/edu-compare-wizard/101.jpg")
    image_path2 = os.path.abspath("D:/ezz/elkheta-compair/edu-compare-wizard/104.jpg")

    # Check if images exist
    assert os.path.exists(image_path1), f"Image not found at {image_path1}"
    assert os.path.exists(image_path2), f"Image not found at {image_path2}"

    # Files to be uploaded
    files = {
        'image1': ('101.jpg', open(image_path1, 'rb'), 'image/jpeg'),
        'image2': ('104.jpg', open(image_path2, 'rb'), 'image/jpeg')
    }

    # Make the request to the compare endpoint
    try:
        response = requests.post(f"{BASE_URL}/compare", files=files)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the JSON response
        comparison_result = response.json()

        # Assert that the images are not identical
        assert not comparison_result.get('is_identical'), "Test Failed: Expected is_identical to be False for different images"

        # Assert that the difference percentage is greater than 0
        assert comparison_result.get('difference_percentage', 0) > 0, "Test Failed: Expected difference_percentage to be greater than 0 for different images"

        print("Test passed: Comparison of different images is correct.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        print("Please ensure the backend server is running on http://127.0.0.1:5000")

if __name__ == "__main__":
    test_upload_and_compare_different_images()
