import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from dash.dependencies import Input, Output
import geopandas as gpd
import json
from flask_caching import Cache
import os
import multiprocessing
import connectiondb as db
#import plotly.graph_objects as go
#from dash.exceptions import PreventUpdate


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, 
                external_stylesheets=external_stylesheets,
                title='Crimes in Chicago')

server = app.server

CACHE_CONFIG = {
    'CACHE_TYPE' : 'filesystem',
    'CACHE_DIR' : 'my-cache-directory-sqlite',

}

cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

cache.clear()

userr = os.environ.get('USER')
passw = os.environ.get('KEY')
database = os.environ.get('DATABASE')
#print("Database : ", database)
engine = db.create_connection_sqlite(database)

#
m =  pd.read_csv("./m.csv")

locations = [str(each) for each in m.columns] 
#locations = ["STREET",  "RESIDENCE", "APARTMENT", "SIDEWALK", "OTHER", "PARKING LOT/GARAGE(NON.RESID.)", "ALLEY", "RESIDENTIAL YARD (FRONT/BACK)", "SMALL RETAIL STORE", "SCHOOL, PUBLIC, BUILDING" ]

districts = [str(each) for each in m["District"]]
#districts = ["1", "2","3","4","5","6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]

fonts = {
    'title':'Playfair Display'
    }
colors = {
        'background':'#111111',
        'text':'#7FDBFF',
        'lp':'#DDEE54'
}

e = open('./boundaries.json')
df2 = json.load(e)

district_lookup = {feature['properties']['dist_num']: feature 
                   for feature in df2['features']}
selections = {"2"}

ok = False
@cache.memoize()
def getmask(sel_districts,start,end):
    
    sel_districts = [float(each) for each in sel_districts]
    sel_districts = tuple(sel_districts)
    
    # FOR POSTGRESQL databases, uncomment the following line and comment the ones for SQLite (SQLite needs the single quotes ' ' for parsing strings):
    
    #sel_districts = ", ".join(str(x) for x in sel_districts)

    # beginning of SQLite:
    new_sel = []
    for each in sel_districts:
        each = "'{}'".format(each)
        new_sel.append(each)

    sel_districts = ", ".join(str(x) for x in new_sel)
    # end of SQLite
    
    sel_districts = "(" + sel_districts + ")"

    query = """select "District","date","Districtperday" as "total crimes" from crimes_alldata where "District" in {} and "date" between '{}' and '{}' group by "District", "date", "Districtperday" """.format(sel_districts,start,end)

    result_set, columns = db.execute_read_query_sqlite(engine, query)
    columns = [each[0] for each in columns]
    dff = pd.DataFrame(result_set, columns = columns)
    
    return dff

@cache.memoize()
def getmask_loc(sel_districts,start,end):
    
    sel_districts = [float(each) for each in sel_districts]
    sel_districts = tuple(sel_districts)

    # FOR POSTGRESQL databases, uncomment the following line and comment the ones for SQLite:
    
    #sel_districts = ", ".join(str(x) for x in sel_districts)

    # beginning of SQLite:
    new_sel = []
    for each in sel_districts:
        each = "'{}'".format(each)
        new_sel.append(each)

    sel_districts = ", ".join(str(x) for x in new_sel)
    # end of SQLite
    
    sel_districts = "(" + sel_districts + ")"

    str_locations = tuple(locations[2:6])

    
    query = """select "District", "LocationDescription", sum("total") as "TOTAL" from (
                select "District","date", "LocationDescription", count("Location/Distrperday") as total from crimes_alldata where 
                "District" in {} and "date" between '{}' and '{}' and "LocationDescription" in {}
group by "District", 
"LocationDescription","date", "Location/Distrperday") as sss
group by "District", "LocationDescription" """.format(sel_districts,start,end,str_locations)
    result_set, columns = db.execute_read_query_sqlite(engine, query)
    
    columns = [each[0] for each in columns]
    dffbar = pd.DataFrame(result_set, columns = columns)
    
    return dffbar

