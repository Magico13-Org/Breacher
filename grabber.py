# This file handles image processing, including determining the grid and target sequences
#builtin
import math
import time

#pip
import cv2
import imutils
from skimage.metrics import structural_similarity

#ours
from breacher import Breacher

code_images = {}

def build_source_contours():
    '''Reads in the code images to build their contours for comparing to later'''
    global code_images
    images = {} # clear it out just in case
    codes = ['1C', '7A', '55', 'BD', 'E9']

    for code in codes:
        im = cv2.imread('codes/{0}.png'.format(code), cv2.IMREAD_UNCHANGED)
        images[code] = im
    
    code_images = images


def massage_data(raw_data):
    '''Takes the raw snippets and remaps to the expected values, in-place'''
    for i in range(len(raw_data)):
        raw = raw_data[i]
        #only expected values are 1C, 7A, E9, BD, 55
        l = len(raw)
        if l == 0:
            print('No text data for item {0}, cannot massage.'.format(i))
        elif l == 1:
            #try to massage
            if raw == '1' or raw == 'C': raw_data[i] = '1C'
            elif raw == '7' or raw =='A': raw_data[i] = '7A'
            elif raw == 'E' or raw =='9': raw_data[i] = 'E9'
            elif raw == 'B' or raw =='D': raw_data[i] = 'BD'
            elif raw == '5': raw_data[i] = '55'
        elif l == 2:
            #verify?
            continue
        else:
            print('Invalid text data "{0}" at index {1}'.format(raw, i))

def find_code_matrix(img_thresh):
    '''Finds the code matrix in the image, returns the roi and its bounds (x,y,w,h) within the source image'''
    roi_1_bounds = [(0, int(img_thresh.shape[1]/2)), (0, int(img_thresh.shape[0]*0.75))] # this is in width, height
    left_half = img_thresh[roi_1_bounds[1][0]:roi_1_bounds[1][1], roi_1_bounds[0][0]:roi_1_bounds[0][1]]

    grid_box = None
    bounds = (0, 0, 0, 0)

    cnts = cv2.findContours(left_half.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        ratio = w/h
        x += roi_1_bounds[0][0]
        y += roi_1_bounds[1][0]
        if ratio > 1.3 and ratio < 1.5 and w > 400 and h > 300: #must be roughly 1.4 aspect ratio and minimum of 300 pixels
            if img is not None:
                cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            bounds = (x+10, y+50, w, h)
            grid_box = img_thresh[bounds[1]:y+h-10, bounds[0]:x+w-10]
            break

    return grid_box, bounds
    

def extract_grid(grid_box, grid_bounds, img=None):
    '''Extract the grid from the (thresholded) image. Original image just used for tagging. img_thresh used for data'''
    
    #find the number regions by making the numbers a blob then finding those contours
    grid_box_copy = cv2.morphologyEx(grid_box, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13,13)));
    cnts = cv2.findContours(grid_box_copy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    grid_raw = []
    # regions_raw = []
    grid_boxes = []
    # i = 0
    for c in cnts: #starts in bottom right, goes right to left
        (x, y, w, h) = cv2.boundingRect(c)
        # grab the number region, pad it, ocr it
        pad = 5
        region = grid_box[y-pad:y+h+pad, x-pad:x+w+pad]
        region = cv2.bitwise_not(region)

        closest_code = None
        closest_score = -1
        for code in code_images: #infinitely faster than doing OCR with tesseract (<0.1s vs 5s)
            code_im = code_images[code]
            region_resized = cv2.resize(region, (code_im.shape[1], code_im.shape[0]))
            (score, _) = structural_similarity(region_resized, code_im, full=True)
            if score > closest_score:
                closest_score = score
                closest_code = code

        text = closest_code
        grid_raw.append(text)
        x += grid_bounds[0]
        y += grid_bounds[1]
        grid_boxes.append((x, y, w, h)) #in original image coordinates, not roi coords
        if img is not None:
            cv2.rectangle(img, (x-pad, y-pad), (x+w+pad, y+h+pad), (255, 255, 0), 2) #display a box around it
    grid_raw.reverse()
    grid_boxes.reverse()
    # regions_raw.reverse()
    # for i in range(len(regions_raw)):
    #     cv2.imshow('region_{0}'.format(i), regions_raw[i])
    # massage_data(grid_raw) # not needed with image comparison vs OCR
    
    grid_size = math.sqrt(len(grid_raw))
    if math.floor(grid_size) != math.ceil(grid_size):
        print('Warning! Invalid data, non-square grid detected.')
    grid_size = round(grid_size)
    print('Found {0} items in grid. Grid size {1}'.format(len(grid_raw), grid_size))
    # print(grid_raw)
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

    # cv2.imshow('grid_box', grid_box)
    return grid_square, grid_boxes_square

def overlay_result(img, sequence, box_positions):
    '''Draws lines on the original image showing the solved pattern'''
    for i in range(len(sequence) - 1):
        # draw line between this point and the next point
        first_seq = box_positions[sequence[i][0]][sequence[i][1]]
        first = (first_seq[0] + int(first_seq[2]/2), first_seq[1] + int(first_seq[3]/2))

        second_seq = box_positions[sequence[i+1][0]][sequence[i+1][1]]
        second = (second_seq[0] + int(second_seq[2]/2), second_seq[1] + int(second_seq[3]/2))
        cv2.arrowedLine(img, first, second, (255, 255, 255), 2)


if __name__ == "__main__":
    # filename = 'example2_5g_8b_1.3.png'
    # filename = 'example4_6g_8b_3.4.png'
    filename = 'example1_6g_8b_1.4.png'

    timer_overall = time.perf_counter()

    build_source_contours()

    img = cv2.imread(filename)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    grid_box, grid_bounds = find_code_matrix(img_thresh)
    if grid_box is None:
        print('Could not find grid...')
        exit()

    timer_cv_matrix = time.perf_counter()

    grid, boxes = extract_grid(grid_box, grid_bounds, img)
    if grid is not None:
        for row in grid:
            print(' '.join(row))

    timer_extract_matrix = time.perf_counter()

    breach = Breacher()
    breach.set_grid(grid)
    breach.set_targets([
        # ['BD', 'BD'],
        # ['1C', '1C', 'BD'],
        # ['BD', 'BD', '1C', '55']
        ['1C', '55', '55', 'BD']
    ], 8)

    seq, score = breach.solve()
    seq_txt = breach.positions_to_text(seq)
    print('"Best" option:', seq, seq_txt, score)

    timer_solve = time.perf_counter()

    #overlay pattern on original image
    overlay_result(img, seq, boxes)

    elapsed_overall = round(time.perf_counter() - timer_overall, 2)
    elapsed_cv_matrix = round(timer_cv_matrix - timer_overall, 2)
    elapsed_extract_matrix = round(timer_extract_matrix - timer_cv_matrix, 2)
    elapsed_solve = round(timer_solve - timer_extract_matrix, 2)

    print('Timing {0}s overall. {1}s find matrix, {2}s matrix extract, {3}s solve.'.format(elapsed_overall, elapsed_cv_matrix, elapsed_extract_matrix, elapsed_solve))

    cv2.imshow('img', img)
    # cv2.imshow('img_gray', img_gray)
    # cv2.imshow('img_thresh', img_thresh)
    # cv2.imshow('img_left', left_half)
    # if grid_box is not None:
    cv2.imshow('grid_box', grid_box)

    cv2.waitKey()
