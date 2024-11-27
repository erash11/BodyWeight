import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# Load the dataset
file_path = r"C:\Users\Eric_Rash\OneDrive - Baylor University\AppliedPerformancProjects\CodingProjects\PythonScripts\New Repo\BodyWeightMaster.csv"
data = pd.read_csv(file_path)

# Convert the DATE column to datetime format
data['DATE'] = pd.to_datetime(data['DATE'])

# Extract date from the DATE column
data['Date'] = data['DATE'].dt.date

# Add YearMonth column
data['YearMonth'] = data['DATE'].dt.to_period('M')

# Create Dash app
app = dash.Dash(__name__)
server = app.server

app.config.suppress_callback_exceptions = True # Allow for dynamic callback components

app.layout = html.Div([
    html.H1("Body Weight Trends Over Time"),
    html.Label("Select Mode:"),
    dcc.RadioItems(
        id='mode-radio',
        options=[
            {'label': 'Individual', 'value': 'Individual'}, 
            {'label': 'Position', 'value': 'Position'}
        ],
        value='Individual',
        labelStyle={'display': 'inline-block'}
    ),
    html.Div(id='dynamic-dropdown-div'),
    html.Div(id='dropdown-value', style={'display': 'none'}),
    dcc.Graph(id='weight-graph', figure=go.Figure()) # Initialize with an empty figure
])

@app.callback(
    Output('dynamic-dropdown-div', 'children'),
    [Input('mode-radio', 'value')]
)
def update_dropdown(selected_mode):
    if selected_mode == 'Individual':
        return html.Div([
            html.Label("Select Individual:"),
            dcc.Dropdown(
                id='dynamic-dropdown',
                options=[{'label': str(name), 'value': str(name)} for name in sorted(data['NAME'].astype(str).unique())] + [{'label': 'All Individuals', 'value': 'All Individuals'}],
                value='All Individuals',  # Default value to the first name
                searchable=True
            )
        ])
    else:
        return html.Div([
            html.Label("Select Position:"),
            dcc.Dropdown(
                id='dynamic-dropdown',
                options=[{'label': str(name), 'value': str(name)} for name in sorted(data['POS'].astype(str).unique())] + [{'label': 'All Positions', 'value': 'All Positions'}],
                value='All Positions',  # Default value 
                searchable=True
            )
        ])
    
@app.callback(
    Output('dropdown-value','children'),
    [Input('dynamic-dropdown','value')]
)
def update_dropdown_value(selected_value):
    return selected_value

@app.callback(
    Output('weight-graph', 'figure'),
    [Input('mode-radio', 'value'), 
     Input('dropdown-value', 'children')]
)
def update_graph(mode, selected_value):
    if selected_value is None:
        return go.Figure() # Return an empty figure if no value is selected
    
    if mode == 'Individual':
        if selected_value == 'All Individuals':
            ind_data = data.copy()
        else:
            ind_data = data[data['NAME'] == selected_value] #if selected_individual != 'All Individuals' else data.copy()
    else:
        if selected_value == 'All Positions':
            ind_data = data.copy()
        else:
            ind_data = data[data['POS'] == selected_value] #if selected_value != 'All Positions' else data.copy()
        
    # Calculate average weight for each day
    avg_weight_by_day = ind_data.groupby(['Date'])['WEIGHT'].mean().reset_index()

    # Calculate average weight for each month
    avg_weight_by_month = ind_data.groupby(['YearMonth'])['WEIGHT'].mean().reset_index()

    # Convert YearMonth back to datetime for plotting
    avg_weight_by_month['YearMonth'] = avg_weight_by_month['YearMonth'].dt.to_timestamp()

    # Create the figure
    fig = go.Figure()

    # Plot the average weight for each day with breaks at the end of each month
    for i, month in enumerate(avg_weight_by_month['YearMonth']):
        if i < len(avg_weight_by_month['YearMonth']) - 1:
            mask = (pd.to_datetime(avg_weight_by_day['Date']) >= month) & (pd.to_datetime(avg_weight_by_day['Date']) < avg_weight_by_month['YearMonth'][i + 1])
        else:
            mask = pd.to_datetime(avg_weight_by_day['Date']) >= month
        
        monthly_data = avg_weight_by_day.loc[mask]
        fig.add_trace(go.Scatter(x=monthly_data['Date'], y=monthly_data['WEIGHT'],
                                 mode='lines+markers', name='Daily Avg Weight', line=dict(color='rgba(0,128,128,0.15)'), showlegend=False))

    # Plot the average weight for each month as separate segments with data labels
    for date, weight in zip(avg_weight_by_month['YearMonth'], avg_weight_by_month['WEIGHT']):
        fig.add_trace(go.Scatter(x=[date, date + pd.DateOffset(days=30)], y=[weight, weight],
                                 mode='lines+text', line=dict(color='navy', width=2), 
                                 name='Monthly Avg Weight',
                                 text=[None, f'{weight:.1f}'],  # Add data labels
                                 textposition='top center',  # Position the text
                                 textfont=dict(color='darkred', family='Arial', size=12)  # Set the color, font, and size of the text
                                ))
    
    # Update the layout to list each individual month on the x-axis
    #title = f'Body Weight per Month for {selected_value}' if mode == 'Individual' else f'Body Weight per Month for {selected_value}'
    
    title = f'Body Weight per Month for {selected_value}'

    fig.update_layout(
        title=title, #f'Body Weight per Month for {selected_value} in {selected_value}',
        xaxis_title='Date',
        yaxis_title='Weight (lbs)',
        xaxis=dict(
            tickmode='array',
            tickvals=avg_weight_by_month['YearMonth'],
            ticktext=avg_weight_by_month['YearMonth'].dt.strftime('%b %y'),
            tickangle=-45  # Rotate the x-axis labels by 45 degrees
        ),
        legend_title_text='',
        legend=dict(
            x=0.01,
            y=0.99,
            traceorder='normal',
            bgcolor='rgba(0,0,0,0)',
            bordercolor='rgba(0,0,0,0)'
        ),
        showlegend=False
    )

    return fig

if __name__ == '__main__':
    #app.run_server(debug=True, host='0.0.0.0')
    app.run_server(debug=True, host='127.0.0.1')
