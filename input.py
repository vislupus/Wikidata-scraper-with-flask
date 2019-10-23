import os
import sys
import re
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from flask import Flask, render_template, request, session
from werkzeug.utils import secure_filename
import pywikibot

app = Flask(__name__)

def wikidataID(link):
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, link)

    item_dict = item.get()
    clm_dict = item_dict["labels"]["en"]
    
    return clm_dict

@app.route('/')
def index():
	return render_template("index.html")

@app.route('/wiki_table', methods = ['POST'])
def wiki_table():
	if request.method == "POST":
		text_url = request.form['input']
		if text_url =="":
			return render_template("index.html")
	
	language = request.form.get('language')
	if language=="Choose language":
		language='en'
		
	wikipedia_page=request.form.get('wikipedia_page')
	wikidata_page=request.form.get('wikidata_page')
	commons=request.form.get('commons')
	label=request.form.get('label')
	descriptions=request.form.get('descriptions')
	coordinates=request.form.get('coordinates')
	instance=request.form.get('instance')
	image=request.form.get('image')
	wiki_pages=request.form.get('wiki_pages')
	country=request.form.get('country')
	location=request.form.get('location')
	commons_page=request.form.get('commons_page')
	
	title_list=[]
	temp_array=[]
	item={}
	
	
	item['text_url']=text_url
	item['language']=language
	
	item['wikipedia_page']=str(wikipedia_page=="true")
	item['wikidata_page']=str(wikidata_page=="true")
	item['commons']=str(commons=="true")
	item['label']=str(label=="true")
	item['descriptions']=str(descriptions=="true")
	item['coordinates']=str(coordinates=="true")
	item['instance']=str(instance=="true")
	item['image']=str(image=="true")
	item['wiki_pages']=str(wiki_pages=="true")
	item['country']=str(country=="true")
	item['location']=str(location=="true")
	item['commons_page']=str(commons_page=="true")
	
	if 'wikipedia.org' in text_url:
		p=Path(text_url)
		url="https://"+p.parts[1]

		# Load Wikipedia Category Page
		page_response = requests.get(text_url)
		page_content = BeautifulSoup(page_response.content, "html.parser")

		# check if there is a div tag with class mw-pages or mw-category
		if 'mw-pages' in str(page_content):
			# Pages in category
			divPage = page_content.find('div',{"id":"mw-pages"})
			
			# print("mw-pages")
			
		elif 'mw-category' in str(page_content):
			# Pages in category
			divPage = page_content.find('div',{"class":"mw-category"})
			
			# print("mw-category")
			
		# Get li tags
		li=divPage.find_all('li')
			
		# Looping through all the links
		for j in range(len(li)):
			a=li[j].find('a', href=True)

			# Title of article
			title_list.append(a['title'])
			
			item[a['title']]={}
			item[a['title']]["title"]=a['title']
			
			# Create new link for subpage
			url_new=url+a['href']
			item[a['title']]["title_url"]=url_new
			
			# WikiData from URL
			try:
				page_data = requests.get(url_new)
				page_data_content = BeautifulSoup(page_data.content, "html.parser") 
				li_data=page_data_content.find('li',{"id":"t-wikibase"})
				
				a_data=li_data.find('a', href=True)
				a_data_id=a_data['href'].replace("https://www.wikidata.org/wiki/Special:EntityPage/","")
				a_data_entity="http://www.wikidata.org/entity/"+a_data_id
				
				# Url of wikidata page
				item[a['title']]["wikidata_id"]=a_data_id
				item[a['title']]["wikidata_url"]=a_data_entity
				
				page_data_instance = requests.get(a_data_entity)
				page_data_instance_content = BeautifulSoup(page_data_instance.content, "html.parser") 
					
				b=str(page_data_instance_content)
				text_json = json.loads(b)
				
				# Whole JSON data of a page
				# print(text_json)
				
				if label=="true":
					try:
						item[a['title']]["label"]=text_json["entities"][a_data_id]['labels'][language]['value']
					except:
						pass
				
				if descriptions=="true":
					try:
						item[a['title']]["descriptions"]=text_json["entities"][a_data_id]['descriptions'][language]['value']
					except:
						pass
				
				if instance=="true":
					try:
						for i in range(len(text_json["entities"][a_data_id]['claims']['P31'])):
							P31_item=wikidataID(text_json["entities"][a_data_id]['claims']['P31'][i]['mainsnak']["datavalue"]["value"]["id"])
							temp_array.append(P31_item)
						
							item[a['title']]['instance']=temp_array
						temp_array=[]
					except:
						pass
				
				if country=="true":
					try:
						for i in range(len(text_json["entities"][a_data_id]['claims']['P17'])):
							P17_item=wikidataID(text_json["entities"][a_data_id]['claims']['P17'][i]['mainsnak']["datavalue"]["value"]["id"])
							temp_array.append(P17_item)
							
							item[a['title']]['country']=temp_array
						temp_array=[]
					except:
						pass
				
				if location=="true":
					try:
						for i in range(len(text_json["entities"][a_data_id]['claims']['P131'])):
							P131_item=wikidataID(text_json["entities"][a_data_id]['claims']['P131'][i]['mainsnak']["datavalue"]["value"]["id"])
							temp_array.append(P131_item)
							
							item[a['title']]['located']=temp_array
						temp_array=[]
					except:
						pass
				
				if image=="true":
					try:
						for i in range(len(text_json["entities"][a_data_id]['claims']['P18'])):
							P18_item=text_json["entities"][a_data_id]['claims']['P18'][i]['mainsnak']["datavalue"]["value"]
							temp_array.append(P18_item)
							
							item[a['title']]['image']=temp_array
						temp_array=[]
					except:
						pass
				
				if commons=="true":
					try:
						for i in range(len(text_json["entities"][a_data_id]['claims']['P373'])):
							P373_item=text_json["entities"][a_data_id]['claims']['P373'][i]['mainsnak']["datavalue"]["value"]
							temp_array.append(P373_item)
							
							item[a['title']]['commons']=temp_array
						temp_array=[]
					except:
						pass
				
				if coordinates=="true":
					try:
						temp_array_lat=[]
						temp_array_lon=[]
						for i in range(len(text_json["entities"][a_data_id]['claims']['P625'])):
							P625_item_lat=text_json["entities"][a_data_id]['claims']['P625'][i]['mainsnak']["datavalue"]["value"]['latitude']
							P625_item_lon=text_json["entities"][a_data_id]['claims']['P625'][i]['mainsnak']["datavalue"]["value"]['longitude']
							
							temp_array_lat.append(P625_item_lat)
							item[a['title']]['latitude']=temp_array_lat
							
							temp_array_lon.append(P625_item_lon)
							item[a['title']]['longitude']=temp_array_lon
					except:
						pass
					
				if commons_page=="true":
					try:
						item[a['title']]['commonswiki']=text_json["entities"][a_data_id]['sitelinks']['commonswiki']['title']
					except:
						pass 
				
				if wiki_pages=="true":
					try:
						item[a['title']]['wiki']=text_json["entities"][a_data_id]['sitelinks'][str(language)+'wiki']['title']
					except:
						pass
			except:
				pass
				
		length=len(title_list)

	else:
		pass
		
	return render_template("wiki_table.html", length=length, title_list=title_list, item=item)
	
if __name__ == '__main__':
	app.run()