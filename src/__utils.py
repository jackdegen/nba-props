import matplotlib.pyplot as plt
import seaborn as sns

BLUE_COLORS = {
    "medium_blue": "#3498db",
    "deep_blue": "#2980b9", 
    "sky_blue": "#5DA5DA",
    "steel_blue": "#4682B4",
    "deep_sky_blue": "#00BFFF"
}

GOLD_COLORS = {
    "classic_gold": "#FFD700",
    "vegas_gold": "#C5B358",
    "old_gold": "#CFB53B",
    "metallic_gold": "#D4AF37",
    "amber_gold": "#FFBF00",
    "golden_yellow": "#FFDF00",
    "satin_gold": "#CBA135",
    "golden_brown": "#996515"
}

GREEN_COLORS = {
    "emerald_green": "#2ecc71",
    "forest_green": "#228B22",
    "mint_green": "#98FB98",
    "lime_green": "#32CD32",
    "sage_green": "#8A9A5B",
    "olive_green": "#556B2F",
    "sea_green": "#2E8B57",
    "teal_green": "#008080",
    "jade_green": "#00A86B",
    "hunter_green": "#355E3B"
}

RED_COLORS = {
    "crimson": "#DC143C",
    "ruby_red": "#E0115F",
    "candy_apple": "#FF0800",
    "fire_engine": "#CE2029",
    "scarlet": "#FF2400",
    "dark_red": "#8B0000",
    "brick_red": "#CB4154",
    "burgundy": "#800020",
    "cardinal_red": "#C41E3A",
    "vermilion": "#E34234"
}

def visualize_prop_ratio(df, **kwargs):
    """
    Create a single, pretty pie chart showing distribution of 'no-props' column.
    Returns the figure without displaying it to prevent duplication.
    """
    # Set a more aesthetically pleasing style
    plt.style.use('ggplot')
    sns.set_palette("pastel")
    
    # Create figure with a specific size
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Get the value counts
    counts = df.loc[df['fpts'] >= kwargs.get('cutoff', kwargs.get('cap', 0.0)), 'no-props'].value_counts().sort_index()

    # Create pie chart with improved aesthetics
    wedges, texts, autotexts = ax.pie(
        counts, 
        labels=['Props', 'No Props'],   # Custom labels (assuming 0=Props Used, 1=No Props)
        autopct='%1.1f%%',                   # Add percentage labels
        startangle=90,                       # Start from top
        shadow=True,                         # Add shadow effect
        explode=(0.05, 0),                   # Slightly explode the first slice
        # colors=['#5DA5DA', '#FAA43A'],       # Custom colors - blue and orange
        colors=[GREEN_COLORS['emerald_green'], RED_COLORS['candy_apple']],
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

# Usage:
# fig = plot_props_pie_chart(df)
# fig.savefig('props_distribution.png')  # Optional: save to file
# plt.close(fig)  # Close the figure to prevent it from displaying twice

# When using in a notebook or interactive environment, use this:
# fig = plot_props_pie_chart(df)
# display(fig)  # Only display once



