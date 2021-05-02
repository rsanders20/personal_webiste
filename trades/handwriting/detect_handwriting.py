from google.cloud import vision
import io
import os
import base64
import requests

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/ryan/keys/nodal-deck-312502-9494dd06fe8f.json'


def detect_document(content_string):
    """Detects document features in an image."""
    # decoded = base64.b64decode(content_string)
    # # content = decoded
    # file_like_object = io.BytesIO(decoded)
    # # content = file_like_object
    # content = file_like_object.read()
    #
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    content_strings = content_string.split(",")
    print(content_strings[0])
    image.content = base64.b64decode(content_strings[1])
    # req = {
    #     'image': {'content': content},
    #     'features': [{'type': 'DOCUMENT_TEXT_DETECTION'}],
    # }
    #

    # json_data = {
    #     "requests": [
    #         {"image": {"content": content_string},
    #          "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
    #          }
    #     ]
    # }
    #
    # response = client.document_text_detection(requests=json_data)

    response = client.document_text_detection(image=image)


    word_list = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            print('\nBlock confidence: {}\n'.format(block.confidence))

            for paragraph in block.paragraphs:
                print('Paragraph confidence: {}'.format(
                    paragraph.confidence))

                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    print('Word text: {} (confidence: {})'.format(
                        word_text, word.confidence))
                    word_list.append(word_text)

                    for symbol in word.symbols:
                        print('\tSymbol: {} (confidence: {})'.format(
                            symbol.text, symbol.confidence))

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        word_string = ' '.join(word_list)
        return word_string


if __name__ == "__main__":
    path = r'/home/ryan/Desktop/dev/personal_website/assets/handwriting/ab92e0bc80aaa280f73bef31d099bf39.jpg'
    detect_document(path)