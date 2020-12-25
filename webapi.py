
import os
import uuid
import time
import io

from flask import Flask, request
from flask.helpers import send_file

import image_processing
from breacher import Breacher

ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg'])

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 #16 megs

@app.route('/')
def healthcheck():
    return 'Success', 200

@app.route('/breach', methods = ['POST'])
def breach():
    if 'file' not in request.files:
            print('No file part')
            return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        print('No selected file')
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = ''
        try:
            _, ext = os.path.splitext(file.filename)
            filename = str(uuid.uuid4()) + ext
            file.save(filename)

            start = time.perf_counter()

            img = image_processing.open_image(filename)
            if os.path.exists(filename): os.remove(filename)
            grid, targets, buffer, grid_bounds, boxes = image_processing.run_extraction(img, False)
            
            if grid is None:
                return 'Could not find grid', 400

            breach = Breacher(grid, targets, buffer)
            seq, score = breach.solve()
            seq_txt = breach.positions_to_text(seq)

            image_processing.overlay_result(img, seq, boxes, (255, 255, 0))

            img_cropped = img[grid_bounds[1]:grid_bounds[1]+grid_bounds[3], grid_bounds[0]:grid_bounds[0]+grid_bounds[2]]

            base64_image = image_processing.base64_encode_image(img_cropped, '.jpg').decode()

            elapsed = time.perf_counter() - start

            resp = {
                'score': score,
                'sequence': seq,
                'sequence_text': seq_txt,
                'buffer_size': buffer,
                'targets': targets,
                'grid': grid,
                'result_image': base64_image,
                'elapsed': elapsed
            }

            return resp, 200
        except Exception as e:
            print(e)
            return 'Error', 500
        finally:
            if filename and os.path.exists(filename):
                os.remove(filename)

    return 'Failed to process', 400


def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext in ALLOWED_EXTENSIONS