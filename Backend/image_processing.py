# This file handles image processing, including determining the grid and target sequences
#builtin
import math
import time
import base64
import os

#pip
import cv2
import imutils
import numpy
from skimage.metrics import structural_similarity

#ours
from breacher import Breacher

def build_source_codes():
    '''Reads in the code images for later compariosn'''
    images = {} # clear it out just in case
    codes = ['1C', '7A', '55', 'BD', 'E9', 'FF']

    for code in codes:
        fp = 'codes/{0}.png'.format(code)
        if not os.path.exists(fp):
            fp = 'Backend/' + fp
        im = cv2.imread(fp, cv2.IMREAD_UNCHANGED)
        images[code] = im
    
    return images

def determine_code(region, code_images, extra_pad = 0):
    '''Determine which code is in the provided region by comparing images. Optional extra padding around the region, taking the resizing into account'''
    closest_code = None
    closest_score = -1
    for code in code_images: #infinitely faster than doing OCR with tesseract (<0.1s vs 5s)
        code_im = code_images[code]
        region_resized = cv2.resize(region, (code_im.shape[1]-2*extra_pad, code_im.shape[0]-2*extra_pad))
        if extra_pad != 0:
            region_resized = cv2.copyMakeBorder(region_resized, extra_pad, extra_pad, extra_pad, extra_pad, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        (score, _) = structural_similarity(region_resized, code_im, full=True)
        if score > closest_score:
            closest_score = score
            closest_code = code
    return closest_code
    

def find_code_matrix(img_thresh, img=None):
    '''Finds the code matrix in the image, returns the roi and its bounds (x,y,w,h) within the source image'''
    roi_1_bounds = [(0, int(img_thresh.shape[1]/2)), (int(img_thresh.shape[0]*0.25), int(img_thresh.shape[0]*0.9))] # this is in width, height
    left_half = img_thresh[roi_1_bounds[1][0]:roi_1_bounds[1][1], roi_1_bounds[0][0]:roi_1_bounds[0][1]]
    # cv2.imshow('img_left', left_half)
    grid_box = None
    bounds = (0, 0, 0, 0)

    cnts = cv2.findContours(left_half.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ratio = w/h
        x += roi_1_bounds[0][0]
        y += roi_1_bounds[1][0]
        if ratio > 1.1 and ratio < 1.5 and w > 400 and h > 300: #must be roughly 1.4 aspect ratio and minimum of 300 pixels
            bounds = (x+10, y+int(h/8), w-20, h-10-int(h/8))
            grid_box = img_thresh[bounds[1]:bounds[1]+bounds[3], bounds[0]:bounds[0]+bounds[2]]
            if img is not None:
                cv2.rectangle(img, (bounds[0], bounds[1]), (bounds[0]+bounds[2], bounds[1]+bounds[3]), (255, 0, 0), 2)
            break

    return grid_box, bounds

def extract_grid(grid_box, grid_bounds, code_images, img=None):
    '''Extract the code snippets from the (thresholded) region of interest. Original image just used for tagging.'''
    pad = 5
    #find the code regions by making the codes a blob then finding those contours
    grid_box_copy = cv2.morphologyEx(grid_box, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13,13)));
    cnts = cv2.findContours(grid_box_copy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    grid_raw = []
    grid_boxes = []
    for c in cnts: #starts in bottom right, goes right to left
        (x, y, w, h) = cv2.boundingRect(c)
        ratio = w/h
        if ratio > 1.0 and ratio < 1.7 and h > 15:
            # grab the number region, pad it, compare it
            region = grid_box[y-pad:y+h+pad, x-pad:x+w+pad]
            region = cv2.bitwise_not(region)
            if region is None: continue

            #for any new codes
            # cv2.imwrite(f'numbers/{x}{y}.png', region)
            text = determine_code(region, code_images)

            grid_raw.append(text)
            # x += grid_bounds[0]
            # y += grid_bounds[1]
            grid_boxes.append((x, y, w, h)) #in original image coordinates, not roi coords
            if img is not None:
                x2 = x + grid_bounds[0]
                y2 = y + grid_bounds[1]
                cv2.rectangle(img, (x2-pad, y2-pad), (x2+w+pad, y2+h+pad), (255, 255, 0), 2) #display a box around it
    grid_raw.reverse()
    grid_boxes.reverse()
    
    grid_size = math.sqrt(len(grid_raw))
    if math.floor(grid_size) != math.ceil(grid_size):
        print('Warning! Invalid data, non-square grid detected.')
    grid_size = round(grid_size)
    print('Found {0} items in grid. Grid size {1}'.format(len(grid_raw), grid_size))
    grid_square = []
    grid_boxes_square = []
    for i in range(grid_size):
        row = []
        row_boxes = []
        for j in range(grid_size):
            row.append(grid_raw[i*grid_size + j])
            row_boxes.append(grid_boxes[i*grid_size + j])
        grid_square.append(row)
        grid_boxes_square.append(row_boxes)
    return grid_square, grid_boxes_square

def extract_targets(img_thresh, code_images, img=None):
    pad = 5
    targets = []
    
    roi_bounds = [(int(img_thresh.shape[1]*0.4), (int(img_thresh.shape[1]*0.65))), (int(img_thresh.shape[0]*0.3), int(img_thresh.shape[0]*0.75))] # this is in width, height
    roi = img_thresh[roi_bounds[1][0]:roi_bounds[1][1], roi_bounds[0][0]:roi_bounds[0][1]]
    # cv2.imshow('roi', roi)

    closing_size = 5
    if img_thresh.shape[1] > 1600: closing_size = 7 #1600x900
    if img_thresh.shape[1] > 1920: closing_size = 9 #1920x1080
    roi_closed = cv2.morphologyEx(roi, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (closing_size, closing_size)))
    cv2.imshow('roi', roi_closed)
    cnts = cv2.findContours(roi_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    current_row = []
    cur_y = -1
    for c in cnts: #this goes from bottom right to top left
        (x, y, w, h) = cv2.boundingRect(c)
        ratio = w/h
        if ratio > 1.1 and ratio < 1.7 and w < 100 and w > 10: #must be roughly 1.5 aspect ratio and max of 100 pixels wide
            if cur_y < 0 : cur_y = y
            if y < cur_y - 10:
                #new row
                current_row.reverse()
                targets.append(current_row)
                current_row = []
                cur_y = y
            region = roi[y:y+h, x:x+w]
            region = cv2.bitwise_not(region)
            text = determine_code(region, code_images, pad)
            current_row.append(text)
            x += roi_bounds[0][0]
            y += roi_bounds[1][0]
            if img is not None:
                cv2.rectangle(img, (x-pad, y-pad), (x+w+pad, y+h+pad), (255, 255, 0), 2) #display a box around it
    if current_row:
        current_row.reverse()
        targets.append(current_row)
    targets.reverse()
    print('Targets:')
    for row in targets:
        print(' '.join(row))
    return targets

def find_buffer_region(img_thresh, img=None):
    '''Finds the buffer region, returns the bounds (x,y,w,h) but not the image.'''
    roi_bounds = [(int(img_thresh.shape[1]*0.42), (int(img_thresh.shape[1]*0.8))), (int(img_thresh.shape[0]*0.15), int(img_thresh.shape[0]*0.25))] # this is in width, height
    roi = img_thresh[roi_bounds[1][0]:roi_bounds[1][1], roi_bounds[0][0]:roi_bounds[0][1]]

    buffer_bounds = (0,0,0,0)

    cnts = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts: #this goes from bottom right to top left
        (x, y, w, h) = cv2.boundingRect(c)
        ratio = w/h
        if ratio > 1 and h > 10:
            x += roi_bounds[0][0]
            y += roi_bounds[1][0]
            buffer_bounds = (x, y, w, h)
            if img is not None:        
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2) #display a box around it
            break
    return buffer_bounds