start = '2012-01-01'
end = '2013-01-01'
data = selections
dfbar = getmask_loc(data,start,end)
fig_bar = px.bar(dfbar, x="TOTAL", y="District", orientation = "h", color="LocationDescription", 
color_discrete_map={
    'RESIDENCE': 'red',
    'STREET': 'white',
    'APARTMENT':'gray',
    'SIDEWALK':'yellow',
    
},barmode = 'stack')

if not ok or len(data) == 1:
    for data in fig_bar.data:
        data["width"] = 0.25
    ok = True
    #print("Change OK in second!!")
fig_bar.update_layout(
paper_bgcolor='rgba(0,0,0,0)',
plot_bgcolor='rgba(0,0,0,0)',
font_family=fonts["title"],
#font_color="blue",
font_color="#636efa",
title_font_family="Times New Roman",
title_font_color="#636efa",
legend_title_font_color="aliceblue",
title = {
    'text' : "Where crimes occured",
    'x':0.5,
    'y':0.95,
    'xanchor':'center',
    'yanchor':'top'
    }
)
fig_bar.update_traces(
                marker_line_width=1.5, opacity=0.5)
fig_bar.update_xaxes(
title_text = "total crimes",
showline = False,
linewidth = 10,
tickwidth = 0.5,
ticklen = 2,
#font_size = "10px",
),
fig_bar.update_yaxes(
    type='category',
    #categoryorder='total ascending',
    showline = False,
    linewidth = 10,
    tickwidth = 0.5,
    ticklen = 2,
)

## Next 2 functions are for the Chropleht map update:

def get_highlights(selecteds, geojson=df2, district_lookup=district_lookup):
    geojson_highlights = dict()
    for k in geojson.keys():
        if k != 'features':
            geojson_highlights[k] = geojson[k]
        else:
            geojson_highlights[k] = [district_lookup[selected] for selected in selecteds]        
    return geojson_highlights

@cache.memoize()
def get_figure(selecteds):

    fig = px.choropleth_mapbox(
                                m,
                                locations="id",
                                geojson=df2,
                                color="beats",
                                hover_name="District",
                                hover_data=["District","beats"],
                                #title="",
                                mapbox_style="carto-darkmatter",
                                color_continuous_scale=px.colors.sequential.Plasma,
                                opacity=0.2,
                                center={"lat":41.8, "lon": -87.7},
                                
    )
    fig.update_layout(
                      mapbox_style="carto-darkmatter", 
                      mapbox_zoom=9,
                      mapbox_center={"lat":41.8, "lon": -87.7},
                      margin={"r":0,"t":0,"l":0,"b":0},
                      uirevision='constant',
                      )
    fig.layout.paper_bgcolor = 'black'
    fig.update_coloraxes(colorbar_bgcolor=colors['background'])
    if len(selecteds) > 0:
        # highlights contain the geojson information for only 
        # the selected districts
        highlights = get_highlights(selecteds)

        fig.add_trace(
            px.choropleth_mapbox(
                m,
                locations="id",
                geojson=highlights,
                color="beats",
                hover_name="District",
                hover_data=["District","beats"],
                color_continuous_scale=px.colors.sequential.Plasma,
                opacity=1,
                ).data[0])

        fig.update_layout(
                      mapbox_style="carto-darkmatter", 
                      mapbox_zoom=9,
                      mapbox_center={"lat":41.8, "lon": -87.7},
                      margin={"r":0,"t":0,"l":0,"b":0},
                      uirevision='constant',
                      )
        fig.layout.paper_bgcolor = 'black'
        fig.update_coloraxes(colorbar_bgcolor=colors['background'])
        
    
    return fig



