import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from argparse import ArgumentParser
from matplotlib.dates import DateFormatter
import os
import geopandas
import matplotlib.ticker as mtick
import gzip

parser = ArgumentParser()

parser.add_argument('--location', dest= 'location',
                                  default= 'Brazil', type= str,
                                  help= 'Brazil, US, World')
                  
parser.add_argument('--state_or_city', dest= 'state_or_city', 
                                       default= 'state', type= str,
                                       help= 'Brazil: state or city')

parser.add_argument('--not_last_date', dest= 'not_last_date', 
                                       default= False, type= bool,
                                       help= 'Run for the last date from the data frame')

parser.add_argument('--date', dest= 'until_date', 
                              default= '2020-05-05', type= str,
                              help= 'Set --not_last_date to use it')

parser.add_argument('--show_plot', dest= 'show_plot', 
                                   default= False, type= bool,
                                   help= 'Show plot for each location')

parser.add_argument('--output_name', dest= 'output_name', 
                                     default= 'output.csv', type= str,
                                     help= 'CSV file: output.csv')

parser.add_argument('--slice', dest= 'slice', 
                               default= False, type= bool,
                               help= 'Set true and use --slice_list')

parser.add_argument('--slice_name', dest= 'slice_list', 
                                    nargs='+', default=[])

parser.add_argument('--save_figdata', dest= 'save_figdata',
                                      default= False, type= bool,
                                      help= 'Save figure data')

parser.add_argument('--map', dest= 'plot_map', 
                             default= False, type= bool,
                             help= 'Plot maps')

args = parser.parse_args()

last = not args.not_last_date

path_data = 'data'
path_output = 'results/dfs'

if not os.path.exists(path_data):
    os.makedirs(path_data)

if not os.path.exists(path_output):
    os.makedirs(path_output)

# Defining useful functions

# Function to download data
def download_df(url, filename):
    with open(filename, 'wb') as f:
        r = requests.get(url)
        f.write(r.content)

    return pd.read_csv(filename)

### Function to calculate rates
def delta(df_conf):
    list_ = []
    list_.append(0)
    for j in range(len(df_conf) - 1):
        list_.append(df_conf[j+1] - df_conf[j])
    return list_  

# Downloading data

print('Downloading updated data')

if args.location == 'Brazil':
    
    url = "https://data.brasil.io/dataset/covid19/caso_full.csv.gz"
    filename =  path_data + '/caso_full.csv.gz'
    download_df(url, filename)
    with gzip.open(filename) as f:
        df = pd.read_csv(f)
    
    cases_key = 'last_available_confirmed'
    newcases_key = 'new_confirmed'
    newdeaths_key = 'new_deaths'
    
    df = df[ df['place_type'] == args.state_or_city]

    if args.state_or_city == 'state':
        df['city_ibge_code'] = df['city_ibge_code'].astype(int)
        df = df.drop(columns= ['city'])
        loc_key = 'state'

    else:
        df = df.dropna()
        df['city_ibge_code'] = df['city_ibge_code'].astype(int)
        loc_key  = 'city_ibge_code'
        args.slice_list= list(map(int, args.slice_list))

elif args.location == 'World':
    url = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
    filename = path_data + '/world_' + url.split("/")[-1]
    
    cases_key = 'total_cases'
    loc_key = 'location'
    newcases_key = 'new_cases'
    newdeaths_key = 'new_deaths'
    
    df = download_df(url, filename)

else:
    url = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
    filename = path_data + '/US_states' + '.csv'
    
    cases_key = 'cases'
    loc_key = 'state'
    deaths_key = 'deaths'
    
    df = download_df(url, filename)

if args.slice:
    locs_ = np.array(args.slice_list)
else:
    locs_ = df[loc_key].unique()

print('Running')

results_ = []

# EWM
alpha = 30.
alpha2 = 10.
alpha3 = 10.

def classifica(ncasos,vel_norm,acel_norm):
    
    CASES_THR = 50
    VEL_THR = 1.
    ACEL_THR0 = 0.05
    ACEL_THR1 = 0.1
    ACEL_THR2 = 0.25
    ACEL_THR3 = 0.5
    
    if ncasos < CASES_THR:
        return("INITIAL")
    elif vel_norm < VEL_THR:
        return("CONTROLLED")
    elif acel_norm< -ACEL_THR0:
        return("DECELERATING")
    elif abs(acel_norm)< ACEL_THR0:
        return("STABLE")
    elif acel_norm < ACEL_THR1:
        return("ACCELERATING0")
    elif acel_norm < ACEL_THR2:
        return("ACCELERATING1")
    elif acel_norm < ACEL_THR3:
        return("ACCELERATING2")
    else:
        return("ACCELERATING3")

color_dict = {
    'INITIAL': 'white',
    'ACCELERATING0': '#ffe6e6',
    'ACCELERATING1': '#ffb3b3',
    'ACCELERATING2': '#ff6666',
    'ACCELERATING3': '#ff0000',
    'DECELERATING': 'yellow', 
    'STABLE': '#9966ff', 
    'CONTROLLED': 'green'}       