def extract_buffer(img_gray, buffer_bounds, img=None):
    '''Determines the buffer size. Takes the gray image, not the thresholded one (we re-threshold just the region)'''
    buffer_size = 0
    pad = 5
    verticals = 0
    roi = img_gray[buffer_bounds[1]+pad:buffer_bounds[1]+buffer_bounds[3]-pad, buffer_bounds[0]+pad:buffer_bounds[0]+buffer_bounds[2]-pad]
    roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1] # we threshold just the buffer region

    cnts = cv2.findContours(roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts: #this goes from bottom right to top left
        (x, y, w, h) = cv2.boundingRect(c)
        ratio = w/h
        if ratio < 0.3: #basically vertical line
            verticals += 1
            if img is not None:
                x += buffer_bounds[0]+pad
                y += buffer_bounds[1]+pad
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 255), 2) #display a box around it

    buffer_size = math.ceil(verticals / 2) #two verticals per buffer block
    return buffer_size

def overlay_result(img, sequence, box_positions, color, grid_bounds=(0,0,0,0), offset_x=0, offset_y=0):
    '''Draws lines on the original image showing the solved pattern'''
    for i in range(len(sequence) - 1):
        # draw line between this point and the next point
        first_seq = box_positions[sequence[i][0]][sequence[i][1]]
        first = (first_seq[0] + int(first_seq[2]/2) + offset_x + grid_bounds[0], first_seq[1] + int(first_seq[3]/2) + offset_y + grid_bounds[1])

        second_seq = box_positions[sequence[i+1][0]][sequence[i+1][1]]
        second = (second_seq[0] + int(second_seq[2]/2) + offset_x + grid_bounds[0], second_seq[1] + int(second_seq[3]/2) + offset_y + grid_bounds[1])
        cv2.arrowedLine(img, first, second, color, 2)


