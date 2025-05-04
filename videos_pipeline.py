import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import html, Input, Output
from dash import dcc
from dash import dash_table
from dash.dash_table import DataTable
import dash.exceptions as dash_exceptions
import random

import os
import re
import math
import ast
import numpy as np
import pandas as pd
import json

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import yt_dlp
from TikTokApi import TikTokApi
import requests
from bs4 import BeautifulSoup
import time
import dash_player
from dash import callback_context
from shapely.geometry import Point, Polygon
import datetime    
from datetime import timedelta
from datetime import date
from datetime import datetime, timedelta

# Google API imports
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path

import moviepy
from yt_dlp.postprocessor.common import PostProcessor
from yt_dlp.utils import sanitize_filename

import glob
from moviepy.editor import VideoFileClip
import shutil


SERVICE_ACCOUNT_FILE = r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Anlysis_Data\arabic-transcription-435113-c8120df00a35.json"
# Define scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 
          'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)


# Build Sheets API service
sheet = service.spreadsheets()


# Authenticate using Service Account
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Drive API service
drive_service = build('drive', 'v3', credentials=creds)
import unicodedata

def remove_emoji(text):
    return sanitize_filename(text, restricted=True)



def upload_video(file_path, folder_id, creds):
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]  # ID of the folder to upload into
    }

    media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = file.get('id')

    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    file_url = f"https://drive.google.com/file/d/{file_id}/view"

    print(f"File uploaded successfully, File ID: {file_id}")
    print(f"File URL: {file_url}")

    return file_url


    
    

def update_cell(spreadsheet_id, row_number, columns_values_dict, sheet_name="Cuts_DB"):
    if " " in sheet_name or any(c in sheet_name for c in "!@#$%^&*()[]{}<>?/\\|"):
        escaped_sheet_name = f"'{sheet_name}'"
    else:
        escaped_sheet_name = sheet_name

    for column_range, values in columns_values_dict.items():
        range_name = f"{escaped_sheet_name}!{column_range}{row_number}"
        
        # Ensure values is a list (even if one value)
        if not isinstance(values, list):
            values = [values]
        
        # If multiple columns (e.g., "K:L"), values should be list matching the number of columns
        body = {'values': [values]}  # 2D array: one row
        
        print(f"Updating {range_name} with values {values}")
        
        try:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            print(f"Successfully updated {range_name}")
        except Exception as e:
            print(f"Error updating {range_name}: {e}")


        
def city_load_data(sheetid,sheetrange):
    SHEET_ID = sheetid
    RANGE = sheetrange
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE).execute()
    values = result.get('values', [])
    if values:
        headers_n = values[0]
        data_n = values[1:]
        df_Cities = pd.DataFrame(data_n, columns=headers_n)
    else:
        print("No data found for DF.")
        df_Cities = pd.DataFrame()
    return df_Cities


global df_cities
sheetid_edit = '1aIEe5GLAY-MVfGPj8BVjaiZoJ1z1lWwfXUTBswT576U'
sheetrange_edit = 'All_Cities!A1:Y50000'
df_cities = city_load_data(sheetid_edit, sheetrange_edit)

global cut_db


global cities_db
sheetid  = '1Svc-2iK5wvHFicmBZHoOxqf5iajdg57ntilgR_cM3ZE'
sheetrange ='Cities!A1:J300'
cities_db = city_load_data(sheetid,sheetrange)

df_cities['TimeStamp'] = pd.to_datetime(df_cities['TimeStamp'])
days_ago = datetime.now() - timedelta(days=5)
filtered_df = df_cities[df_cities['TimeStamp'] >= days_ago]

og_vid_path = r"C:\video_for_ben\og_videos"
trimmed_vid_path = r"C:\video_for_ben\trimmed"

og_files_list = os.listdir(og_vid_path)



download_v = 0
trim_v = 0
upload_v = 0


