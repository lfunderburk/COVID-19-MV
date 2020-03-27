# Author: Laura Gutierrez Funderburk
# Creaed on March 2 2020
# Last Updated on March 23 2020

"""
This script pulls and updates repository 

https://github.com/CSSEGISandData/COVID-19

but can be modified to pull and update other repositories

The script also contains a few functions and widgets used in conjunction with DataVisCOVID-19 Jupyter Notebook

"""

#!pip install ipycombobox
#!jupyter nbextension enable --py [--sys-prefix|--user|--system] ipycombobox
# https://github.com/vidartf/ipycombobox

#pip install pycountry_convert

import pandas as pd
import requests as r
import sys, os
import os
from git import Repo
import git
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

from ipywidgets import widgets, VBox, HBox, Button
from ipywidgets import Button, Layout, widgets
from IPython.display import display, Javascript, Markdown, HTML
from ipycombobox import Combobox

import pandas as pd
import plotly
import plotly.offline as offline
import world_bank_data as wb
import plotly.graph_objects as go


def version_to_int_list(version):
    return [int(s) for s in version.split('.')]


assert version_to_int_list(plotly.__version__) >= version_to_int_list('3.8.0'), 'Sunburst plots require Plotly >= 3.8.0'


    
def run_4cell( b ):
    
    display(Javascript('IPython.notebook.execute_cell_range(IPython.notebook.get_selected_index(),IPython.notebook.get_selected_index()+4)'))    

style = {'description_width': 'initial'}

def print_commit(commit):
    print('----')
    print(str(commit.hexsha))
    print("\"{}\" by {} ({})".format(commit.summary,
                                     commit.author.name,
                                     commit.author.email))
    print(str(commit.authored_datetime))
    print(str("count: {} and size: {}".format(commit.count(),
                                              commit.size)))
    
def print_repository(repo):
    print('Repo description: {}'.format(repo.description))
    print('Repo active branch is {}'.format(repo.active_branch))
    for remote in repo.remotes:
        print('Remote named "{}" with URL "{}"'.format(remote, remote.url))
    print('Last commit for repo is {}.'.format(str(repo.head.commit.hexsha)))
    

    
if __name__ == "__main__":
     
    try:
        
        # Specify path
        os.environ["GIT_REPO_PATH"] = './COVID-19/'
        COMMITS_TO_PRINT = 5

        # Pull repo
        repo = git.Repo('./COVID-19/')
        o = repo.remotes.origin
        o.pull()
        repo_path = os.getenv('GIT_REPO_PATH')
        # Repo object used to programmatically interact with Git repositories
        repo = Repo(repo_path)
        # check that the repository loaded correctly
        if not repo.bare:
            print('Repo at {} successfully loaded.'.format(repo_path))
            print_repository(repo)
            # create list of commits then print some of them to stdout
            commits = list(repo.iter_commits('master'))[:COMMITS_TO_PRINT]
            # Optional - uncomment if you want to see who and what was committed