def run_extraction(img, show_debug_markers=False):
    '''Runs the extraction steps, returning the grid, targets list, buffer size, matrix region coords and matrix code positions (for overlay)'''
    code_images = build_source_codes()

    debug_image = None
    if show_debug_markers: 
        debug_image = img

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    grid_box, grid_bounds = find_code_matrix(img_thresh, debug_image)
    if grid_box is None:
        print('Could not find grid...')
        return None, None, None, None, None

    targets = extract_targets(img_thresh, code_images, debug_image)

    buffer_bounds = find_buffer_region(img_thresh, debug_image)
    buffer_size = extract_buffer(img_gray, buffer_bounds, debug_image)
    print('Buffer is size {0}'.format(buffer_size))
    
    grid, boxes = extract_grid(grid_box, grid_bounds, code_images, debug_image)
    if grid is not None:
        for row in grid:
            print(' '.join(row))

    return grid, targets, buffer_size, grid_bounds, boxes
    

def full_process(img, calculate_shortest=False, show_debug_markers=False):
    timer_overall = time.perf_counter()

    code_images = build_source_codes()

    debug_image = None
    if show_debug_markers: 
        debug_image = img

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # cv2.imshow('img_thresh', img_thresh)

    grid_box, grid_bounds = find_code_matrix(img_thresh, debug_image)
    if grid_box is None:
        print('Could not find grid...')
        return None, None

    targets = extract_targets(img_thresh, code_images, debug_image)

    buffer_bounds = find_buffer_region(img_thresh, debug_image)
    buffer_size = extract_buffer(img_gray, buffer_bounds, debug_image)
    print('Buffer is size {0}'.format(buffer_size))

    timer_cv_matrix = time.perf_counter()

    grid, boxes = extract_grid(grid_box, grid_bounds, code_images, debug_image)
    if grid is not None:
        for row in grid:
            print(' '.join(row))

    timer_extract_matrix = time.perf_counter()

    breach = Breacher()
    breach.set_grid(grid)
    breach.set_targets(targets, buffer_size)

    seq, score = breach.solve(shortest=calculate_shortest)
    seq_txt = breach.positions_to_text(seq)
    #overlay pattern on original image
    overlay_result(img, seq, boxes, (0, 255, 255), grid_bounds)
    print('Solution:', seq, seq_txt, score)
    print('Examined {0} possibilities with {1} valid solutions found.'.format(breach.total_tested, breach.total_solutions))

    timer_solve = time.perf_counter()

    elapsed_overall = round(time.perf_counter() - timer_overall, 2)
    elapsed_cv_matrix = round(timer_cv_matrix - timer_overall, 2)
    elapsed_extract_matrix = round(timer_extract_matrix - timer_cv_matrix, 2)
    elapsed_solve = round(timer_solve - timer_extract_matrix, 2)

    print('Timing {0}s overall. {1}s find matrix, {2}s matrix extract, {3}s solve.'.format(elapsed_overall, elapsed_cv_matrix, elapsed_extract_matrix, elapsed_solve))

    matrix_roi = img[grid_bounds[1]:grid_bounds[1]+grid_bounds[3], 
                        grid_bounds[0]:grid_bounds[0]+grid_bounds[2]]
    cv2.imshow('matrix_final', matrix_roi)

    return seq, seq_txt

def open_image(filename):
    return cv2.imread(filename)

def save_image(img, filename):
    cv2.imwrite(filename, img)

def base64_encode_image(img, extension):
    '''Base64 encodes the image to a byte-string'''
    _, buffer = cv2.imencode(extension, img)
    return base64.b64encode(buffer)

def base64_decode_image(base64Bytes):
    '''Takes a base64 encoded image as a byte-string and converts to an OpenCV image'''
    img = numpy.fromstring(base64.b64decode(base64Bytes), numpy.uint8)
    return cv2.imdecode(img, flags=cv2.IMREAD_COLOR)

def wait_for_keypress():
    cv2.waitKey()

if __name__ == "__main__":
    # filename = 'examples/example1_6g_8b_1.4.png'
    # filename = 'examples/example2_5g_8b_1.3.png'
    # filename = 'examples/example3_6g_8b_3.4.png'
    # filename = 'examples/example4_6g_8b_3.4.png'
    # filename = 'examples/example5_5g_4b_3.3_downloaded.jpg'
    # filename = 'examples/example6_1440.png'
    # filename = 'examples/example7.png'
    # filename = 'examples/example11.png'
    # filename = 'examples/example12_firstcomplete.png'
    # filename = 'examples/example13_jpg.jpg'
    filename = 'examples/example14_7g_900.png'
    
    img = cv2.imread(filename)
    sequence, text = full_process(img, calculate_shortest=False, show_debug_markers=True)

    # matrix_roi = img[grid_bounds[1]:grid_bounds[1]+grid_bounds[3], 
    #                     grid_bounds[0]:grid_bounds[0]+grid_bounds[2]]
    # cv2.imshow('matrix_final', matrix_roi)
    cv2.imshow('img', img)
    # cv2.imshow('img_gray', img_gray)
    # cv2.imshow('img_thresh', img_thresh)
    # cv2.imshow('img_left', left_half)
    # if grid_box is not None:
    # cv2.imshow('grid_box', grid_box)

    cv2.waitKey()
