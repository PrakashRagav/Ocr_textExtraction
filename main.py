import textExtract
import pdf2image
import numpy as np
import csv
from PIL import Image
import re,os,glob
import logging
import pathlib
import cv2
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
    textExtract.sort_alphaN(jpgFilenamesList)
    
    csv_str_list =[]
    for img_i in (jpgFilenamesList[2:-1]): 
        img = Image.open(img_i)
        page = np.asarray(img)

        pimg = cv2.threshold(page, 128, 255, cv2.THRESH_BINARY)[1]
        thr = cv2.threshold(page, 128, 255, cv2.THRESH_BINARY_INV)[1]
        rects = textExtract.getTBRects(page,thr)
        
        for r_item in rects:
            i_items = textExtract.getInnerRects(r_item,pimg)
            i_item,x,y = i_items
            for i in i_item:
                strings = textExtract.getResults(i,x,y,page)
                print(strings)
                csv_str_list.append(strings)      
        img.close ()
        
    csv_path = os.path.join(pr_csv_path, place)
    os.makedirs(csv_path,exist_ok=True)

    with open(f'{csv_path}\\{f_name}.csv', 'w',encoding='utf_8_sig',newline='') as f:
        write = csv.writer(f)
        write.writerows(csv_str_list)
