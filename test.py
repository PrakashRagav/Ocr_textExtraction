import cv2 
import pytesseract
import pdf2image
import numpy as np
import csv
from PIL import Image
import re,os,glob
import logging
import pathlib


def sort_alphaN( l ):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    l.sort( key=alphanum_key )

def getTBRects(page):
    cnts,_ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnts_tables = [cnt for cnt in cnts if cv2.contourArea(cnt) > 50000]
    tb_rects = sorted([cv2.boundingRect(cnt) for cnt in cnts_tables],
               key=lambda r: r[1])
    return tb_rects

def getInnerRects(tb_rects):
    x,y,w,h = tb_rects
    icnts,_ = cv2.findContours(pimg[y:y+h,x:x+w],
                            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    inner_rects = sorted([cv2.boundingRect(cnt) for cnt in icnts if cv2.contourArea(cnt) > 50000],
                         key=lambda r: (r[1], r[0]))
    return inner_rects,x,y

def getResults(inner_rects,x,y):
    xx,yy,ww,hh = inner_rects
    xx += x
    yy += y
    cell = page[yy:yy+hh, xx:xx+ww]
    result = cell.copy()
    thresh = cv2.threshold(cell.copy(), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    print('\n')
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35,1))
    detect_horizontal = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    cnts = cv2.findContours(detect_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255,255,255), 5)
    
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,15))
    detect_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    cnts = cv2.findContours(detect_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for c in cnts:
        cv2.drawContours(result, [c], -1, (255,255,255),5)
        

    _,threshold = cv2.threshold(result.copy(),150,255,cv2.THRESH_BINARY_INV)
    contours, _= cv2.findContours(threshold,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    mas = np.zeros(result.shape, dtype=np.uint8)
    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if h<80: #80
            cv2.drawContours(mas, [cnt], 0, (255,255,255), 1)

    kernel = np.ones((6,60),np.uint8)
    dilation = cv2.dilate(mas,kernel,iterations = 1)
    _, threshold_d = cv2.threshold(dilation,150,255,cv2.THRESH_BINARY)
    contours_d, hierarchy = cv2.findContours(threshold_d,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)

    sorted_ctrs = sorted([cnt for cnt in contours_d if cv2.contourArea(cnt)>1000], key=lambda ctr: cv2.boundingRect(ctr)[1])
    
    cImage =result.copy()
    ROI = []
    for cnt in sorted_ctrs:
        x,y,w,h = cv2.boundingRect(cnt)
        if w>15 and h>15:
            roi_c = cImage[y:y+h, x:x+w] 
            ROI.append(roi_c)
    list_str = []
    for  enum, i  in enumerate(ROI,start=1):
        if enum in(1,2):
            tx = pytesseract.image_to_string(i, config='--psm 6',lang='eng')
            tx= tx.replace('\n\x0c','').replace('\x0c','').replace('\u200c','').replace('|','').replace('\n','')
            list_str.append(tx)
        else:
            tx = pytesseract.image_to_string(i, config='--psm 6',lang='tam+eng')
            tx= tx.replace('\n\x0c','').replace('\x0c','').replace('\u200c','').replace('|','').replace('\n','')
            list_str.append(tx)
    return list_str
        

        

if __name__ == '__main__':
    temp = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath
    
    path = pathlib.Path.cwd()
    pdf_path = pathlib.PosixPath(path,'pdfs')
    pr_image_path = pathlib.PosixPath(path,'images')
    pr_csv_path = pathlib.PosixPath(path,'csv')

    pdf_list = list(pdf_path.glob('**/*.pdf'))
    csv_list = list(pr_csv_path.glob('**/*.csv'))

    l_csv = int(len(csv_list))
    for pdf in pdf_list[l_csv::]:
        head,tail = os.path.split(pdf)
        place = head.split("\\")[-1]
        f_name = tail.replace('.pdf','')

        

        image_place_path = os.path.join(pr_image_path,place+f'\\{f_name}\\')
        os.makedirs(image_place_path,exist_ok=True)
        images = pdf2image.convert_from_path(pdf, grayscale=True, dpi =300)
        for i in range(len(images)):
            images[i].save(image_place_path+'page'+ str(i)+'.png')

        jpgFilenamesList = glob.glob(str(image_place_path)+'/*.png')
        sort_alphaN(jpgFilenamesList)
        csv_str_list =[]
        for img_i in (jpgFilenamesList[2:-1]): 
            img = Image.open(img_i)
            page = np.asarray(img)

            pimg = cv2.threshold(page, 128, 255, cv2.THRESH_BINARY)[1]
            thr = cv2.threshold(page, 128, 255, cv2.THRESH_BINARY_INV)[1]
            rects = getTBRects(page)
            
            
            for r_item in rects:
                i_items = getInnerRects(r_item)
                i_item,x,y = i_items
                for i in i_item:
                    strings = getResults(i,x,y)
                    print(strings)
                    csv_str_list.append(strings)      
            img.close ()
        csv_path = os.path.join(pr_csv_path, place)
        os.makedirs(csv_path,exist_ok=True)

        with open(f'{csv_path}\\{f_name}.csv', 'w',encoding='utf_8_sig',newline='') as f:
            write = csv.writer(f)
            write.writerows(csv_str_list)
    
            
