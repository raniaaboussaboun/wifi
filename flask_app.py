import requests
import speedtest
import pandas as pd
from datetime import datetime
from dash import Dash, dcc, html
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    response.raise_for_status()
    return response.json()['ip']

def get_isp_info(ip):
    response = requests.get(f'https://ipinfo.io/{ip}/json')
    response.raise_for_status()
    return response.json()

def is_starlink(isp_info):
    known_starlink_asn = "AS14593"
    known_starlink_org = "Space Exploration Technologies Corp"
    return isp_info.get('org') == known_starlink_org or isp_info.get('asn') == known_starlink_asn

def get_internet_speed():
    try:
        st = speedtest.Speedtest()
        st.download()
        st.upload()
        results = st.results.dict()
        return {
            "Download Speed (Mbps)": results["download"] / 1_000_000,
            "Upload Speed (Mbps)": results["upload"] / 1_000_000,
            "Ping (ms)": results["ping"]
        }
    except speedtest.ConfigRetrievalError as e:
        return {
            "Download Speed (Mbps)": "Error",
            "Upload Speed (Mbps)": "Error",
            "Ping (ms)": "Error"
        }

def get_internet_details():
    ip = get_public_ip()
    isp_info = get_isp_info(ip)
    
    loc = isp_info.get('loc', 'Unknown,Unknown').split(',')
    
    speed_info = get_internet_speed()
    
    details = {
        "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "IP Address": ip,
        "ISP": isp_info.get('org', 'Unknown'),
        "City": isp_info.get('city', 'Unknown'),
        "Region": isp_info.get('region', 'Unknown'),
        "Country": isp_info.get('country', 'Unknown'),
        "Latitude": loc[0] if len(loc) > 1 else 'Unknown',
        "Longitude": loc[1] if len(loc) > 1 else 'Unknown',
        "Network Type": "Starlink" if is_starlink(isp_info) else isp_info.get('org', 'Unknown'),
        "Download Speed (Mbps)": speed_info["Download Speed (Mbps)"],
        "Upload Speed (Mbps)": speed_info["Upload Speed (Mbps)"],
        "Ping (ms)": speed_info["Ping (ms)"]
    }
    return details

def save_to_csv(details):
    fieldnames = ["Timestamp", "IP Address", "ISP", "City", "Region", "Country", "Latitude", "Longitude", "Network Type", "Download Speed (Mbps)", "Upload Speed (Mbps)", "Ping (ms)"]
    try:
        df = pd.read_csv('internet_info.csv')
        new_row = pd.DataFrame([details])
        df = pd.concat([df, new_row], ignore_index=True)
    except FileNotFoundError:
        df = pd.DataFrame([details], columns=fieldnames)
    
    df.to_csv('internet_info.csv', index=False)

def load_data():
    try:
        df = pd.read_csv('internet_info.csv')
    except FileNotFoundError:
        df = pd.DataFrame(columns=["Timestamp", "IP Address", "ISP", "City", "Region", "Country", "Latitude", "Longitude", "Network Type", "Download Speed (Mbps)", "Upload Speed (Mbps)", "Ping (ms)"])
    return df

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Internet Speed Dashboard", className="text-center"), className="mb-5 mt-5")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Button("Refresh Internet Details", id="refresh-button", color="primary", className="mb-4"),
            html.Div(id="details", children=[])
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="speed-graph")
        ], width=12)
    ]),
    dcc.Interval(
        id='interval-component',
        interval=1*60*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(
    [Output('details', 'children'),
     Output('speed-graph', 'figure')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard(n_clicks, n_intervals):
    details = get_internet_details()
    save_to_csv(details)
    
    df = load_data()
    
    details_display = [
        html.P(f"Timestamp: {details['Timestamp']}"),
        html.P(f"IP Address: {details['IP Address']}"),
        html.P(f"ISP: {details['ISP']}"),
        html.P(f"City: {details['City']}"),
        html.P(f"Region: {details['Region']}"),
        html.P(f"Country: {details['Country']}"),
        html.P(f"Latitude: {details['Latitude']}"),
        html.P(f"Longitude: {details['Longitude']}"),
        html.P(f"Network Type: {details['Network Type']}"),
        html.P(f"Download Speed (Mbps): {details['Download Speed (Mbps)']}"),
        html.P(f"Upload Speed (Mbps): {details['Upload Speed (Mbps)']}"),
        html.P(f"Ping (ms): {details['Ping (ms)']}")
    ]
    
    speed_fig = px.line(df, x='Timestamp', y=['Download Speed (Mbps)', 'Upload Speed (Mbps)', 'Ping (ms)'], title='Internet Speeds Over Time')
    
    return details_display, speed_fig

if __name__ == '__main__':
    app.run_server(debug=True)