app.layout =html.Div(
    style={'backgroundColor':colors['background'],
           'position':'relative',
            'zIndex':1},
    
    children=[
        
        html.H1(
            children='Crimes in the Chicago city', 
            className = 'big_title'
        ),
        html.H2(
            children='pick a date range and select the districts on the chicago map!', 
            className = 'subtitle',
        ),
            
        html.Div(
            id = "LP",
            className = 'h-50',
            style={
                'position':'fixed',
                'padding':0,
                'margin':0,
                'top':0,
                'left':0,
                'width': '100%',
                'height': '100%',
                'zIndex':1003,
                'textAlign':'center',
            },
           children =[
               
               
                html.Div(
                    id = "LP_div",
                    style={
                    },
                    
                    children=[
                        html.H1(
                        children='Welcome!!',
                        style={'color':'coral'}
                        ),
                        html.H2(
                        id = "lp_description",
                        children=[
                        html.P(["""This is an application to visualize data of crimes in the city of Chicago.""", html.Br() ,"""The dataset comes from the Chicago prefectures and it's stored in a relational database (SQLite).""", html.Br(), dcc.Markdown(""" When you interact with it, you're performing requests that process nearly _***1,500,000*** records!_""")])
                        ]
                        ),
                        html.Button('Rock It!', id='lp_button',
                            ),
                 ]
                )
           ]
        ),
        html.Div(
            id= "data_div",
            style={
                #'display':'inline-block',
                'marginLeft':'auto',
                'marginRight':'auto',
                'justify':'center',
                'textAlign':'center',      
                    },
            children = [
            dcc.DatePickerRange(
                id="date-picker-range",
                start_date_placeholder_text="Start Period",
                end_date_placeholder_text="End Period",
                calendar_orientation='vertical',
                min_date_allowed='2012-01-01',
                max_date_allowed='2015-07-21',
                start_date = '2012-01-01',
                end_date ='2013-01-01',
                style={
                    'textAlign':'center'
                    }
            ),
            ]
        ),
        html.Div(
            id = "boundstack_div",
        children=[
            html.Div(
            id = "beats_div",
            draggable="True",
            children=[
                html.H2(
                    id = "beats_title",
                    children = "BEATS"
                    ),
                html.P(
                    id = "beats_text",
                    children= "A tract of land designated for police patrol. A naive understanding would suggest that the more beats a district has, the higher it's the security."),
                html.Button('Got It!', id='beats_button',style={'margin':'10px','width':'10px','height':'30px','border':0,'padding':0,}
                            ),
                ]
            ),
            
            dcc.Graph ( 
                 
            id='boundary_map',
            style={
               'width': '49%', 'display': 'inline-block'},
            config = {
                    'scrollZoom':False
                                    },
            figure=get_figure(selections)
            ), 
            
            dcc.Graph (
            id='stacked_bar',
            style={#'backgroundColor':colors['background'],
               'width': '49%', 'display': 'inline-block'},
            figure=fig_bar
            ),
        ]
        ),
        dcc.Graph (
        id='time_series_district',
        style={
               'backgroundColor':colors['background'],
               }
        #figure=fig
        ),
        dcc.Store(id='signal'),
        html.Div(
            id = "contacts",
            children = [
                html.A(
                        html.Img(id = "gitimg",src="./assets/github2.png"),
                        href="https://github.com/danielfurlan/chicago_crimes", target='_blank'
                        ),
                html.A(
                        html.Img(id = "linkimg",src="./assets/linkedin.png"),
                        href="https://www.linkedin.com/in/daniel-frederico-masson-furlan-22666a5b/", target='_blank'
                        )
                    ]
            )
])
first_entry = True
beats = True
# For the Landing Page:
if first_entry:
    @app.callback(
    Output('LP', component_property='style'),
    [Input('lp_button', 'n_clicks')]
    )
    def update_style(click):
        global first_entry
        if click is None:
            raise PreventUpdate
        else:
            first_entry = False
            return {'display':'none'}#,{'display':'none'}

    
if beats:
    @app.callback(
    Output('beats_div', component_property='style'),
    [Input('beats_button', 'n_clicks')]
    )
    def update_style(click):
        global beats
        if click is None:
            raise PreventUpdate
        else:
            beats = False
            return {'display':'none'}
    

@app.callback(
    Output('signal', 'data'),
    [Input('boundary_map', 'clickData')],
)

def get_boundary_map(clickData):
    global selections
    sel = selections
    if clickData is not None :            
        location = clickData['points'][0]['location']
        if str(location) not in sel:
            sel.add(str(location)) #### maybe str(location)
        else:
            sel.remove(str(location))
    sel_districts = list(sel)
    sel_districts.sort()
    return sel_districts

