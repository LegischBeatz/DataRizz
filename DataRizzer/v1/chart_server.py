import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
from yahoo_fin import stock_info as si
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Initialize Flask app
from flask import Flask
server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(__name__, server=server, routes_pathname_prefix='/dash/',
                external_stylesheets=['https://fonts.googleapis.com/css?family=Montserrat:400,700&display=swap',
                                      'https://codepen.io/chriddyp/pen/bWLwgP.css'])

# Functions for stock analysis
def moving_average(data, window):
    return data.rolling(window=window, min_periods=1).mean()

def rsi_calculation(series, period=14):
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ETFs or stocks to analyze
stocks = ['SPY', 'QQQ', 'VTI', 'GLD', 'VWO', 'DFAI', 'DISV', 'DFIS', 'IXUS', 'VEU', 'VSS', 'VIGI', 'VXUS', 'AAPL', 'MSFT', 'GOOGL', 'INTC', 'NVDA', 'TCEHY', 'BAYRY', 'YUMC', 'BABA', 'LYG', 'NTES', 'SWGAY', 'TIGO', 'BMWYY', 'RHHBY', 'MA', 'SHOP', 'AAPL', 'TSLA', 'META', 'DIS', 'ZM', 'ISRG', 'HD', 'PFE', 'EL', 'RCL', 'V']

# Dash layout
app.layout = html.Div([
    html.Div([
        html.Img(src=app.get_asset_url('datarizerlogo.png'), style={'height': '120px', 'width': 'auto', 'margin-top': '5px'}),
    ], style={'textAlign': 'left'}),
    dcc.Dropdown(
        id='stock-selector',
        options=[{'label': etf, 'value': etf} for etf in stocks],
        value=stocks[0],  
        style={'width': '60%', 'marginLeft': '5px', 'fontFamily': 'Montserrat'}
    ),
    dcc.Checklist(
        id='data-series-selector',
        options=[
            {'label': 'Short Moving Average', 'value': 'Short_MAVG'},
            {'label': 'Long Moving Average', 'value': 'Long_MAVG'}
        ],
        value=['Short_MAVG', 'Long_MAVG'],
        labelStyle={'display': 'inline-block', 'fontFamily': 'Montserrat'},
        style={'width': '100%', 'margin': '20px auto', 'fontFamily': 'Montserrat'}
    ),
    dcc.Dropdown(
        id='time-range',
        options=[
            {'label': '1 Year', 'value': 1},
            {'label': '2 Years', 'value': 2},
            {'label': '3 Years', 'value': 3},
            {'label': '4 Years', 'value': 4},
            {'label': '5 Years', 'value': 5}
        ],
        value=1,
        style={'width': '60%', 'marginLeft': '5px', 'marginBottom': '30px', 'fontFamily': 'Montserrat'}
    ),
    dcc.Graph(id='stock-graph', style={'height': '50vh', 'fontFamily': 'Montserrat'}),
    dcc.Graph(id='rsi-graph', style={'height': '20vh', 'fontFamily': 'Montserrat'}),
    html.Div(id='info-panel', style={'margin-top': '20px', 'fontFamily': 'Montserrat', 'border': '2px solid #007BFF', 'borderRadius': '5px', 'padding': '10px', 'backgroundColor': '#E9F5FF'}),
    html.Div(id='recommendation-reason', style={'margin-top': '20px', 'fontFamily': 'Montserrat', 'border': '2px solid #FFC107', 'borderRadius': '5px', 'padding': '10px', 'backgroundColor': '#FFFBEA'})  # New panel for recommendation reason
])

# Callback for updating the graphs, info panel, and recommendation reason
@app.callback(
    [Output('stock-graph', 'figure'),
     Output('rsi-graph', 'figure'),
     Output('info-panel', 'children'),
     Output('recommendation-reason', 'children')],  # Added output for recommendation reason
    [Input('stock-selector', 'value'),
     Input('data-series-selector', 'value'),
     Input('time-range', 'value')])
