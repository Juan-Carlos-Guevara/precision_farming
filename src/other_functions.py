import numpy as np
import json
import keras.backend.tensorflow_backend as tb
import uuid 
import cv2
import os

from werkzeug.utils import secure_filename
from keras.preprocessing.image import load_img, img_to_array, image
from keras.models import load_model

tb._SYMBOLIC_SCOPE.value = True


kernel = np.ones((6,6),np.uint8) 

yellow_color = (0, 255,255)
violet_color = (140, 40, 120)
red_color = (0, 0, 255)
green_color = (3, 73, 7)
brown_color = (33,120,203)


def predict_image(image_name,model_weight):

    length, height = 150, 150 #Altura, Longitud

    model= './crops_model/'+model_weight["model"]
    weight= './crops_model/'+model_weight["weight"]
    
    cnn = load_model(model)
    cnn.load_weights(weight)

    file = './static/images/stages_calculation/'+image_name+'.png'
        
    x= load_img(file, target_size=(length,height))
    x= img_to_array(x)
    x= np.expand_dims(x, axis=0)
    array= cnn.predict(x) ##[[1,0,0]]
    result= array[0] ##[[0,0,1]]
    answer= np.argmax(result) #2

    return answer
    
#{'Etapa 1': 0, 'Etapa 2': 1, 'Etapa 3': 2, 'Etapa 4': 3, 'Producto_final': 4, 'Terreno': 5}
#print(predict_image())

def generate_uuid(var):

    code = uuid.uuid4()
    
    if var == 1:
        codes = code.time_mid 
    
        return codes

    else:
        return code


def draw_contour(contour, color, image):
     
    for (i,c) in enumerate(contour):
        M = cv2.moments(c)
            
        if M["m00"] != 0:
            x = int(M["m10"]/M["m00"])
            y = int(M["m01"]/M["m00"])
        else:
            x, y = 0, 0
            
        cv2.drawContours(image, [c], 0, color, 2)  

