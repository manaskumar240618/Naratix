import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

def analyze_data(df):
    """
    Perform basic analysis on the dataframe
    """
    results = {}
    
    # Basic info
    results['row_count'] = len(df)
    results['column_count'] = len(df.columns)
    
    # Data types
    results['data_types'] = {col: str(dtype) for col, dtype in df.dtypes.items()}
    
    # Missing values
    results['missing_values'] = {col: int(df[col].isna().sum()) for col in df.columns}
    results['missing_percentage'] = {col: float(df[col].isna().sum() / len(df) * 100) for col in df.columns}
    
    # Summary statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        results['numeric_summary'] = json.loads(df[numeric_cols].describe().to_json())
    
    # Categorical data summary
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    results['categorical_summary'] = {}
    for col in categorical_cols:
        if len(df[col].unique()) <= 20:  # Only for columns with reasonable number of categories
            value_counts = df[col].value_counts().head(10)
            results['categorical_summary'][col] = {
                'unique_values': int(len(df[col].unique())),
                'top_values': {str(k): int(v) for k, v in value_counts.items()}
            }
    
    # Correlation matrix for numeric data
    if len(numeric_cols) > 1:
        results['correlation'] = json.loads(df[numeric_cols].corr().to_json())
    
    return results

def generate_graphs(df):
    """
    Generate a set of standard graphs based on dataframe content
    Returns plotly graph objects as JSON
    """
    graphs = {}
    
    # Identify numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # 1. Missing values visualization
    missing_data = pd.DataFrame({
        'column': df.columns,
        'percent_missing': [df[col].isna().mean() * 100 for col in df.columns]
    })
    if missing_data['percent_missing'].sum() > 0:
        fig = px.bar(missing_data, x='column', y='percent_missing',
                    title='Percentage of Missing Values by Column',
                    labels={'percent_missing': 'Missing Values (%)', 'column': 'Column'})
        graphs['missing_values'] = fig.to_json()
    
    # 2. Distribution of numeric columns (first 5)
    for i, col in enumerate(numeric_cols[:5]):
        fig = px.histogram(df, x=col, title=f'Distribution of {col}',
                         labels={col: col})
        graphs[f'dist_{col}'] = fig.to_json()
    
    # 3. Boxplots for numeric columns (first 5)
    if len(numeric_cols) >= 2:
        fig = px.box(df, y=numeric_cols[:5], title='Box Plots of Numeric Columns')
        graphs['boxplots'] = fig.to_json()
    
    # 4. Scatter plot of first two numeric columns
    if len(numeric_cols) >= 2:
        fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1],
                       title=f'Scatter Plot: {numeric_cols[0]} vs {numeric_cols[1]}',
                       labels={numeric_cols[0]: numeric_cols[0], numeric_cols[1]: numeric_cols[1]})
        graphs['scatter'] = fig.to_json()
    
    # 5. Bar chart for categorical columns (first one, top 10 values)
    if categorical_cols:
        col = categorical_cols[0]
        top_values = df[col].value_counts().head(10)
        fig = px.bar(x=top_values.index, y=top_values.values,
                   title=f'Top 10 values in {col}',
                   labels={'x': col, 'y': 'Count'})
        graphs[f'bar_{col}'] = fig.to_json()
    
    # 6. Correlation heatmap for numeric columns
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        fig = px.imshow(corr, text_auto=True, aspect="auto",
                      title='Correlation Matrix',
                      labels=dict(x="Features", y="Features", color="Correlation"))
        graphs['correlation'] = fig.to_json()
    
    return graphs

def generate_custom_graph(df, graph_type, x_column, y_column):
    """
    Generate a custom graph based on user selection
    """
    if graph_type == 'bar':
        fig = px.bar(df, x=x_column, y=y_column, title=f'Bar Chart: {y_column} by {x_column}')
    elif graph_type == 'line':
        fig = px.line(df, x=x_column, y=y_column, title=f'Line Chart: {y_column} by {x_column}')
    elif graph_type == 'scatter':
        fig = px.scatter(df, x=x_column, y=y_column, title=f'Scatter Plot: {y_column} vs {x_column}')
    elif graph_type == 'box':
        fig = px.box(df, x=x_column, y=y_column, title=f'Box Plot: {y_column} by {x_column}')
    elif graph_type == 'histogram':
        fig = px.histogram(df, x=x_column, title=f'Histogram of {x_column}')
    elif graph_type == 'pie':
        # For pie charts, we need to aggregate the data
        count_data = df.groupby(x_column)[y_column].sum().reset_index()
        fig = px.pie(count_data, values=y_column, names=x_column, title=f'Pie Chart: {y_column} by {x_column}')
    else:
        raise ValueError(f"Unsupported graph type: {graph_type}")
    
    return fig.to_json()