def update_graph(selected_stock, selected_series, time_range):
    if selected_series is None:
        selected_series = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=time_range*365)
    stock_data = si.get_data(selected_stock, start_date=start_date, end_date=end_date)
    stock_data['Short_MAVG'] = moving_average(stock_data['adjclose'], 50)
    stock_data['Long_MAVG'] = moving_average(stock_data['adjclose'], 200)
    stock_data['RSI'] = rsi_calculation(stock_data['adjclose'])

    # Calculate support and resistance levels
    support_level = stock_data['adjclose'].min()
    resistance_level = stock_data['adjclose'].max()

    # Latest values
    latest_close_price = stock_data['adjclose'].iloc[-1]
    latest_short_mavg = stock_data['Short_MAVG'].iloc[-1]
    latest_rsi = stock_data['RSI'].iloc[-1]

    # Initialize figures
    fig_stock = go.Figure()
    fig_rsi = go.Figure()

    # Add traces with greyscale colors for stock graph
    fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['adjclose'], mode='lines', name='Close Price', line={'color': '#333'}))
    
    if 'Short_MAVG' in selected_series:
        fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Short_MAVG'], mode='lines', name='Short MAVG', line={'color': '#006400'}))
    if 'Long_MAVG' in selected_series:
        fig_stock.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Long_MAVG'], mode='lines', name='Long MAVG', line={'color': '#FF8C00'}))

    # Add RSI trace with intelligent scaling for RSI graph
    fig_rsi.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI', line={'color': '#4169E1'}))

    # Update layout for stock graph
    fig_stock.update_layout(
        title=f'{selected_stock} Stock Data',
        yaxis_title='Price',
        xaxis_title='Date',
        autosize=True,
        margin=dict(l=50, r=50, b=30, t=30, pad=4),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Montserrat', size=12, color='#333'),
    )

    # Update layout for RSI graph
    fig_rsi.update_layout(
        title='RSI',
        yaxis_title='RSI',
        xaxis_title='Date',
        autosize=True,
        margin=dict(l=50, r=50, b=30, t=30, pad=4),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Montserrat', size=12, color='#333'),
    )

    # Recommendation based on RSI
    recommendation, reason = "Hold", "The RSI is within the neutral range (30-70)."
    if latest_rsi < 30:
        recommendation, reason = "Buy", "The RSI is below 30, indicating the stock may be oversold."
    elif latest_rsi > 70:
        recommendation, reason = "Sell", "The RSI is above 70, indicating the stock may be overbought."

    # Info panel content
    info_panel_content = html.Div([
        html.H3('Current Information', style={'color': '#007BFF'}),
        html.Table([
            html.Tr([html.Th('Support Level'), html.Td('${:.2f}'.format(support_level))]),
            html.Tr([html.Th('Resistance Level'), html.Td('${:.2f}'.format(resistance_level))]),
            html.Tr([html.Th('Latest Close Price'), html.Td('${:.2f}'.format(latest_close_price))]),
            html.Tr([html.Th('Latest Short MAVG'), html.Td('${:.2f}'.format(latest_short_mavg))]),
            html.Tr([html.Th('Latest RSI'), html.Td('{:.2f}'.format(latest_rsi))]),
            html.Tr([html.Th('Recommendation', style={'color': '#D9534F', 'fontSize': '20px'}), html.Td(recommendation, style={'color': '#D9534F', 'fontSize': '20px', 'fontWeight': 'bold'})])
        ], style={'marginLeft': '35px', 'margin-top': '10px'})
    ])

    # Recommendation reason content
    recommendation_reason_content = html.Div([
        html.H3('Recommendation Reason', style={'color': '#FFC107'}),
        html.P(reason, style={'fontSize': '16px', 'margin': '10px'})
    ])

    return fig_stock, fig_rsi, info_panel_content, recommendation_reason_content

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
