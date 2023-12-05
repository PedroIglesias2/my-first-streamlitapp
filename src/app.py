import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json
from copy import deepcopy

# Put main df in cache
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

@st.cache_data
def load_json(path):
    with open(path) as json_file:
        data_json1 = json.load(json_file)
    return data_json1

# we load raw data
dogs_df_raw = load_data(path="./data/kul100od1001.csv")
dogs_df = deepcopy(dogs_df_raw)

# We load json from previously saved json file from the URL below
# URL of json:'https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Statistische_Quartiere?service=WFS&version=1.1.0&request=GetFeature&outputFormat=GeoJSON&typename=adm_statistische_quartiere_map'
zh_json = load_json(path = "./data/zh_json.json")

#Declare a map dictionary to map a quarter number with its name
map_dict = {}
for i in range(len(zh_json['features'])):
    map_dict[zh_json['features'][i]['properties']["qnr"]]=zh_json['features'][i]['properties']["qname"]

#Translate column names from German to english
translation_dict = {
    'StichtagDatJahr': 'RecordYear',
    'DatenstandCd': 'DataStatusCd', # Datenstand, D = definitiv, P = provisorisch
    'HalterId': 'OwnerID',
    'AlterV10Cd': 'AgeV10Cd', #10-year age group of the dog-owning person
    'AlterV10Lang': 'AgeV10Lang',
    'AlterV10Sort': 'AgeV10Sort',
    'SexCd': 'SexOwnerCd', # Gender of the person owning the dog
    'SexLang': 'SexOwnerLang',
    'SexSort': 'SexOwnerSort',
    'KreisCd': 'DistrictCd',
    'KreisLang': 'DistrictLang',
    'KreisSort': 'DistrictSort',
    'QuarCd': 'QuarCd',
    'QuarLang': 'QuarLang',
    'QuarSort': 'QuarSort',
    'Rasse1Text': 'Breed1Text',
    'Rasse2Text': 'Breed2Text',
    'RasseMischlingCd': 'BreedMixedCd', # Mixed breed of dog. Indicates whether the dog is a pedigree dog (only Race1 filled),
    'RasseMischlingSort': 'BreedMixedSort', #  mixed breed, secondary breed known (Race1 and Race2 known) or mixed breed, 
    'RasseMischlingLang': 'BreedMixedLang', #secondary breed unknown (Race1 known and Race2 unknown).
    'RassentypCd': 'BreedTypeCd',
    'RassentypLang': 'BreedTypeLang',
    'RassentypSort': 'BreedTypeSort',
    'GebDatHundJahr': 'DogBirthYear',
    'AlterVHundCd': 'AgeDogCd',
    'AlterVHundLang': 'AgeDogLang',
    'AlterVHundSort': 'AgeDogSort',
    'SexHundCd': 'SexDogCd',
    'SexHundLang': 'SexDogLang',
    'SexHundSort': 'SexDogSort',
    'HundefarbeText': 'DogColorText',
    'AnzHunde': 'NumDogs'
}
dogs_df.rename(columns = translation_dict, inplace = True )


# Add title and header
st.title("Dogs in Zurich: Data Exploration")
st.caption("Data set from 2015 - 2023 (May)")
# Widgets: checkbox (you can replace st.xx with st.sidebar.xx)
if st.checkbox("Show Dataframe"):
    st.subheader("This is my dataset:")
    st.dataframe(data=dogs_df)
    # st.table(data=dogs_df)

# Setting up columns
left_column, right_column  = st.columns(2)

# Widgets: selectbox
osex = ["All"]+sorted(pd.unique(dogs_df['SexOwnerLang']))
owSex = left_column.selectbox("Choose owner's sex", osex)

# Widgets: radio buttons
sexDog = right_column.radio(
    label="Dog's sex", options=['All', 'Males only', "Females only"])


# Flow Control for conditions
if not owSex == "All":
    reduced_df = dogs_df[dogs_df["SexOwnerLang"] == owSex]
else:
    reduced_df = dogs_df

if sexDog ==  'Males only':
    reduced_df = reduced_df[reduced_df["SexDogLang"] == "männlich"]
elif sexDog ==  "Females only":
    reduced_df = reduced_df[reduced_df["SexDogLang"] == 'weiblich']

st.caption("Total number of dogs with these characterestics: "+str(reduced_df.OwnerID.count()) )

#Sort data by quarter and add its mapping column
num_of_dogs =  reduced_df.groupby("QuarSort").OwnerID.count()
num_of_dogs = pd.DataFrame(num_of_dogs)
num_of_dogs.reset_index(inplace = True)


def mapping(quarnum):
    try:
        val = map_dict[quarnum]
    except KeyError:
        val = 0
    return val
num_of_dogs["QuarLang"] = num_of_dogs["QuarSort"].apply(mapping)

fig = px.choropleth_mapbox( geojson=zh_json, featureidkey = "properties.qnr",  
                           locations=num_of_dogs["QuarSort"], color= num_of_dogs["OwnerID"], 
                           mapbox_style="carto-positron",
                           zoom=9.9, center = {"lat":47.3769, "lon": 8.5417},
                           opacity=0.5,
                           hover_name=num_of_dogs["QuarLang"],
                           hover_data={"Number of dogs" : num_of_dogs["OwnerID"]},
                           color_continuous_scale="RdYlGn_r",
                           # reversescale = True,
                           range_color=(80, 5600),
                           title = "Number of dogs per quarter", 
                           
                          )


fig.update_traces(customdata = num_of_dogs["OwnerID"],
                    text = num_of_dogs["QuarLang"],
                    hovertemplate= "<b>%{text}</b><br><br>" +
                    "Number of dogs: %{customdata:.0f}<br>")


st.plotly_chart(fig)
