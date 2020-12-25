
import os
import uuid

from flask import Flask, flash, request, redirect, url_for

import image_processing
from breacher import Breacher

ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg'])

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16 megs

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/breach', methods = ['POST', 'GET'])
def breach():
    if 'file' not in request.files:
            print('No file part')
            return 'No file part', 400
    file = request.files['file']
    # if user does not select file, browser also
    # submit a empty part without filename
    if file.filename == '':
        print('No selected file')
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = ''
        try:
            _, ext = os.path.splitext(file.filename)
            filename = str(uuid.uuid4()) + ext
            file.save(filename)

            img = image_processing.open_file(filename)
            grid, targets, buffer, boxes = image_processing.run_extraction(img, False)
            
            breach = Breacher(grid, targets, buffer)
            seq, score = breach.solve()
            seq_txt = breach.positions_to_text(seq)

            resp = {
                'score': score,
                'sequence': seq,
                'sequence_text': seq_txt,
                'buffer_size': buffer,
                'targets': targets,
                'grid': grid
            }

            return resp, 200
        except:
            return 'Error', 500
        finally:
            if filename:
                os.remove(filename)

    return 'Failed to process', 400


def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext in ALLOWED_EXTENSIONS