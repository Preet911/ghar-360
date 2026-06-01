# import easyocr
# import re
# import os
# from pdf2image import convert_from_path

# import cv2
# import easyocr
# import re

# # ✅ Aadhaar Verhoeff checksum
# multiplication_table = [
#     [0,1,2,3,4,5,6,7,8,9],
#     [1,2,3,4,0,6,7,8,9,5],
#     [2,3,4,0,1,7,8,9,5,6],
#     [3,4,0,1,2,8,9,5,6,7],
#     [4,0,1,2,3,9,5,6,7,8],
#     [5,9,8,7,6,0,4,3,2,1],
#     [6,5,9,8,7,1,0,4,3,2],
#     [7,6,5,9,8,2,1,0,4,3],
#     [8,7,6,5,9,3,2,1,0,4],
#     [9,8,7,6,5,4,3,2,1,0]
# ]
# permutation_table = [
#     [0,1,2,3,4,5,6,7,8,9],
#     [1,5,7,6,2,8,3,0,9,4],
#     [5,8,0,3,7,9,6,1,4,2],
#     [8,9,1,6,0,4,3,5,2,7],
#     [9,4,5,3,1,2,6,8,7,0],
#     [4,2,8,6,5,7,3,9,0,1],
#     [2,7,9,3,8,0,6,4,1,5],
#     [7,0,4,6,9,1,3,2,5,8]
# ]

# def verhoeff_validate(num):
#     c = 0
#     for i, item in enumerate(reversed(num)):
#         c = multiplication_table[c][permutation_table[(i % 8)][int(item)]]
#     return c == 0

# # ✅ Aadhaar extractor
# def extract_aadhaar(text_all):
#     # Step 1: Find any long digit sequence (with/without spaces)
#     candidates = re.findall(r"(?:\d\s*){10,16}", text_all)
#     print(candidates)

#     for cand in candidates:
#         # Remove spaces
#         num = re.sub(r"\s+", "", cand)
#         print(num)

#         # Step 2: Truncate if longer than 12 digits
#         if len(num) > 12:
#             num = num[:12]
#         print(num)

#         # Step 3: Only accept 12-digit numbers
#         if len(num) == 12 and verhoeff_validate(num):
#             return {"aadhaar_number": f"{num[0:4]} {num[4:8]} {num[8:12]}"}

#     return {"aadhaar_number": None}

# # ✅ OCR
# reader = easyocr.Reader(['en'])
# img_path = "C:/Users/preet/Downloads/aadhar.jpg"  # replace with your Aadhaar image
# results = reader.readtext(img_path, detail=0)

# text_all = " ".join(results)
# print(" Raw OCR Extracted Text:\n", text_all)

# aadhaar = extract_aadhaar(text_all)
# print("\n Final Extracted Aadhaar Number:\n", aadhaar)

import easyocr
import re
import os
import cv2
from pdf2image import convert_from_path

# ✅ Aadhaar Verhoeff checksum
multiplication_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0]
]
permutation_table = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8]
]

def verhoeff_validate(num):
    c = 0
    for i, item in enumerate(reversed(num)):
        c = multiplication_table[c][permutation_table[(i % 8)][int(item)]]
    return c == 0

# ✅ Aadhaar extractor
def extract_aadhaar(text_all):
    # Step 0: Remove any mobile number patterns (10-digit after "Mobile")
    text_all = re.sub(r"Mobile\s*No\.?:?\s*\d{10}", "", text_all, flags=re.IGNORECASE)

    # Step 1: Find digit sequences
    candidates = re.findall(r"(?:\d\s*){12,16}", text_all)  # Aadhaar = 12 digits
    print("Candidates found:", candidates)

    for cand in candidates:
        # Remove spaces
        num = re.sub(r"\s+", "", cand)

        # Step 2: Truncate if longer than 12 digits
        if len(num) > 12:
            num = num[:12]

        # Step 3: Only accept 12-digit valid Aadhaar
        if len(num) == 12 and verhoeff_validate(num):
            return {"aadhaar_number": f"{num[0:4]} {num[4:8]} {num[8:12]}"}

    return {"aadhaar_number": None}

# ✅ OCR
reader = easyocr.Reader(['en'])
img_path = "C:/Users/preet/Downloads/aadhar.jpg"  # replace with your Aadhaar image
results = reader.readtext(img_path, detail=0)

text_all = " ".join(results)
print("\n Raw OCR Extracted Text:\n", text_all)

aadhaar = extract_aadhaar(text_all)
print("\n Final Extracted Aadhaar Number:\n", aadhaar)