for locs in locs_:

    df_ = df[ df[loc_key] == locs].sort_values(by='date').set_index('date')
    df_ =  df_ [ df_[cases_key]  > 0]
    df_.index = pd.to_datetime(df_.index)
    
    if args.location == 'US':
        df_['new_cases'] = df_[cases_key].diff(periods=1)
        df_['new_deaths'] = df_[deaths_key].diff(periods=1)
        newcases_key = 'new_cases'
        newdeaths_key = 'new_deaths'
    
    if args.state_or_city == 'city':
        cities = df_['city'][0]
        print(cities)
    else:
        print(locs)
     
    # velocity
    df_['rate_cases'] = df_[newcases_key].ewm(com = alpha).mean()
    df_['rate_deaths'] = df_[newdeaths_key].ewm(com = alpha).mean()
    
    # acceleration
    df_['accel_cases'] = df_['rate_cases'].diff().fillna(0).ewm(com= alpha2).mean()
    df_['accel_deaths'] = df_['rate_deaths'].diff().fillna(0).ewm(com= alpha2).mean()
    
    # acceleration rate
    df_['accelrate_cases'] = df_['accel_cases'].diff().fillna(0).ewm(com= alpha3).mean()
    df_['accelrate_deaths'] = df_['accel_deaths'].diff().fillna(0).ewm(com= alpha3).mean()
       
    ker=np.zeros(29)
    ker[18:]=1.
    
    if len(df_)<29:
        df_['norm'] = df_['last_available_confirmed']
    else:
        df_['norm']=np.convolve(df_['rate_cases'], ker,'same')
    
    df_['rate_cases_NORM(%)'] = 100.*df_['rate_cases'] / df_['norm']
    df_['accel_cases_NORM(%)'] = 100.*df_['accel_cases'] / df_['norm'] 
    df_.replace([-np.inf,np.inf,np.nan], 0, inplace=True)
    
    df_['rate_deaths_NORM(%)'] = 100.*df_['rate_deaths'] / df_['norm']
    df_['accel_deaths_NORM(bp)'] = 10000.*df_['accel_deaths'] / df_['norm']
    df_.replace([-np.inf,np.inf,np.nan], 0, inplace=True)
    
    df_['CLASSIFICATION'] = df_.apply(lambda x:classifica(x[cases_key],
                                                      x['rate_cases_NORM(%)'],
                                                      x['accel_cases_NORM(%)']),
                                                      axis=1) 
    # Plot
    
    if args.show_plot:
        
        rotulos = ['New Cases','Acceleration','Acceleration rate','Cases']
        cols = ['rate_cases','accel_cases','accelrate_cases',cases_key]
        cor = ['C4','C3','C2','C1']
        
        fig, axes = plt.subplots(1, 4, figsize= (24, 4)) 
        fig.subplots_adjust(wspace=0.3)
        
        for i in range(4):
            axes[i].plot(df_[cols[i]][10:],color= cor[i])
            
            if args.state_or_city == 'city':
                axes[i].set_title(cities, fontsize= 16)
            else:
                axes[i].set_title(locs, fontsize= 16)
                
            axes[i].set_ylabel(rotulos[i], fontsize= 12)
            axes[i].set_xlabel('Date', fontsize= 12)
            axes[i].grid(linestyle=':')
        
        plt.savefig(path_output + '/' + args.output_name + '.png', dpi=300)
        print('Saving ' + ' figure' )
        
    if args.save_figdata:
        path_fig_data = 'results/figures'
        if not os.path.exists(path_fig_data):
            os.makedirs(path_fig_data)

        if args.state_or_city == 'city':
            df_.to_csv(path_fig_data + '/df_figures_%s.csv' % str(cities), 
                       index= True, sep= ';')
        else:
            df_.to_csv(path_fig_data + '/df_figures_%s.csv' % str(locs), 
                       index= True, sep= ';')

    df_ = df_.reset_index()

    if last:
        results_.append(df_.iloc[-1].to_dict())
    else:
        idx_ = df_.index[df_['date'] == args.until_date]
        if len(idx_) > 0:
            results_.append(df_.iloc[idx_[0]].to_dict())
        else:
            print('%s data NOT available for %s' % (args.until_date, locs))
   
results = pd.DataFrame(results_)
results.to_csv(path_output + '/' + args.output_name + '.csv', index= True, sep= ';')

if args.plot_map:
    
    if args.state_or_city == 'city':
        shapefile="data/BRMUE250GC_SIR.shp"
        geodiv=geopandas.read_file(shapefile)
        geodiv.rename(columns={'CD_GEOCMU':'city_ibge_code'}, inplace=True)
       
    elif args.state_or_city == 'state':
            shapefile="data/BRUFE250GC_SIR.shp"
            geodiv=geopandas.read_file(shapefile)
            geodiv.rename(columns={'CD_GEOCUF':'city_ibge_code'}, inplace=True)

    geodiv["city_ibge_code"] = geodiv["city_ibge_code"].apply(pd.to_numeric)   
    df_map = results.merge(geodiv, on='city_ibge_code')
    df_map = geopandas.GeoDataFrame(df_map)
    
    fig, ax = plt.subplots(1, figsize=(28,16))
    
    df_map.plot(color=df_map["CLASSIFICATION"].map(color_dict), 
                categorical=True, linewidth=.5, 
                edgecolor='0.6', legend=True, 
                legend_kwds={'bbox_to_anchor':(.35, 0.4),
                'fontsize':20,'frameon':False}, ax=ax)
    
    ax.axis('off')
    plt.tight_layout()
    plt.savefig(path_output + '/' + args.output_name+'.png',dpi=300)
    plt.close(fig)

    if args.state_or_city == 'city':
        for ST in results.state.unique():
            
            df_ST = df_map[df_map['state'] == ST]
            fig, ax = plt.subplots(1, figsize=(28,16))
            df_ST.plot(color=df_ST["CLASSIFICATION"].map(color_dict), 
                       categorical=True, linewidth=.5, edgecolor='0.6',
                       legend=True, legend_kwds={'bbox_to_anchor':(.9, 0.1),
                       'fontsize':20,'frameon':False}, ax=ax)
            
            ax.axis('off')
            plt.tight_layout()
            plt.savefig(path_output + '/' + args.output_name + ST + '.png', dpi=300)
            print('Saving ' + ST + ' figure' )
            plt.close(fig)


