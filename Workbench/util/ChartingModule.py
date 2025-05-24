import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Optional

def sns_plot_chart(
        df: pd.DataFrame,
        fields: List[str],
        title: str = "Chart",
        x_label: str = "x",
        y_label: str = "y",
        set_benchmark: bool = False,
        benchmark: float = 0,
        secondary_y: Optional[List[str]] = None,
        benchmark_color: str = "red",
        benchmark_style: str = "-",
        benchmark_label: str = "Benchmark",
        save_path: Optional[str] = None,
        show_in_browser: bool = False,
        marker_columns: Optional[List[str]] = None,
):

    secondary_y = secondary_y or []
    marker_columns = marker_columns or []

    # Initialize the figure and axes
    fig, ax1 = plt.subplots(figsize=(36, 18))
    ax2 = ax1.twinx() if secondary_y else None

    # Helper function to plot on the appropriate axis
    def plot_field(field, axis, color=None):
        sns.lineplot(x=df.index, y=df[field], label=field, ax=axis, color=color)

    # Helper function to plot markers
    def plot_markers(column, axis):
        marker_data = df[df[column] == True]
        axis.scatter(marker_data.index, marker_data[fields[0]], marker='^', label=f'{column} marker')

    # Plot fields on the primary or secondary axis
    palette = sns.color_palette("tab10", len(fields))  # Dynamically generate colors
    for i, field in enumerate(fields):
        if field in secondary_y and ax2:
            plot_field(field, ax2, color=palette[i])
        else:
            plot_field(field, ax1, color=palette[i])

    # Plot markers if specified
    for marker_column in marker_columns:
        plot_markers(marker_column, ax1)

    # Add benchmark line if required
    if set_benchmark:
        ax1.axhline(
            y=benchmark,
            color=benchmark_color,
            linestyle=benchmark_style,
            label=benchmark_label,
        )

    # Set titles and labels
    ax1.set_title(title)
    ax1.set_xlabel(x_label)
    ax1.set_ylabel(y_label)
    if ax2:
        ax2.set_ylabel(f"Secondary {y_label}")

    # Add legends
    if ax1.get_legend_handles_labels()[0]:  # Only add legend if there are labels
        ax1.legend(loc="upper left")
    if ax2 and ax2.get_legend_handles_labels()[0]:
        ax2.legend(loc="upper right")

    # Add gridlines
    ax1.grid()

    # Adjust layout to prevent label/title overlap
    plt.tight_layout()

    # Save the plot if a save path is specified
    if save_path:
        plt.savefig(save_path)
        print(f"Plot saved to {save_path}")

    # Show the plot
    if show_in_browser:
        from IPython.display import display
        import mpld3
        display(mpld3.display(fig))
    else:
        plt.show()

def plot_x_y(
        x,
        y ,
        title: str = "Chart",
        x_label: str = "x",
        y_label: str = "y",
        set_benchmark: bool = False,
        benchmark: float = 0,
        secondary_y: Optional[List[str]] = None,
        benchmark_color: str = "red",
        benchmark_style: str = "-",
        benchmark_label: str = "Benchmark",
        save_path: Optional[str] = None,
        show_in_browser: bool = False,
):
    # Create a DataFrame from x and y
    df = pd.DataFrame({'x': x, 'y': y})
    df.set_index('x', inplace=True)
    df =df.drop(columns=['x'], inplace=True, errors='ignore')
    # Call sns_plot_chart with the prepared DataFrame
    sns_plot_chart(
        df=df,
        fields=['y'],
        title=title,
        x_label=x_label,
        y_label=y_label,
        set_benchmark=set_benchmark,
        benchmark=benchmark,
        secondary_y=secondary_y,
        benchmark_color=benchmark_color,
        benchmark_style=benchmark_style,
        benchmark_label=benchmark_label,
        save_path=save_path,
        show_in_browser=show_in_browser
    )