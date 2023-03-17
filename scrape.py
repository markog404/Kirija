import requests
from bs4 import BeautifulSoup
import pandas
import os
import time
import datetime

#Definisanje pretrage
url="https://www.halooglasi.com/nekretnine/izdavanje-stanova/beograd?page="
lista_oglasa=[]  
page=0

#Scrape
while True:
    page+=1
    r=requests.get(url+str(page))
    c=r.content

   
    soup=BeautifulSoup(c,'html.parser')

  
    premium_ads=soup.find_all("div",{"class":"product-item product-list-item Premium real-estates my-product-placeholder"})
    top_ads=soup.find_all("div",{"class":"product-item product-list-item Top real-estates my-product-placeholder"})
    regular_ads= soup.find_all("div",{"class":"product-item product-list-item Standard real-estates my-product-placeholder"})
    

    if regular_ads!=[] or top_ads!=[] or premium_ads!=[]:
        
        
    #Premium oglasi

        for index in range(len(premium_ads)):
            premium_ads_dict={}  
            #naslov oglasa
            premium_ads_dict["Naslov"]=premium_ads[index].find("h3",{"class","product-title"}).text
            premium_ads_dict["ID"] = premium_ads[index].find("h3", {"class": "product-title"}).find("a").get("href").split('/')[-1].split('?')[0]


            #lokacija
            location_data=premium_ads[index].find_all("ul",{"class","subtitle-places"})[0]
            data_list=[]
            for item in location_data.find_all("li"):
                data_list.append(item.text)

            #mesto
            premium_ads_dict["Mesto"]=data_list[0].replace("\xa0","")
            
            #opstina
            premium_ads_dict["Opstina"]=data_list[1].replace("\xa0","")

            #gradska lokacija
            try:
                premium_ads_dict["Gradska lokacija"]=data_list[2].replace("\xa0","")
            except:
                premium_ads_dict["Gradska lokacija"]=None

            inner_apa_data=premium_ads[index].find_all("div",{"class":"value-wrapper"})
            inner_apa_data_list=[]
            for item in inner_apa_data:
                inner_apa_data_list.append(item.text)

            #ukupna povrsina stana
            premium_ads_dict["Povrsina stana"]=inner_apa_data_list[0].replace("\xa0m2Kvadratura","")


            #Cena stana
            premium_ads_dict["Cena nekretnine"]=premium_ads[index].find("div",{"class":"central-feature"}).text.replace("\xa0€","")


            lista_oglasa.append(premium_ads_dict)
        
        #Top oglasi

        for index in range(len(top_ads)):
            top_ads_dict={}  
            #naslov oglasa
            top_ads_dict["Naslov"]=top_ads[index].find("h3",{"class","product-title"}).text
            top_ads_dict["ID"] = top_ads[index].find("h3", {"class": "product-title"}).find("a").get("href").split('/')[-1].split('?')[0]

            #lokacija
            location_data=top_ads[index].find_all("ul",{"class","subtitle-places"})[0]
            data_list=[]
            for item in location_data.find_all("li"):
                data_list.append(item.text)

            #mesto
            top_ads_dict["Mesto"]=data_list[0].replace("\xa0","")
            
            #opstina
            top_ads_dict["Opstina"]=data_list[1].replace("\xa0","")

            #gradska lokacija
            try:
                top_ads_dict["Gradska lokacija"]=data_list[2].replace("\xa0","")
            except:
                top_ads_dict["Gradska lokacija"]=None

            inner_apa_data=top_ads[index].find_all("div",{"class":"value-wrapper"})
            inner_apa_data_list=[]
            for item in inner_apa_data:
                inner_apa_data_list.append(item.text)

            #ukupna povrsina stana
            top_ads_dict["Povrsina stana"]=inner_apa_data_list[0].replace("\xa0m2Kvadratura","")


            #Cena stana
            top_ads_dict["Cena nekretnine"]=top_ads[index].find("div",{"class":"central-feature"}).text.replace("\xa0€","")


            lista_oglasa.append(top_ads_dict)



        #Regular oglasi

        for index in range(len(regular_ads)):

            reg_ads_dict={}  

            #naslov oglasa
            reg_ads_dict["Naslov"]=regular_ads[index].find("h3",{"class","product-title"}).text
            reg_ads_dict["ID"] = regular_ads[index].find("h3", {"class": "product-title"}).find("a").get("href").split('/')[-1].split('?')[0]

            #lokacija
            location_data=regular_ads[index].find_all("ul",{"class","subtitle-places"})[0]
            data_list=[]
            for item in location_data.find_all("li"):
                data_list.append(item.text)

            #mesto
            reg_ads_dict["Mesto"]=data_list[0].replace("\xa0","")
            
            #opstina
            reg_ads_dict["Opstina"]=data_list[1].replace("\xa0","")

            #gradska lokacija
            reg_ads_dict["Gradska lokacija"]=data_list[2].replace("\xa0","")

            inner_apa_data=regular_ads[index].find_all("div",{"class":"value-wrapper"})
            inner_apa_data_list=[]
            for item in inner_apa_data:
                inner_apa_data_list.append(item.text)

            #ukupna povrsina stana
            reg_ads_dict["Povrsina stana"]=inner_apa_data_list[0].replace("\xa0m2Kvadratura","")


            #Cena stana
            reg_ads_dict["Cena nekretnine"]=regular_ads[index].find("div",{"class":"central-feature"}).text.replace("\xa0€","")


            lista_oglasa.append(reg_ads_dict)
        
    else:
        break
        

df=pandas.DataFrame(lista_oglasa)
#Formatiranje
df['Cena nekretnine']=df['Cena nekretnine'].apply(lambda x: x.replace('.', '')).astype(float)
df['Povrsina stana'] = df['Povrsina stana'].apply(lambda x: x.replace(',', '.')).astype(float)
df=df.drop_duplicates(subset=['ID'])
df['Po m2'] = round(df['Cena nekretnine'] / df['Povrsina stana'], 2)
df = df[ (df['Cena nekretnine'] > 100)  & (df['Cena nekretnine'] < 10000) & (df['Po m2'] < 60) ]
df['merged'] = df['Opstina'] + ' ' + df['Gradska lokacija']

df.to_csv("bgoutput.csv")

#Vreme scrape-a
mod_time = os.path.getmtime('bgoutput.csv')
mod_time_str = time.ctime(mod_time)
mod_time_obj = datetime.datetime.strptime(mod_time_str, "%a %b %d %H:%M:%S %Y")
serbian_time = mod_time_obj.strftime("%d.%m.%Y u %H:%M")
print(serbian_time)
with open('time.txt', 'w') as f:
    f.write(serbian_time)
