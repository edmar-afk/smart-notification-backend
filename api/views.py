# views.py

import re
import pytesseract
from PIL import Image
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["POST"])
def scan_school_id(request):
    image = request.FILES.get("image")

    if not image:
        return Response(
            {"error": "No image provided."},
            status=400
        )

    try:
        img = Image.open(image)

        text = pytesseract.image_to_string(img)

        print("OCR TEXT:")
        print(text)

        # Example ID formats:
        # 2024-12345
        # 2025-123456
        # 24-12345
        id_match = re.search(
            r"\b(?:20\d{2}[-\s]?\d{4,6}|\d{2}[-\s]?\d{4,6})\b",
            text
        )

        school_id = id_match.group(0) if id_match else ""

        return Response({
            "success": True,
            "text": text,
            "school_id": school_id,
        })

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=500
        )