for idx,row in filtered_df.iterrows():
    download_per_vid = 0
    trim_per_vid = 0
    upload_per_vid = 0

    cut_id = row['Cut_ID']
    rec_id = row['record_id']
    country = row['Country']
    city = row['City']
    url_link = row['Links']
    vid_title = row['Title']
    vid_dur = row['Duration']
    vid_og_dur = row['Original Duration']
    
    cut_sheet_id = '1R-qzDHwVB6f27sGYQvpQTZIoDQbzla59j5jM0rfIm3M'
    cut_range = 'Cuts_DB!A1:Q500000'
    cut_db = city_load_data(cut_sheet_id,cut_range)

    filtered_cuts = cut_db[cut_db['Cut_ID']==cut_id]
    for idx_cut, cut_row in filtered_cuts.iterrows():
        start_time = cut_row['Cut_Start']
        finish_time = cut_row['Cut_Fnish']
        annotation_name = cut_row['Annotated File Name']

        if filtered_cuts['Annotated File Name'].str.contains('TBD').any():        
            cleaned_title = remove_emoji(vid_title)
            exists = next((f for f in og_files_list if os.path.splitext(f)[0] == cleaned_title), None)
            if not exists:
                try:
                    ydl_opts = {
                        'quiet': False,
                        'outtmpl': 'C:/video_for_ben/og_videos/%(title)s.%(ext)s',
                        'ffmpeg_location': r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Analysis\ffmpeg-2025-04-14-git-3b2a9410ef-full_build\bin",
                        "restrictfilenames": True,
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url_link, download=True)
                        downloaded_filename = ydl.prepare_filename(info)
                    download_per_vid +=1
                except:
                    download_per_vid =0
                    
                    
                
                full_path = downloaded_filename

                if vid_dur < vid_og_dur:    


                            
                    ann_initals = cities_db[cities_db['City Name']==city]['City_Bucket_CodeName'].values[0]
                    init_df  = cut_db[cut_db['Annotated File Name'].str.contains(ann_initals)]        
                    
                    
                    init_df['number'] = init_df['Annotated File Name'].str.extract(r'_(\d+)_1').astype(int)
                    df_sorted = init_df.sort_values(by='number')
                    df_sorted = df_sorted.reset_index(drop=True)
                    full_ann_name = df_sorted['Annotated File Name'].iloc[-1]
                    ann_number =  df_sorted['Annotated File Name'].tail(1).str.extract(r'_(\d+)_1').astype(int).iloc[0, 0]
                    lastest_val = ann_number + 1
                    latest_annot = full_ann_name.replace(str(ann_number), str(lastest_val))  
                    try:        
                        clip = VideoFileClip(full_path).subclip(start_time, finish_time)
                        trimmed_vid_path = rf"C:\video_for_ben\trimmed\{latest_annot}.mp4"
                        clip.write_videofile(trimmed_vid_path, codec="libx264")      
                        trim_per_vid +=1
                        trim_v +=1
                    except:
                        trim_per_vid = 0
                        
                    cut_sheet_ids = '1R-qzDHwVB6f27sGYQvpQTZIoDQbzla59j5jM0rfIm3M'
                    
                    cut_sizes = os.path.getsize(trimmed_vid_path)
                    cut_size_mb = cut_sizes / (1024 * 1024) 
                    cut_size = f"{cut_size_mb:.2f} MB"


                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    drive_id = cities_db[cities_db['City Name']==city]['City_Bucket_URL'].values[0]
                    video_url = upload_video(trimmed_vid_path, drive_id, creds)
                    
                    columns_values_dict={
                    "G": latest_annot ,
                    "K:L": [cut_size, video_url],
                    "O": now
                }
                    

                    update_cell(cut_sheet_ids, idx_cut + 2, columns_values_dict)
                        

                else:
                    shutil.copy(full_path,trimmed_vid_path)
                    trim_per_vid +=1
                    trim_v +=1 
                
            else:
                ann_initals = cities_db[cities_db['City Name']==city]['City_Bucket_CodeName'].values[0]
                init_df  = cut_db[cut_db['Annotated File Name'].str.contains(ann_initals)]

                rec_df = filtered_df[df_cities['record_id']==rec_id].copy()
                rec_df['base'] = rec_df['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0]
                rec_df['version'] = rec_df['Cut_ID'].str.extract(r'_v(\d+)$')[0].astype(int)
                latest_versions = rec_df.sort_values('version').groupby('base', as_index=False).last()

                cuts_number = latest_versions['base'].nunique()   
                new_cut = cuts_number + 1

                init_df['number'] = init_df['Annotated File Name'].str.extract(r'_(\d+)_1').astype(int)
                df_sorted = init_df.sort_values(by='number')
                df_sorted = df_sorted.reset_index(drop=True)
                full_ann_name = df_sorted['Annotated File Name'].iloc[-1]
                ann_number = df_sorted['Annotated File Name'].tail(1).str.extract(r'_(\d+)_1').astype(int).iloc[0, 0]
                lastest_val = ann_number + 1
                latest_annot = full_ann_name.replace(str(ann_number), str(lastest_val))
                
                parts = latest_annot.rsplit('_', 1)         
                latest_cut = f"{parts[0]}_{new_cut}"
                
                
                full_path = os.path.join(og_vid_path, exists)
                try:
                    clip = VideoFileClip(full_path).subclip(start_time, finish_time)
                    trimmed_vid_path = rf"C:\video_for_ben\trimmed\{latest_cut}.mp4"
                    clip.write_videofile(trimmed_vid_path, codec="libx264")      
                    trim_per_vid +=1
                    trim_v +=1
                except:
                    trim_per_vid = 0
                
                cut_sheet_ids = '1R-qzDHwVB6f27sGYQvpQTZIoDQbzla59j5jM0rfIm3M'
                
                cut_sizes = os.path.getsize(trimmed_vid_path)
                cut_size_mb = cut_sizes / (1024 * 1024) 
                cut_size = f"{cut_size_mb:.2f} MB"


                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                drive_id = cities_db[cities_db['City Name']==city]['City_Bucket_URL'].values[0]
                video_url = upload_video(trimmed_vid_path, drive_id, creds)
                
                columns_values_dict={
                "G": latest_cut ,
                "K:L": [cut_size, video_url],
                "O": now
            }
                
                update_cell(cut_sheet_ids, idx_cut + 2, columns_values_dict)
  
        else:
            continue          
            
 
        

    
