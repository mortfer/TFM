import streamlit as st
import pandas as pd
import numpy as np
import re
import plotly.express as px
import plotly.graph_objects as go
import json
import copy
from streamlit_plotly_events import plotly_events
import time
import functions as F
from collections import OrderedDict
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
import os


def app():    

    data_name='netflix'
    
    data_path='{}/../data'.format(os.path.dirname(os.path.abspath(__file__)))
    #Colors for each cluster chosen from px.colors.qualitative.Dark24
    colores=['#17BECF','#E15F99','#1CA71C','#FB0D0D','#DA16FF','#B68100','#EB663B','#511CFB','#00A08B','#FB00D1',\
            '#B2828D','#6C7C32','#862A16','#A777F1','#DA60CA','#6C4516','#0D2A63','#AF0038']

    #Load data  
    df_orig,topic_terms,vocab,term_frequency=F.get_data(data_name,data_path)
    #Copy data to avoid mutate it
    df=df_orig.copy(deep=True)
    
    ################Sidebar################
    
    #Place all the widgets on the sidebar
    with st.sidebar:
        num_tweets=st.empty()

    with st.sidebar:
        st.subheader('Filtro de fechas')
        
        minfechas=df['date'].min().strftime("%Y-%m-%d")
        maxfechas=df['date'].max().strftime("%Y-%m-%d")
        
        start_date=st.text_input('Desde (mínimo {})'.format(minfechas), minfechas,autocomplete=minfechas)
        end_date=st.text_input('Hasta (máximo {})'.format(maxfechas), maxfechas,autocomplete=maxfechas)
        if start_date.strip()=='':
            start_date=minfechas
        if end_date.strip()=='':
            end_date=maxfechas
        
    with st.sidebar:
        st.subheader('Filtro de clusters')
        Clusters = np.sort(df_orig['Cluster'].unique())
        clusters_filtro = st.multiselect('Elige clusters', Clusters)
        
    with st.sidebar:   
        st.subheader('Filtro de texto')
        text_filtro = st.text_input("Tweets con el texto...", '').strip()    

    with st.sidebar:   
        st.subheader('Filtro de enlaces externos')
        outlinks_filtro = st.text_input("Si se quiere elegir varios enlaces, escribir entre comas (p. ej.: youtube.com, youtu.be)", '').replace(' ','').split(',')
        outlinks_filtro= [i for i in outlinks_filtro if i] #Remove empty string if filter not provided    

    with st.sidebar:   
        st.subheader('Filtro de opiniones')
        posibles_opiniones=pd.unique(df_orig['Opinión'])
        opinion_filtro = st.multiselect('Tipo de opinión inferida mediante algoritmo', posibles_opiniones)

    with st.sidebar:   
        st.subheader('Filtro de idioma')
        #Split words
        lang_filtro = st.text_input("Si se quiere elegir varios idiomas, escribir entre comas (p. ej.: es,en)", '').replace(' ','').split(',')
        lang_filtro= [i for i in lang_filtro if i] #Para quitar el string vacío si no se pone nada en la caja de texto

    with st.sidebar:   
        st.subheader('Filtro de dispositivo')
        sources=pd.unique(df_orig['sourceLabel'])
        source_filtro = st.multiselect('Elige dispositivos', sources)

    st.title('Tweets {}'.format(data_name))
    st.write('20000 tweets extraidos desde Twitter con la palabra clave \'netflix\' desde el 28/09/2021 hacia atrás \
            con un mínimo de 5 retweets y en español')
    
    ############Filter df############
    
    
    #Every time filters are used, streamlit runs the full script again
    df=F.df_filtered(df,start_date,end_date,text_filtro,clusters_filtro,lang_filtro,outlinks_filtro,source_filtro,opinion_filtro)
    #Number of tweets on the sidebar
    num_tweets.write('Tweets: {} ({:.1f}%)'.format(len(df),100*len(df)/len(df_orig)))

    ##########Figures##########

    #Plotly figures configuration
    config1 = {'displayModeBar': False} 

    #Dicts to assign a position to every cluster regardless of current filters. This order will be kept along the full script
    cluster_counts_orig=df_orig['Cluster'].value_counts(ascending=True)
    clusters_indices=np.array(cluster_counts_orig.index).astype(str)
    cluster_to_pos=dict()
    for pos,cluster in enumerate(cluster_counts_orig.index):
        cluster_to_pos[cluster]=pos
    pos_to_cluster={v:k for k,v in cluster_to_pos.items()}

    #First row with 2 columns
    c11, c12 = st.columns((3,1))#Tuple specifying width 

    #Add figures
    cluster_counts_fig_func=F.cluster_figure(df_orig,df,topic_terms,colores,pos_to_cluster)
    c11.plotly_chart(cluster_counts_fig_func,use_container_width=True, config=config1)

    time_series_figure=F.temporal_fig(df,cluster_to_pos,clusters_filtro,colores)
    c11.plotly_chart(time_series_figure,use_container_width=True, config=config1)

    hourday_fig=F.hourday_figure(df_orig,df)
    c12.plotly_chart(hourday_fig,use_container_width=True, **{'config': config1})

    dayofweek_figure=F.dayofweek_figure(df_orig,df)
    c12.plotly_chart(dayofweek_figure,use_container_width=True, **{'config': config1})

    hashtags_counts_fig=F.value_counts_figure(df,'hashtags',top=5,title='Hashtags')
    c12.plotly_chart(hashtags_counts_fig,use_container_width=True, **{'config': config1})

    mentionedUsers_counts_fig=F.value_counts_figure(df,'mentionedUsers',top=5,title='Menciones')
    c12.plotly_chart(mentionedUsers_counts_fig,use_container_width=True, config=config1)



    #Second row with 3 columns
    c21,c22,c23=st.columns((1.5,1.5,1))

    #Distributions of retweets and likes
    violin_fig_retweets=F.violin_distribution(df,'retweetCount',clusters_filtro,cluster_to_pos,colores)
    c21.plotly_chart(violin_fig_retweets,use_container_width=True, **{'config': config1})

    violin_fig_likes=F.violin_distribution(df,'likeCount',clusters_filtro,cluster_to_pos,colores)
    c22.plotly_chart(violin_fig_likes,use_container_width=True, **{'config': config1})

    #Opinions and links
    Opinion_counts_fig=F.value_counts_figure(df,'Opinión',top=5,title='Opiniones')
    c23.plotly_chart(Opinion_counts_fig,use_container_width=True, config=config1)

    outlinks_counts_fig=F.value_counts_figure(df,'outlinks',top=5,title='Enlaces externos')
    c23.plotly_chart(outlinks_counts_fig,use_container_width=True, **{'config': config1})

    #Third row with 3 columns
    c31,c32,c33=st.columns((2,1,1))

    representative_tweets=F.representative_tweets(df)
    c31.plotly_chart(representative_tweets,use_container_width=True, **{'config': config1})


    relevant_terms=F.relevant_terms_table(df)
    c32.plotly_chart(relevant_terms,use_container_width=True,config={'displayModeBar': False})

    lang_counts_fig=F.value_counts_figure(df,'lang',top=5,title='Idioma')
    c33.plotly_chart(lang_counts_fig,use_container_width=True, config=config1)

    source_counts_fig=F.value_counts_figure(df,'sourceLabel',top=5,title='Dispositivo')
    c33.plotly_chart(source_counts_fig,use_container_width=True, **{'config': config1})


    st.subheader('Tabla de tweets')
    F.df_tabla(df)

