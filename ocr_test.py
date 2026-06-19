import easyocr

esr = easyocr.Reader(['en'])

img_path='img.png'

result = esr.readtext(img_path)

for line in result:
    text=line[1]
    confidence=line[2]

    print(f"Text: {text} | Confidence: {confidence}")