#             for commit in commits:
#                 print_commit(commit)
#                 pass
        else:
            print('Could not load repository at {} :('.format(repo_path))
    except:
        print("WARNING: Something went wrong pulling and updating the repo. Check you \n!git clone https://github.com/CSSEGISandData/COVID-19, and that you have not changed directories.")
    
    try:
        # Specify path to daily reports
        COVID_19_files = "./COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/"

        # Create master dataframe from each CSV - iterate
        all_df = []
        for subdir, dirs, files in os.walk(COVID_19_files):
            for file in files:
                #print os.path.join(subdir, file)
                filepath = subdir + os.sep + file

                if filepath.endswith(".csv"):
                    df_i = pd.read_csv(filepath)
                    all_df.append(df_i)
        # Master dataframe
        final = pd.concat(all_df,sort=False)
    
    except:
        
        print("WARNING: could not iterate and parse through files. Check you are in the right directory. \nCheck the directory structure of the repository is ./COVID-19/csse_covid_19_data/csse_covid_19_daily_reports/")
        
    try:
        # Convert column to datetime format
        final['Last Update'] =pd.to_datetime(final['Last Update'])
        # Sort df by Last Update 
        sorted_df = final.sort_values(by='Last Update')

        # remove coordinates
        sorted_df = sorted_df.iloc[:,0:6]
        
        sorted_df = sorted_df[pd.notnull(sorted_df['Last Update'])]
        
        sorted_df = sorted_df.replace({"US": "United States", "Taiwan*": "Taiwan","UK":"United Kingdom"})

        # Rename NaN columns
        values = {'Province/State': "No Name", 'Confirmed': 0, 'Deaths': 0, 'Recovered': 0}
        sorted_df = sorted_df.fillna(value=values)

        # Get unique countries
        countries_regions = sorted_df["Country/Region"].unique()
        # Get unique states
        provinces_states = sorted_df["Province/State"].unique()

        # Build country dictionary: states
        country_dic  = {}
        for i in range(len(countries_regions)): 

            states = sorted_df[sorted_df["Country/Region"]==countries_regions[i]]["Province/State"].unique()

            country_dic[countries_regions[i]] = states
    except:
        
        print("WARNING: check that 'Last Update' is still a column with dates and times in it. \nThe same applies for 'Country/Region' and 'Province/State' columns.")

    # UI 
    
    countries_regions = countries_regions.tolist()
    all_the_widgets = [widgets.Combobox(
        # value='John',
        placeholder='Choose country',
        options = countries_regions, 
        description ='Country/Region:',
        ensure_option=True,
        style=style,
        disabled=False
    )]
    

    # UI
    CD_button = widgets.Button(
        button_style='success',
        description="Choose Country", 
        layout=Layout(width='15%', height='30px'),
        style=style
    )    

    # Connect widget to function - run subsequent cells
    CD_button.on_click( run_4cell )
    
   
    # UI
    PR_button = widgets.Button(
        button_style='success',
        description="Plot Data", 
        layout=Layout(width='15%', height='30px'),
        style=style
    )  
    
    # Connect widget to function - run subsequent cells
    PR_button.on_click( run_4cell )
    
    ########################### 
    # SUNBURST PLOT
    # To get continents 
    import pycountry_convert as pc

    # Get earliest date
    least_recent_date = sorted_df['Last Update'].min()
    # Get latest date
    recent_date = sorted_df['Last Update'].max()

    # Get data for the latest date
    last_date = pd.Timestamp(recent_date.date())
    latest = sorted_df[sorted_df["Last Update"]>=last_date]

    # Create new dataframe
    confirmed = []
    death = []
    removed = []
    continent_cd = []
    country_cd = []
    good_country = []
    
    # Iterate over each country
    for item in countries_regions:
        try:

            # Transform country name into code
            country_code = pc.country_name_to_country_alpha2(item, cn_name_format="default")
            # Assign to appropriate continent
            continent_name = pc.country_alpha2_to_continent_code(country_code)

            # Start appending once we have both country and continent codes
            country_cd.append(country_code)
            continent_cd.append(continent_name)
            good_country.append(item)

            # Data on confirmed
            country_conf = latest[latest["Country/Region"]==item]["Confirmed"].sum()
            confirmed.append(country_conf)

            # Data on deaths
            country_deat = latest[latest["Country/Region"]==item]["Deaths"].sum()
            death.append(country_deat)

            # Data on recovered
            country_reco = latest[latest["Country/Region"]==item]["Recovered"].sum()
            removed.append(country_reco)


        except:
            # Data is dirty - some of these entries are not recognized by country_name_to_country_alpha2
            # or by country_alpha2_to_continent_code
            continue
    
    # Build dataframe
    sums_per_country = pd.DataFrame({"Country":good_country,"ContinentCode":continent_cd,\
                "Confirmed":confirmed,"Deaths":death,"Recovered":removed})  

    # Remove deaths and recovered, sort values for confirmed
    conf_df = sums_per_country.sort_values(by="Confirmed",ascending=False).iloc[:,0:3]

    # Remove entries that have a 0 under Confirmed/Deaths/Recovered
    conf_df = conf_df[(conf_df.T != 0).all()]
    
    # The sunburst plot requires weights (values), labels, and parent (region, or World)
    # We build the corresponding table here
    # Inspired and adapted from https://pypi.org/project/world-bank-data/ 
    columns = ['labels','parents',  'values']
    # Build the levels 
    # Level 1 - create copy of original 
    level1 = conf_df.copy()
    # Rename columns
    level1.columns = columns
    # Add a text column - format values column
    level1['text'] = level1['values'].apply(lambda pop: '{:,.0f}'.format(pop))

    # Create level 2
    # Group by continent code
    level2 = conf_df.groupby('ContinentCode').Confirmed.sum().reset_index()[['ContinentCode', 'ContinentCode', 'Confirmed']]
    # Rename columns
    level2.columns = columns
    level2['parents'] = 'World'
    # move value to text for this level
    level2['text'] = level2['values'].apply(lambda pop: '{:,.0f}'.format(pop))
    level2['values'] = 0

    # Create level 3 - world total as of latest date
    level3 = pd.DataFrame({'parents': [''], 'labels': ['World'],
                           'values': [0.0], 'text': ['{:,.0f}'.format(latest["Confirmed"].sum())]})

    # Create master dataframe with all levels
    all_levels = pd.concat([level1, level2,level3], axis=0,sort=True).reset_index(drop=True)
