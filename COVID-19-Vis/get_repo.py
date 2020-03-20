# Author: Laura Gutierrez Funderburk
# Creaed on March 2 2020
# Last Updated on March 19 2020

"""
This script pulls and updates repository 

https://github.com/CSSEGISandData/COVID-19

but can be modified to pull and update other repositories

The script also contains a few functions and widgets used in conjunction with DataVisCOVID-19 Jupyter Notebook

"""

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
    #         for commit in commits:
    #             print_commit(commit)
    #             pass
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
    all_the_widgets = [widgets.Dropdown(
                    value = countries_regions[0],
                    options = countries_regions, 
                    description ='Country/Region:', 
                    style = style, 
                    disabled=False)]
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
    