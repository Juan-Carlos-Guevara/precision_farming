from pysheds.grid import Grid
from rasterio import plot
from keras.preprocessing.image import load_img, img_to_array, image
from keras.models import load_model
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import geopandas as gpd
import mplleaflet
import matplotlib.pyplot as plt
import os 
 
os.listdir('./static/images/stages_calculation')
imagePath = './static/images/stages_calculation'

def humidily_ndvi():

    band4 = rasterio.open(imagePath+'layer4.tiff')
    band5 = rasterio.open(imagePath+'layer5.tiff')
 
    nir = band5.read(1).astype('float64')
    red = band4.read(1).astype('float64')

    ndvi = np.where(
        (nir+red)==0.,
        0,
        (nir-red)/(nir+red)
    )

    ndviImage = rasterio.open('./stages_calculation/NDVI_Image.tiff','w',driver ='Gtiff',
                                width=band4.width, height=band4.height,
                                count=1,
                                crs=band4.crs,
                                transform=band4.transform,
                                dtype='float64' 
                            )
    ndviImage.write(ndvi,1)    
    ndviImage.close()                     

def humidily_ndwi():

    band5 = rasterio.open(imagePath+'layer5.tiff')
    band6 = rasterio.open(imagePath+'layer6.tiff')

    nir = band5.read(1).astype('float64')
    swir = band6.read(1).astype('float64')
   
    ndwi = np.where(
        (nir+swir)==0.,
        0,
        (nir-swir)/(nir+swir)
    )

    ndwiImage = rasterio.open('./stages_calculation/NDWI_Image.tiff','w',driver ='Gtiff',
                                width=band6.width, height=band6.height,
                                count=1,
                                crs=band6.crs,
                                transform=band6.transform,
                                dtype='float64' 
                            )
    ndwiImage.write(ndwi,1)    
    ndwiImage.close()                     