@app.callback(
    Output('boundary_map', 'figure'),
    [Input('signal', 'data')],
)
#@cache.memoize()
def update_map(data):
    return get_figure(set(data))

@app.callback(
    Output('time_series_district', 'figure'),
    [Input('signal', 'data')],
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
)
def update_time_series(data, start,end):
    if len(data) == 0:
        #raise PreventUpdate
        fig = px.line(template="plotly_dark",render_mode = "webgl",
                    range_x = [start,end])
        fig.update_layout(
        font_family=fonts["title"],
        font_color="#636efa",
        title_font_family="Times New Roman",
        title_font_color="#636efa",
        legend_title_font_color="white",
            title = {
            'text' : "Total Crimes per District",
            'x':0.5,
            'y':0.95,
            'xanchor':'center',
            'yanchor':'top'
            },)
        fig.update_xaxes(
            title_text="date"
        )
        fig.update_yaxes(
            title_text="crimes"
        )
        return fig
        #raise PreventUpdate
    else:
        dff= getmask(data,start,end)
        fig = px.line(dff, x='date', y='total crimes',color='District',template="plotly_dark",render_mode = "webgl",)
        fig.update_layout(
        hovermode="x",
        font_family=fonts["title"],
        font_color="#636efa",
        title_font_family="Times New Roman",
        title_font_color="#636efa",
        legend_title_font_color="aliceblue",
            title = {
            'text' : "Total Crimes per District",
            'x':0.5,
            'y':0.95,
            'xanchor':'center',
            'yanchor':'top'
            }
                        )
        fig.update_yaxes(
            title_text="crimes",
        )
        return fig

@app.callback(
    Output('stacked_bar', 'figure'),
    [Input('signal', 'data')],
    Input('date-picker-range', 'start_date'),
    Input('date-picker-range', 'end_date'),
)
def update_stack_bar(data,start,end):
    global ok
    if len(data) == 0:
        #raise PreventUpdate
        
        fig_bar = px.bar()
        fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family=fonts["title"],
        font_color="#636efa",
        title_font_family="Times New Roman",
        title_font_color="#636efa",
        legend_title_font_color="white",
        title = {
            'text' : "Where crimes occured",
            'x':0.5,
            'y':0.95,
            'xanchor':'center',
            'yanchor':'top'
            },
        )
        fig_bar.update_xaxes(
        title_text = "total crimes",
        #font_size= "5px",
        )
        fig_bar.update_yaxes(
        title_text = "Districts",
        type='category',
        categoryorder='category ascending',
        )
        ok = False
        return fig_bar
    else:
        dfbar = getmask_loc(data,start,end)
        fig_bar = px.bar(dfbar, x="TOTAL", y="District", orientation = 'h',
        color="LocationDescription", #color_continuous_scale=px.colors.sequential.Viridis
        color_discrete_map={
            'RESIDENCE': 'red',
            'STREET': 'white',
            'APARTMENT':'gray',
            'SIDEWALK':'yellow',
            
        }
        ,barmode = 'stack',
        )
        if not ok or len(data) == 1:
            for data in fig_bar.data:
                data["width"] = 0.25
            ok = True
        fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_family=fonts["title"],
        font_color="#636efa",
        title_font_family="Times New Roman",
        title_font_color="#636efa",
        legend_title_font_color="aliceblue",
        title = {
            'text' : "Where crimes occured",
            'x':0.5,
            'y':0.95,
            'xanchor':'center',
            'yanchor':'top'
            }
        )
        fig_bar.update_traces(
                        marker_line_width=1.5, opacity=0.5)
        fig_bar.update_xaxes(
        title_text = "total crimes",
        showline = False,
        linewidth = 10,
        tickwidth = 0.5,
        ticklen = 2,
        ),
        fig_bar.update_yaxes(
            type='category',
            showline = False,
            linewidth = 10,
            tickwidth = 0.5,
            ticklen = 2,
        )
        return fig_bar

if __name__ == '__main__':
    app.run_server(threaded=True,processes=1)#,port=10450)
    cache.clear()
    
