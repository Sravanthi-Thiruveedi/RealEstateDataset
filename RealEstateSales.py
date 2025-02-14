# pip install dash
# pip install --upgrade pip setuptools wheel
# pip install geopy
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from dash import dcc, html, Dash, callback, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import requests

response = requests.get("https://example.com", verify=False)
print(response.text)
# Load the data
data = pd.read_csv('Real_Estate_Sales_2001-2022_GL.csv')
#data.head()
#data.info()
# Data Cleaning
data_cleaned = data.drop(data[data['Town'] == '***Unknown***'].index)
data_cleaned['Town'].unique()
css = ["https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css", ]
app = Dash(name="RealEstateSales Dashboard", external_stylesheets=css)
server = app.server
#Create a table to show the sample data
def create_table():
    top_40_data = data_cleaned[['Serial Number','List Year','Date Recorded','Town', 'Address', 'Assessed Value','Sale Amount',
                               	'Sales Ratio','Property Type','Residential Type','Non Use Code','Assessor Remarks','OPM remarks',
                            	'Location']].head(40)
    fig = go.Figure(data=[go.Table(
        header=dict(values=top_40_data.columns, align='left'),
        cells=dict(values=top_40_data.values.T, align='left'))
    ]
    )
    fig.update_layout(paper_bgcolor="#e5ecf6", margin={"t":0, "l":0, "r":0, "b":0}, height=800)
    # Adding a scrollable effect by fixing the header row
    fig.update_traces(cells=dict(height=30))  # Adjust cell height for better visibility
    fig.update_layout(
        autosize=False,
        height=400,  # Limit the table height to enable scrolling
    )
    return fig
#Town Sales by Year Chart
def create_townsalesbyyear_chart(town="Andover"):
    filtered_df = data_cleaned[data_cleaned["Town"] == town]
    filtered_df = filtered_df.groupby(['Town','List Year'])['Serial Number'].count().reset_index(name = 'Number of Sales')
    
    fig = px.line(filtered_df, x="List Year", y="Number of Sales", #color="Town",
                  title=f"Sale Amount for {town} Over the Years")
    
    fig.update_layout(paper_bgcolor="#e5ecf6", height=600)
    return fig
# Top 5 towns by Sale Amount
def create_top5towns_chart(year=2022):
    filtered_df = data_cleaned[data_cleaned["List Year"] == year]
    filtered_df = filtered_df.groupby(['Town','List Year'])['Sale Amount'].sum().reset_index(name = 'Total Sale Amount')
    filtered_df['Total Sale Amount (Millions)'] = filtered_df['Total Sale Amount'].div(1_000_000).round(2)
    filtered_df = filtered_df.sort_values(by = 'Total Sale Amount (Millions)', ascending=False).head(10)
 
    fig = px.bar(filtered_df, x="Town", y="Total Sale Amount (Millions)", color="Town",
                   title="Top 10 Towns by Sale Amount in the year {}".format(year),
                   text_auto=True)
    fig.update_layout(paper_bgcolor="#e5ecf6", height=600)
    return fig
# Number of Sales by Property Type 
def create_propertysales_chart(year=2022):
    filtered_df = data_cleaned[data_cleaned["List Year"] == year]
    filtered_df = filtered_df.groupby(['Property Type','List Year'])['Serial Number'].count().reset_index(name = 'Number of Sales')
 
    fig = px.pie(filtered_df, values='Number of Sales', names='Property Type', 
                 title ='Number of Sales by Property Type in the year {}'.format(year))
    fig.update_layout(paper_bgcolor="#e5ecf6", height=600)
    
    return fig
data_cleaned['town_new'] = data_cleaned['Town'] + ', Connecticut'
filtered_df = data_cleaned.groupby(['town_new'])['Sale Amount'].sum().reset_index(name='Total Sales')
filtered_df['Total Sales (M)'] = filtered_df['Total Sales'].div(1_000_000).round(2)


# Function to get latitude and longitude for each town
def geocode_town(town_name):
    geolocator = Nominatim(user_agent="geo_locator")
    location = geolocator.geocode(town_name)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None
        
# Add latitude and longitude columns
filtered_df["latitude"], filtered_df["longitude"] = zip(*filtered_df["town_new"].apply(geocode_town))
# Filter out towns with missing geolocation data
filtered_df = filtered_df.dropna(subset=["latitude", "longitude"])
# Function to create the map
def create_salesonmap_chart():
    fig = px.scatter_mapbox(
        filtered_df,
        lat="latitude",
        lon="longitude",
        size="Total Sales (M)",
        color="Total Sales (M)",
        center={"lat": 41.6032, "lon": -73.0877},
        hover_name="town_new",
        title="Town-wise Sales",
        mapbox_style="carto-positron"
        ,zoom=8
    )
    return fig
# Dropdown for selecting town
towns = sorted(data_cleaned["Town"].unique()) 
years = sorted(data_cleaned['List Year'].unique(),reverse = True)
listyears_old = data_cleaned.drop(data_cleaned[data_cleaned['List Year'].isin([2001, 2002, 2003, 2004, 2005])].index)
#listyears = listyears_old.sort_values(by='List Year', ascending=False) 
listyears = sorted(listyears_old['List Year'].unique(),reverse = True)
                   
cont_town = dcc.Dropdown(id="cont_town",options=[{"label": town, "value": town} for town in towns], value="Andover",clearable=False)
cont_year = dcc.Dropdown(id="cont_year",options=[{"label": year, "value": year} for year in years], value=2022,clearable=False)
cont_proptypeyears = dcc.Dropdown(id="cont_proptypeyears",options=[{"label": year, "value": year} for year in listyears], value=2022,clearable=False)
#app layout
app.layout = html.Div([
    html.Div([
        html.H1("Real Estate Sales Dataset Analysis", className="text-center fw-bold m-2"),
        html.Br(),
        dcc.Tabs([
            dcc.Tab([html.Br(),
                     dcc.Graph(id="dataset", figure=create_table())], label="Dataset"),
            dcc.Tab([html.Br(), "Select Town", cont_town, html.Br(),
                     dcc.Graph(id="townwisesales")],label="Year Wise Sales"),
            dcc.Tab([html.Br(), "Select Year", cont_year, html.Br(),
                     dcc.Graph(id="top10towns")], label="Town Wise Sales"),
            dcc.Tab([html.Br(), "Select Year", cont_proptypeyears, html.Br(),
                     dcc.Graph(id="propertytypesales")], label="Property Type Sales"),
            dcc.Tab([html.Br(), 
                     dcc.Graph(id="sales_map",figure=create_salesonmap_chart())], label="Town Wise Sales Map")
        ])
    ], className="col-8 mx-auto"),
], style={"background-color": "#3e6eb2", "height": "150vh"})
#Callbacks
@callback(Output("townwisesales", "figure"), [Input("cont_town", "value")])
def update_townsalesbyyear_chart(town):
    return create_townsalesbyyear_chart(town)

@callback(Output("top10towns", "figure"), [Input("cont_year", "value")])
def update_top5towns_chart(year):
    return create_top5towns_chart(year)

@callback(Output("propertytypesales", "figure"), [Input("cont_proptypeyears", "value")])
def update_propertysales_chart(year):
    return create_propertysales_chart(year)
if __name__ == "__main__":
    app.run(debug=True)





