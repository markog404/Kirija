from pywebio.platform.flask import webio_view
from pywebio import STATIC_PATH, start_server, config
from flask import Flask, send_from_directory
from pywebio.input import * 
from pywebio.output import *
from pywebio.session import  *
import argparse
import requests
import pandas as pd
import time 
import plotly.graph_objs as go
import re
import plotly.io as pio
from sklearn.neighbors import NearestNeighbors
import googlemaps
import numpy as np




app = Flask(__name__)
    
    #Index
def oglasi():
    clear()
    set_env(title='Kirija.net - analiza kirija u Beogradu', output_animation=False)
    put_markdown("# 🏢 Podaci za Beograd: ")
    df = pd.read_csv('bgoutput.csv')
    with open('time.txt', 'r') as f:
         vrm = f.read()
         
    put_text('Središnja cena najma: ' +round(df['Cena nekretnine'].median(), 2).astype(str)+' EUR')
    put_text('Središnja cena najma (po m\u00b2): ' +round(df['Po m2'].median(), 2).astype(str)+' EUR/m\u00b2')
    uz = len(df.index)
    put_text('Broj stanova na oglasima: ' +str(uz))
    put_text('Azurirano: ' +vrm)
    put_html('<br>')
      

    put_markdown("# 📈 Analiza stana iz oglasa: ")
    put_html('Iskopirajte link oglasa za izdavanje stana sa sajta <a href="https://www.halooglasi.com/nekretnine/izdavanje-stanova/beograd?sort=ValidFromForDisplay%2Casc" target="_blank">Halo oglasi</a>. Trenutno je moguca analiza samo stanova u Beogradu.')

    url_pattern = r'https://www.halooglasi.com/nekretnine/izdavanje-stanova/.+/[0-9]+'
    url = input("Link oglasa:", type=TEXT, placeholder="https://www.halooglasi.com/nekretnine/izdavanje-stanova/beograd", required=True)

    

    clear()
    
     

   #Validacija URL-a
    if re.match(url_pattern, url):
       id = int(re.search(r'/(\d+)(?:$|\?)', url).group(1))
       filtered_df = df.loc[df['ID'] == id, ['merged', 'Po m2', 'Opstina', 'Povrsina stana']].copy()
       if filtered_df.empty:
               toast('Oglas jos nije u bazi, ili je istekao. Pokusajte kasnije', duration=4, color='error')
               oglasi()
       else:
        filteri(df, filtered_df) 
    else:     
        toast('Neispravan link!', duration=4, color='error')
        oglasi()
             

def filteri(df, filtered_df):


    row = filtered_df.iloc[0]
    lokacija = row['merged'] 
    global pcena
    pcena = row['Po m2']
    pcena = round(pcena, 2)
    pcena = str(pcena)
    filtered_df2 = df[(df["merged"] == lokacija)].copy()    
    filtered_df2.to_csv("filtered_df2.csv")  
    check=[]
    rezultat(filtered_df2, lokacija, df, check)

   
        
        
     #Rezultat
def rezultat(filtered_df2, lokacija, df, check):
        

        
        df3 = round(filtered_df2['Cena nekretnine'].median(), 2).astype(str)
        df4 = round((filtered_df2['Po m2']).median(), 2).astype(str)
        low = round(filtered_df2['Po m2'].quantile(0.25), 2)
        high = round(filtered_df2['Po m2'].quantile(0.75), 2)
        mi = min(round(filtered_df2['Po m2'], 2))
        mx = max(round(filtered_df2['Po m2'], 2))
        uz = len(filtered_df2.index)
        
        if check == []:
           loca = lokacija
        else:
           separator = ', '
           loca = separator.join(check)
        
         
          
        
        #Skala
        value = float(pcena) 


        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = float(pcena),
            title = {'text': "EUR/m\u00b2"},
            delta = {'reference': float(df4)},
            gauge = {
                'axis': {'range': [(float(low)-(float((high-low)/2))), ((float(high)+(float((high-low)/2))))]},
                'bar': {'color': "rgba(0, 0, 0, 0)"},
                'steps' : [
                    {'range': [(float(low)-(float((high-low)/2))), float(low)], 'color': "white"},
                    {'range': [float(low), float(high)], 'color': "lightgreen"},
                    {'range': [float(high), ((float(high)+(float((high-low)/2))))], 'color': "white"}],
                'threshold' : {
                    'line': {'color': "black", 'width': 6},
                    'thickness': 1,
                    'value':value}}))
                    
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )            
                    
                    
                    
        
             
       
            
                       
        
        html = fig.to_html(include_plotlyjs="require", full_html=False, config={'displaylogo': False, 'modeBarButtonsToRemove': ['toImage']})  
                  
                    
        put_buttons(['Nazad'], onclick=[lambda:oglasi()], small=True, outline = True)             
        put_markdown("# Rezultat: ")
        
        if uz < 10:
        
           popup('Upozorenje', 'Za ovu lokaciju je oglasen mali broj stanova. Kliknite na dugme Prosiri pretragu i ukjucite okolne lokacije u analizu.')
           put_buttons(['Prosiri pretragu'], onclick=[lambda:expand_search(lokacija, df, check, loca)], small = True)
        
          


        put_text('Lokacija: ' +loca)  
        put_text('Središnja cena najma  ' +df3+' EUR')
        put_text('Središnja cena najma (po m\u00b2): ' +df4+' EUR/m\u00b2')
        put_text('Broj stanova na lokaciji: ' +str(uz))
        
        put_html(html)
        put_text('Zelena oblast predstavlja raspon cene u kojem se nalazi 50% stanova na datoj lokaciji, a crna kazaljka oznacava cenu pretrazivanog stana. Ukoliko se kazaljka nadje van zelene oblasti - stan je skuplji (ako je kazaljka s desne strane), odnosno jeftiniji (ako je kazaljka s leve strane) od 75% stanova na lokaciji kojoj pripada.')
        
  
        
        
       #Prosirenje pretrage 
def expand_search(lokacija, df, check, loca):
             
            clear()
             
            gmaps = googlemaps.Client(key='APIHERE')
            neighborhoods = pd.read_csv('neighborhoods.csv')
            locations = neighborhoods[['latitude', 'longitude']].to_numpy()
            knn_model = NearestNeighbors(n_neighbors=10, algorithm='ball_tree').fit(locations)


            def recommend_neighborhoods(address):

                geocode_result = gmaps.geocode(address)
                lat = geocode_result[0]['geometry']['location']['lat']
                lng = geocode_result[0]['geometry']['location']['lng']
                location = np.array([[lat, lng]])

                distances, indices = knn_model.kneighbors(location)
                recommended_neighborhoods = neighborhoods.iloc[indices[0]]['neighborhood'].tolist()
                return recommended_neighborhoods
                
            recommended_neighborhoods = recommend_neighborhoods(lokacija)
            if check == []:
               recommended_neighborhoods.remove(lokacija)
            else:   
               for item in check:
                   recommended_neighborhoods.remove(item)
            
            


            

            put_markdown("# Izaberite lokacije u blizni: ")
            checked = checkbox(options=recommended_neighborhoods, default=recommended_neighborhoods)
            check = [lokacija] + check + checked
            check = list(dict.fromkeys(check))
            filtered_df2 = df[df['merged'].isin(check)].copy()
            
            
            clear()         
            rezultat(filtered_df2, lokacija, df, check)

     
      
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=8080)
    args = parser.parse_args()
    start_server(oglasi, port=args.port, websocket_ping_interval=30, debug=True)




   
