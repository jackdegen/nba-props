import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def prop_ratio(df_, **kwargs):
    """
    Create a single, pretty pie chart showing distribution of 'no-props' column.
    Returns the figure without displaying it to prevent duplication.
    """
    df = df_.copy(deep=True)
    # Set a more aesthetically pleasing style
    plt.style.use('ggplot')
    sns.set_palette("pastel")
    
    # Create figure with a specific size
    fig, ax = plt.subplots(figsize=(kwargs.get('figsize', (5, 3))))

    df['no_props'] = df.props.map(lambda prop_: 1 if prop_ == '---' else 0)
    
    # Get the value counts
    counts = df.loc[df['fpts'] >= kwargs.get('cutoff', kwargs.get('cap', 0.0))].no_props.value_counts().sort_index()

    if df.loc[df.no_props == 1].empty:


        # Create pie chart with improved aesthetics
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=['Props'],   # Custom labels (assuming 0=Props Used, 1=No Props)
            autopct='%1.1f%%',                   # Add percentage labels
            startangle=90,                       # Start from top
            shadow=True,                         # Add shadow effect
            explode=(0.05, 0),                   # Slightly explode the first slice
            # colors=['#5DA5DA', '#FAA43A'],       # Custom colors - blue and orange
            colors=["#2ecc71"], # Emerald green
            textprops={'fontsize': 14}           # Larger font size
        )
        
        # Make the percentage labels more readable
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            
        # Add a title with styling
        ax.set_title('Distribution of Lineups with Props vs No Props', 
                     fontsize=16, 
                     fontweight='bold', 
                     pad=20)
        
        # Add count information as a subtitle
        plt.figtext(0.5, 0.01, f'Total Entries: {counts.sum()} ({counts.iloc[0]} Props, 0 No Props)', 
                    ha='center', 
                    fontsize=12)
        
        # Equal aspect ratio ensures pie is circular
        ax.set_aspect('equal')
        
        plt.tight_layout()
        
        # Return the figure without calling plt.show()
        return fig
        
        

    # Create pie chart with improved aesthetics
    wedges, texts, autotexts = ax.pie(
        counts, 
        labels=['Props', 'No Props'],   # Custom labels (assuming 0=Props Used, 1=No Props)
        autopct='%1.1f%%',                   # Add percentage labels
        startangle=90,                       # Start from top
        shadow=True,                         # Add shadow effect
        explode=(0.05, 0),                   # Slightly explode the first slice
        # colors=['#5DA5DA', '#FAA43A'],       # Custom colors - blue and orange
        colors=["#2ecc71", "#FF0800"], # Emerald Green + Candy Apple Red
        textprops={'fontsize': 14}           # Larger font size
    )
    
    # Make the percentage labels more readable
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        
    # Add a title with styling
    ax.set_title('Distribution of Lineups with Props vs No Props', 
                 fontsize=16, 
                 fontweight='bold', 
                 pad=20)
    
    # Add count information as a subtitle
    plt.figtext(0.5, 0.01, f'Total Entries: {counts.sum()} ({counts.iloc[0]} Props, {counts.iloc[1]} No Props)', 
                ha='center', 
                fontsize=12)
    
    # Equal aspect ratio ensures pie is circular
    ax.set_aspect('equal')
    
    plt.tight_layout()
    
    # Return the figure without calling plt.show()
    return fig