def humidity_calculation(image_name):

    file = './static/images/humidity_calculation/'+image_name+'.png'

    image = cv2.imread(file)
    imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 

    low_yellow = np.array([12, 100, 30], np.uint8)
    high_yellow = np.array([32, 255, 255], np.uint8)

    low_violet = np.array([130, 100, 20], np.uint8)
    high_violet = np.array([160, 255, 255], np.uint8)

    low_red = np.array([0, 100, 20], np.uint8)
    high_red = np.array([10, 255, 255], np.uint8)
    low_red1 = np.array([175, 100, 20], np.uint8)
    high_red1 = np.array([180, 255, 255], np.uint8)

    mask_red1 = cv2.inRange(imageHSV, low_red, high_red)
    mask_red2= cv2.inRange(imageHSV, low_red1, high_red1)
    mask_red =  cv2.add(mask_red1, mask_red2)
    mask_yellow = cv2.inRange(imageHSV, low_yellow, high_yellow)
    mask_violet= cv2.inRange(imageHSV, low_violet, high_violet)

    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)
    mask_violet = cv2.morphologyEx(mask_violet, cv2.MORPH_OPEN, kernel)
    mask_red = cv2.morphologyEx(mask_red, cv2.MORPH_OPEN, kernel)

    Yellow_outlines = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    violet_outlines = cv2.findContours(mask_violet, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    red_outlines = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    draw_contour(Yellow_outlines,yellow_color,image)
    draw_contour(violet_outlines,violet_color,image)
    draw_contour(red_outlines,red_color,image)

    yellow_pixels = (np.transpose(np.nonzero(mask_yellow)).sum())
    violet_pixels = (np.transpose(np.nonzero(mask_violet)).sum())
    red_pixels = (np.transpose(np.nonzero(mask_red)).sum())

    total_pixels = yellow_pixels + violet_pixels + red_pixels

    yellow_pixelss = round(100*(yellow_pixels/total_pixels),2)
    violet_pixelss = round(100*(violet_pixels/total_pixels),2)
    red_pixelss = round(100*(red_pixels/total_pixels),2)

    cv2.imwrite('./static/images/humidity_calculation/'+image_name+'.png',image)

    return yellow_pixelss, red_pixelss, violet_pixelss


def plant_health(image_name):

    file = './static/images/plant_health/'+image_name+'.png'

    image = cv2.imread(file)
    imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    low_yellow = np.array([25, 50, 30], np.uint8) 
    high_yellow = np.array([34, 255, 255], np.uint8)

    low_green = np.array([35, 10, 20], np.uint8)
    high_green = np.array([75, 255, 255], np.uint8)

    low_brown = np.array([11, 0, 0], np.uint8)
    high_brown = np.array([24, 255, 255], np.uint8)

    mask_yellow = cv2.inRange(imageHSV, low_yellow, high_yellow)
    mask_green= cv2.inRange(imageHSV, low_green, high_green)
    mask_brown= cv2.inRange(imageHSV, low_brown, high_brown)
    
    mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)
    mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
    mask_brown = cv2.morphologyEx(mask_brown, cv2.MORPH_OPEN, kernel)
   
    Yellow_outlines = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    green_outlines = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
    brown_outlines = cv2.findContours(mask_brown, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    draw_contour(Yellow_outlines,yellow_color,image)
    draw_contour(green_outlines,green_color,image)
    draw_contour(brown_outlines,brown_color,image)

    yellow_pixels = (np.transpose(np.nonzero(mask_yellow)).sum())
    green_pixels = (np.transpose(np.nonzero(mask_green)).sum())
    brown_pixels = (np.transpose(np.nonzero(mask_brown)).sum())
  
    total_pixels = yellow_pixels + green_pixels + brown_pixels

    yellow_pixelss = round(100*(yellow_pixels/total_pixels),2)
    green_pixelss = round(100*(green_pixels/total_pixels),2)
    brown_pixelss = round(100*(brown_pixels/total_pixels),2)

    img_name_cal = str(generate_uuid(2))
    cv2.imwrite('./static/images/plant_health/'+img_name_cal+'.png',image)

    if brown_pixelss >= 20:
        answer = 3

    elif yellow_pixelss > 20:
        answer = 2
    
    else :
        answer = 1

    return green_pixelss, yellow_pixelss, brown_pixelss, answer, img_name_cal

# import glob

# def plant_health2():
    
#     lista=[]
#     lista1=[]
#     lista2=[]
#     i=0

#     files = glob.glob('./static/images/Amarillo/*.JPG')

#     for f in files:

#         image = cv2.imread(f)
#         imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

#         low_yellow = np.array([25, 50, 30], np.uint8) 
#         high_yellow = np.array([34, 255, 255], np.uint8)

#         low_green = np.array([35, 10, 20], np.uint8)
#         high_green = np.array([75, 255, 255], np.uint8)

#         low_brown = np.array([11, 0, 0], np.uint8)
#         high_brown = np.array([22, 255, 255], np.uint8)

#         mask_yellow = cv2.inRange(imageHSV, low_yellow, high_yellow)
#         mask_green= cv2.inRange(imageHSV, low_green, high_green)
#         mask_brown= cv2.inRange(imageHSV, low_brown, high_brown)
        
#         mask_yellow = cv2.morphologyEx(mask_yellow, cv2.MORPH_CLOSE, kernel)
#         mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
#         mask_brown = cv2.morphologyEx(mask_brown, cv2.MORPH_OPEN, kernel)
    
#         Yellow_outlines = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
#         green_outlines = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
#         brown_outlines = cv2.findContours(mask_brown, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

#         draw_contour(Yellow_outlines,yellow_color,image)
#         draw_contour(green_outlines,green_color,image)
#         draw_contour(brown_outlines,brown_color,image)

#         yellow_pixels = (np.transpose(np.nonzero(mask_yellow)).sum())
#         green_pixels = (np.transpose(np.nonzero(mask_green)).sum())
#         brown_pixels = (np.transpose(np.nonzero(mask_brown)).sum())
    
#         total_pixels = yellow_pixels + green_pixels + brown_pixels

#         yellow_pixelss = round(100*(yellow_pixels/total_pixels),2)
#         green_pixelss = round(100*(green_pixels/total_pixels),2)
#         brown_pixelss = round(100*(brown_pixels/total_pixels),2)

#         i=i+1

#         y = yellow_pixelss,' : ', f
#         g = green_pixelss,' : ', f
#         b = brown_pixelss,' : ', f

#         lista.insert(i, y)
#         lista1.insert(i, g)
#         lista2.insert(i, b)
        
 
#     print(lista)
#     #print(lista1)
#     #print(lista2)


# plant_health()
