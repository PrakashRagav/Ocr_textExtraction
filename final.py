import pathlib
import cv2 
import pytesseract
import pdf2image
import numpy as np
import csv
from PIL import Image
import re,os,glob

def sort_alphaN( l ):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    l.sort( key=alphanum_key )

def getTBRects(page):
    cnts,_ = cv2.findContours(thr, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnts_tables = [cnt for cnt in cnts if cv2.contourArea(cnt) > 10000]
    tb_rects = sorted([cv2.boundingRect(cnt) for cnt in cnts_tables],
               key=lambda r: r[1])
    return tb_rects

def getInnerRects(tb_rects):
    x,y,w,h = tb_rects
    icnts,_ = cv2.findContours(pimg[y:y+h,x:x+w],
                            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    inner_rects = sorted([cv2.boundingRect(cnt) for cnt in icnts if cv2.contourArea(cnt) > 10000],
                         key=lambda r: (r[1], r[0]))
    return inner_rects,x,y

def getBoxes(inner_rects,x,y):
    xx,yy,ww,hh = inner_rects
    xx += x
    yy += y
    cell = page[yy+1:yy+hh-1, xx+1:xx+ww-1]
    c_thr = cv2.threshold(cell, 127, 255, cv2.THRESH_BINARY_INV)[1]
    #filling 
    ys, xs = np.min(np.argwhere(cell == 0 ), axis=0)            
    temp = cv2.floodFill(cell.copy(), None, (xs, ys), 255)[1]
    mask = cv2.floodFill(thr[yy:yy+hh, xx:xx+ww].copy(),
                         None, (xs, ys), 0)[1]
    #cell contours
    c_thr = cv2.threshold(mask, 127, 255,cv2.THRESH_BINARY_INV)[1]
    kernel = np.ones((1,1), np.uint8)
    #cell = cv2.GaussianBlur(cell, (3, 3), 0)
    
    #cell = cv2.erode(cell, kernel, iterations=1) 
    cell = cv2.dilate(cell, kernel, iterations=1)
    xc,yc = c_thr.shape
    w_t= int(72*yc/100)
    boxes = (cell[0:xc,0:w_t],cell[0:xc,w_t:yc])
    return boxes

def getRightDetails(box2):
    ker = np.ones((3,3), np.uint8)
    box2 = cv2.dilate(box2, ker, iterations=1)
    xxc,yyc = box2.shape
    hh_t= int(np.floor(xxc/6))-4 
    #cv2_imshow(box2[0:hh_t,0:xxc])
    id_text = pytesseract.image_to_string(
                        box2[0:hh_t,0:xxc],
                        config='--psm 7',
                        lang='eng')
    return id_text

def getLeftDetails(box1):
    xcc,ycc = box1.shape
    x_t = 0
    h_t= int(np.floor(xcc/6)) -4 #6 blocks
    add= int(np.floor(xcc/6))
    y_t = 0
    w_t= ycc
    #cell = cv2.GaussianBlur(cell, (3, 3), 0)

    Crects = [(x_t,h_t,y_t,w_t)]
      
    for i in range(5):
            x_t = h_t
            h_t += add
            Crects.append((x_t, h_t,y_t,w_t))
      
    Crects.reverse() #for condition
    isEmpty = None
    left_list = []
    for ii_ff,(x_d,h_d,y_d,w_d) in enumerate(Crects, start=1):
        if ii_ff == 1:
            ww_d = int((33*w_d)/100)

            #cv2_imshow(box1[x_d:h_d,y_d:ww_d])
            text1 = pytesseract.image_to_string(
                        box1[x_d:h_d,y_d:ww_d],
                        config=' --psm 6'
                        , lang='eng')
            #print(text1)
            
            left_list.append(text1)
            y_d = ww_d
            #gender
            #cv2_imshow(box1[x_d:h_d,y_d:w_d])
            text2 = pytesseract.image_to_string(
                        box1[x_d:h_d,y_d:w_d],
                        config=' --psm 6'
                        , lang='tam+eng')
            
            #print(text2)
            
            left_list.append(text2)
            isEmpty= bool(len(text2)>2)
           
                

        if not(isEmpty):
            if (ii_ff == 2):
                ww_d = int((33*w_d)/100)

                #cv2_imshow(box1[x_d:h_d,y_d:ww_d])
                text1 = pytesseract.image_to_string(
                               box1[x_d:h_d,y_d:ww_d],
                               config=' --psm 6',
                               lang='eng')
                #print(text1)
                
                left_list.append(text1)
                y_d = ww_d
                        
                #gender
                #cv2_imshow(box1[x_d:h_d,y_d:w_d])
                text2 = pytesseract.image_to_string(
                                    box1[x_d:h_d,y_d:w_d],
                                    config=' --psm 6'
                                    ,lang='tam+eng')
                #print(text)
                
                left_list.append(text2)
                        
            else:
                if (ii_ff == 3):        
                    #cv2_imshow(box1[x_d:h_d-4,y_d:w_d])
                    text = pytesseract.image_to_string(
                                box1[x_d:h_d,y_d:w_d],
                                config=' --psm 6'
                                ,lang='eng')
                    
                    #print(text)
                    left_list.append(text)
                            
                else:
                    if not(ii_ff ==6):
                        #cv2_imshow(box1[x_d:h_d,y_d:w_d])
                        text = pytesseract.image_to_string(
                                box1[x_d:h_d,y_d:w_d],
                                config=' --psm 6'
                                ,lang='tam+eng')
                    
                        left_list.append(text)
                        #print (text)
        else:
            if not(ii_ff == 1):
                if not (ii_ff == 6):
                    #cv2_imshow(box1[x_d:h_d,y_d:w_d])
                    text = pytesseract.image_to_string(
                                box1[x_d:h_d,y_d:w_d],
                                config=' --psm 6'
                                ,lang='tam+eng')
                
                    left_list.append(text)
                    #print (text)
            
    return left_list

def cleanText(text):
    strings = [t.replace('\n', '').replace('\f', '').replace('\u200c', '') for t in text]
    strings= [x for x in strings if x]
    Cstrings = []
    for itemb in strings:
        itemb = itemb.replace('தந்ைத','தந்தை')
        if itemb[-1] == '-':
            tex = itemb.replace('-', '')
            Cstrings.append(tex)
        else:
            tex = itemb
            Cstrings.append(tex)
    
    for enum, i_text in enumerate(Cstrings):
        if enum == 0:
            try:
                num = re.findall("\d+",i_text)[0]
                Cstrings[0] = num
            except:
                pass
                #Cstrings[0] = 'missing'
        elif enum == 1:
            house = i_text.split(': ')
            Cstrings[1] = house[-1]

        if enum == 2:
            house = i_text.split(': ')
            Cstrings[2] = house[-1]
    
        
    return Cstrings


if __name__ == '__main__':
    temp = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath
    path = pathlib.Path.cwd()
    pdf_path = pathlib.PosixPath(path,'pdfs')
    image_path = pathlib.PosixPath(path,'images')
    csv_path = pathlib.PosixPath(path,'csv')

    pdf_list = list(pdf_path.glob('**/*.pdf'))
    csv_list = list(csv_path.glob('**/*.csv'))
    l_csv = 0 if len(list) is None else len(list)/2
    
    for pdf in pdf_list[int(int(l_csv))::]:
        head,tail = os.path.split(pdf)
        place = head.split("\\")[-1]
        f_name = tail.replace('.pdf','')

        image_place_path = os.path.join(image_path,place+f'\\{f_name}\\')
        clean_csv_path = os.path.join(csv_path, place+'\\clean\\')
        unclean_csv_path = os.path.join(csv_path, place+'\\unclean\\')

        os.makedirs(image_place_path,exist_ok=True)
        

        print(f_name)
        images = pdf2image.convert_from_path(pdf, grayscale=True, dpi =300)
        for i in range(len(images)):
            images[i].save(image_place_path+'page'+ str(i)+'.jpg', 'JPEG')

        jpgFilenamesList = glob.glob(str(image_place_path)+'/*.jpg')
        sort_alphaN(jpgFilenamesList)
        csv_list1 = []
        csv_list2 = []
        s_no = 1
        for img_i in (jpgFilenamesList[2:3]):
            img = Image.open(img_i)
            page = np.asarray(img)

            pimg = cv2.threshold(page, 128, 255, cv2.THRESH_BINARY)[1]
            thr = cv2.threshold(page, 128, 255, cv2.THRESH_BINARY_INV)[1]
            rects = getTBRects(page)
            
            
            for r_item in rects:
                i_items = getInnerRects(r_item)
                i_item,x,y = i_items
                for i in i_item:
                    try:
                        boxes = getBoxes(i,x,y)
                        box1,box2 = boxes 
                        right = getRightDetails(box2)
                        left = getLeftDetails(box1)
                        left.append(right)
                        strings = cleanText(left)
                        strings.append(s_no)
                        print(strings)
                        s_no += 1
                        if len(strings)==7:
                            csv_list1.append(strings)
                        else:
                            csv_list2.append(strings)               
                        
                    except ValueError: 
                        continue
            img.close ()
                            
        os.makedirs(clean_csv_path,exist_ok=True)
        os.makedirs(unclean_csv_path,exist_ok=True)
                            
        with open(f'{clean_csv_path}/{f_name}_c.csv', 'w',encoding='utf_8_sig',newline='') as f:
            write = csv.writer(f)
            
            write.writerows(csv_list1)
        with open(f'{unclean_csv_path}/{f_name}_u.csv', 'w',encoding='utf_8_sig',newline='') as f:
            write = csv.writer(f)
            write.writerows(csv_list2)

        print(len(csv_list1))
        print(len(csv_list2))
