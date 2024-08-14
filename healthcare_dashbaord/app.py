# Import necessary libraries
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

def load_data():
    # Load and preprocess the data
    df = pd.read_csv('assets/healthcare.csv')
    df['Billing Amount'] = pd.to_numeric(df['Billing Amount'], errors='coerce')
    df['Date of Admission'] = pd.to_datetime(df['Date of Admission'])
    df['YearMonth'] = df['Date of Admission'].dt.to_period('M')  # Aggregating by month
    return df

df = load_data()

# Calculate summary statistics
num_records = len(df)
avg_billing = df['Billing Amount'].mean()

# Initialize the Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, '/assets/styles.css'])

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Healthcare Dashboard"), width=12, className="text-center my-4")
    ]),

    # Summary Statistics
    dbc.Row([
        dbc.Col(html.Div(f"Total Patient Records: {num_records}", className='text-center my-2 top-text'), width=5),
        dbc.Col(html.Div(f"Average Billing Amount: ${avg_billing:,.2f}", className='text-center my-2 top-text'), width=5),
    ], className='mb-4'),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Patient Demographics", className="card-title"),
                    dcc.Dropdown(
                        id="gender-filter",
                        options=[{"label": gender, "value": gender} for gender in df['Gender'].unique()],
                        value=None,
                        placeholder="Select Gender"
                    ),
                    dcc.Graph(id="age-distribution")
                ])
            ])
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Medical Condition Distribution", className="card-title"),
                    dcc.Graph(id="condition-distribution")
                ])
            ])
        ], width=6),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Insurance Provider Comparison", className="card-title"),
                    dcc.Graph(id="insurance-comparison")
                ])
            ])
        ], width=12),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Billing Amount Distribution", className="card-title"),
                    dcc.Slider(
                        id='billing-slider',
                        min=df['Billing Amount'].min(),
                        max=df['Billing Amount'].max(),
                        value=df['Billing Amount'].max(),
                        marks={int(value): f'${int(value):,}' for value in df['Billing Amount'].quantile([0, 0.25, 0.5, 0.75, 1]).values},
                        step=100
                    ),
                    dcc.Graph(id="billing-distribution")
                ])
            ])
        ], width=12),
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Admission Trends", className="card-title"),
                    dcc.RadioItems(
                        id='chart-type',
                        options=[{'label': 'Line Chart', 'value': 'line'}, {'label': 'Bar Chart', 'value': 'bar'}],
                        value='line',
                        inline=True,
                        className='mb-3'
                    ),
                    dcc.Dropdown(
                        id="condition-filter",
                        options=[{"label": condition, "value": condition} for condition in df['Medical Condition'].unique()],
                        value=None,
                        placeholder="Select Medical Condition"
                    ),
                    dcc.Graph(id="admission-trends")
                ])
            ])
        ], width=12),
    ]),
], fluid=True)


# Callbacks for interactivity

@app.callback(
    Output('age-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_age_distribution(selected_gender):
    # Filter the dataframe based on the selected gender
    if selected_gender:
        filtered_df = df[df['Gender'] == selected_gender]
    else:
        filtered_df = df

    # Check if the filtered dataframe is not empty
    if filtered_df.empty:
        return {}

    # Create the histogram
    fig = px.histogram(
        filtered_df, 
        x="Age", 
        nbins=10, 
        color="Gender", 
        title="Age Distribution by Gender",
        color_discrete_sequence=["#636EFA", "#EF553B"]
    )

    return fig


@app.callback(
    Output('condition-distribution', 'figure'),
    Input('gender-filter', 'value')
)
def update_condition_distribution(selected_gender):
    filtered_df = df[df['Gender'] == selected_gender] if selected_gender else df
    fig = px.pie(filtered_df, names="Medical Condition", title="Medical Condition Distribution")
    return fig


@app.callback(
    Output('admission-trends', 'figure'),
    [Input('chart-type', 'value'),
     Input('condition-filter', 'value')]
)
def update_admission_trends(chart_type, selected_condition):
    filtered_df = df[df['Medical Condition'] == selected_condition] if selected_condition else df
    
    # Group by YearMonth and convert to string
    trend_df = filtered_df.groupby('YearMonth').size().reset_index(name='Count')
    trend_df['YearMonth'] = trend_df['YearMonth'].astype(str)  # Convert to string

    if chart_type == 'line':
        fig = px.line(trend_df, x='YearMonth', y='Count', title="Admission Trends Over Time")
    else:
        fig = px.bar(trend_df, x='YearMonth', y='Count', title="Admission Trends Over Time")
    
    return fig


@app.callback(
    Output('billing-distribution', 'figure'),
    [Input('gender-filter', 'value'),
     Input('billing-slider', 'value')]
)
def update_billing_distribution(selected_gender, slider_value):
    filtered_df = df[df['Gender'] == selected_gender] if selected_gender else df
    filtered_df = filtered_df[filtered_df['Billing Amount'] <= slider_value]
    fig = px.histogram(filtered_df, x="Billing Amount", nbins=10, title="Billing Amount Distribution")
    return fig


@app.callback(
    Output('insurance-comparison', 'figure'),
    Input('gender-filter', 'value')
)
def update_insurance_comparison(selected_gender):
    filtered_df = df[df['Gender'] == selected_gender] if selected_gender else df
    fig = px.bar(
        filtered_df, x="Insurance Provider", y="Billing Amount", color="Medical Condition", barmode="group",
        title="Insurance Provider Billing Comparison",
        color_discrete_sequence=px.colors.qualitative.Set2  # Use a different basic color palette
    )
    return fig


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
