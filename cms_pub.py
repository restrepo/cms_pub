#!/usr/bin/env python3
import pandas as pd
import helium as hell
import time
import random
from selenium.common.exceptions import *
#settings
DEBUG=False
headless=True
tries=2


def RETURN(inspire_id,browser):
    browser.close()
    return inspire_id

def get_inspire_id(r,category,sleep=1,headless=False,DEBUG=False):
    '''
    Obtain inspire identification from category record
    '''
    trymax=5
    #time.sleep(sleep)    
    for i in range(trymax):
        try:
            browser=hell.start_chrome(headless=headless)
            url=f'https://cms-results.web.cern.ch/cms-results/public-results/publications/{category}/index.html'
            browser.get(url)
        except (TimeoutException,OSError):
            time.sleep(sleep*2)
            continue

        time.sleep(sleep)
        if DEBUG:
            print(f'{i}',end='\r')
        try:
            hell.click(r)
            break
        except (LookupError,WebDriverException, TimeoutException):#(LookupError,AttributeError):
            #browser.refresh()
            #browser.get(url)
            if i==trymax:                
                return RETURN(None,browser)
            continue
    time.sleep(sleep)
    try:
        inspire_id=browser.find_element_by_link_text('inSPIRE record').get_attribute('href').split('/')[-1]
    except NoSuchElementException:
        return RETURN(None,browser)

    return RETURN(inspire_id,browser)

#******* MAIN PROGRAM ******
#Get categories
browser=hell.start_chrome(headless=headless)

b=browser.get('https://cms-results.web.cern.ch/cms-results/public-results/publications/')

ctgrs=[ {b.find_element_by_tag_name('a').get_attribute('href').split('/')[-2]:b.text} 
           for b in browser.find_elements_by_tag_name('ul'
               )[1].find_elements_by_tag_name('li') ]

browser.close()

#For each category obtain full table and add inspire_id
#In each tr of tries, fill the Nones `inspire_id`
for tr in list(range(tries)):
    if tr>0: 
        dft_old=dft.copy()
        if not dft.empty and dft['inspire_id'].shape[0]-dft['inspire_id'].dropna().shape[0]==0:
            print('`inspire_id` column is complete!')
            break
        
    dft=pd.DataFrame()
    for c in ctgrs:
        ck=list( c.keys() )[0]
        print(f'{tr}:{ck}')
        if tr==0: ##obtain full table for each category: hellium is not required for this part
            url=f'https://cms-results.web.cern.ch/cms-results/public-results/publications/{ck}/index.html'
            dfs=pd.read_html(url)
            df=dfs[2].reset_index(drop=True)
            #Special cases
            if dfs[2].dropna().empty:
                dfs=pd.read_html(url,header=1)
                if len(dfs)>0:
                    df=dfs[0]
                    df=(df.T.reset_index().T).reset_index(drop=True)

            df=df.rename({0:'CMS_id',1:'report',2:'title',3:'journal',4:'date'},axis='columns')

            df['CTG']=ck
            df['category']=c[ck]

            #Checkpoint preparations
            if 'inspire_id' not in df.columns:
                df['inspire_id']=None
        else: #Filter category from existing DataFrame with full data
            df=dft_old[dft_old['CTG']==ck].reset_index(drop=True)
        for i in df.index: # add inspire_id
            print(random.choice(['.','*','_','-','\\','/',':',';','|','!']),end='\r')
            if df.loc[i,'inspire_id'] is None:
                r=df.loc[i,'report']
                try:
                    inspire_id=get_inspire_id(r,ck,headless=headless,DEBUG=DEBUG)
                except (UnboundLocalError,WebDriverException):
                    inspire_id=None
                if inspire_id is not None:
                    df.loc[i,'inspire_id']=inspire_id
                elif pd.isna(inspire_id):
                    df.loc[i,'inspire_id']=''
                #else: left as None
                if DEBUG:
                    print(tr,ck,i,df.loc[i,'report'],df.loc[i,'inspire_id'])

        dft=dft.append(df).reset_index(drop=True)
        print('')
dft.to_csv('cms.csv',index=False)
dft.to_json('cms.json',orient='records')
