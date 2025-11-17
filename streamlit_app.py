import streamlit as st
import pandas as pd
import math
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Renegades',
    page_icon=':clown_face:', # This is an emoji shortcode. Could be a URL too.
    layout='wide',
)

@st.cache_data
def load_data(path):
    try:
        p = Path(path)
        # Choose reader based on file extension
        if p.suffix.lower() == '.csv':
            df = pd.read_csv(path)
        elif p.suffix.lower() in ('.xls', '.xlsx'):
            df = pd.read_excel(path, engine='openpyxl')
        else:
            # Fallback: try csv then excel
            try:
                df = pd.read_csv(path)
            except Exception:
                df = pd.read_excel(path, engine='openpyxl')
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{path}' was not found. Please ensure it's in the same directory.")
        return None
    except Exception as e:
        st.error(f"An error occurred while reading the file '{path}': {e}")
        return None

datasets = {
    'Sewers': 'sewers.csv',
    'Contributions': 'contri.csv',
}
st.sidebar.header('Dataset')
selected_dataset_label = st.sidebar.selectbox('Select dataset', list(datasets.keys()), index=0, key='selected_dataset')
file_path = datasets[selected_dataset_label]
df = load_data(file_path)

if df is not None:
    # Clean the data - remove commas from numeric columns
    raw_value_cols = [col for col in df.columns if col != 'IGN']
    for col in raw_value_cols:
        df[col] = df[col].astype(str).str.replace(',', '')
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Rename date columns to add '_total'
    date_columns = [col for col in df.columns if col != 'IGN']
    new_date_columns = [f"{col}_total" for col in date_columns]
    rename_map = dict(zip(date_columns, new_date_columns))
    df = df.rename(columns=rename_map)

    # Add daily delta columns
    for i in range(1, len(new_date_columns)):
        prev_col = new_date_columns[i-1]
        curr_col = new_date_columns[i]
        delta_col = curr_col.replace('_total', '_delta')
        df[delta_col] = df[curr_col] - df[prev_col]

    # Update column lists for filtering and charting
    all_columns = df.columns.tolist()
    date_total_columns = [col for col in all_columns if col.endswith('_total')]
    delta_columns = [col for col in all_columns if col.endswith('_delta')]

    # Sidebar filters
    st.sidebar.header('Filters')
    # Add filter state to session_state for reset functionality
    if 'selected_name' not in st.session_state:
        st.session_state.selected_name = 'All'
    if 'selected_date_label' not in st.session_state:
        # On first load, default to latest date (not 'All')
        date_label_map = {col: col.replace('_total', '') for col in date_total_columns}
        date_options = ['All'] + [date_label_map[col] for col in date_total_columns]
        if date_total_columns:
            st.session_state.selected_date_label = date_label_map[date_total_columns[-1]]
        else:
            st.session_state.selected_date_label = 'All'
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = 'Total'

    def reset_filters():
        st.session_state.selected_name = 'All'
        st.session_state.selected_date_label = 'All'
        st.session_state.view_mode = 'Total'

    st.sidebar.button('Remove All Filters', on_click=reset_filters)

    name_options = sorted(df['IGN'].dropna().unique().tolist())
    selected_names = st.sidebar.multiselect('Select Name(s)', name_options, default=name_options, key='selected_name')
    # Ensure selected_names is always a list for filtering
    if not isinstance(selected_names, list):
        selected_names = [selected_names] if selected_names else []
    # If 'All' is selected or nothing is selected, use all names
    if not selected_names or selected_names == ['All'] or set(selected_names) == set(name_options):
        selected_names = name_options
    # Clean date options for multiselect (remove _total)
    date_label_map = {col: col.replace('_total', '') for col in date_total_columns}
    date_options = [date_label_map[col] for col in date_total_columns]
    selected_date_labels = st.sidebar.multiselect('Select Date(s)', date_options, default=[date_options[-1]], key='selected_date_label')
    # Map back to the actual column names
    if not selected_date_labels or set(selected_date_labels) == set(date_options):
        selected_dates = date_total_columns
    else:
        selected_dates = [col for col, label in date_label_map.items() if label in selected_date_labels]
    view_mode = st.sidebar.radio('Show', options=['Total', 'Delta'], index=0, key='view_mode')

    # Filter by name
    filtered_df = df.copy()
    if selected_names:
        filtered_df = filtered_df[filtered_df['IGN'].isin(selected_names)]

    # Choose columns for chart and table based on toggle
    if view_mode == 'Total':
        chart_cols = date_total_columns
    else:
        chart_cols = delta_columns
    # If delta view requested but no delta columns exist (e.g., Sewers), fall back
    delta_available = True
    if view_mode == 'Delta' and not chart_cols:
        delta_available = False
        st.warning('Delta view is not available for this dataset. Showing totals instead.')
        chart_cols = date_total_columns

    # Filter by date (for chart and table)
    # --- Contribution Metrics ---
    def show_contribution_metrics(df, date_cols, selected_dates):
        import numpy as np
        if not selected_dates or set(selected_dates) == set(date_cols):
            cols = date_cols
            label = 'All Dates (avg)'
        else:
            cols = selected_dates
            label = ', '.join([c.replace('_total','').replace('_delta','') for c in cols])
        total_people = len(df)
        if total_people == 0:
            st.info('No data to calculate metrics.')
            return
        pct_10k = []
        pct_gt0 = []
        count_10k = []
        count_gt0 = []
        for col in cols:
            s = df[col]
            n_10k = (s >= 10000).sum()
            n_gt0 = (s > 0).sum()
            pct_10k.append(n_10k / total_people * 100)
            pct_gt0.append(n_gt0 / total_people * 100)
            count_10k.append(n_10k)
            count_gt0.append(n_gt0)
        # If multiple dates, show average
        st.write('### Contribution Metrics')
        if len(cols) > 1:
            st.metric('Contributed 10k', f"{np.mean(pct_10k):.1f}% ({int(np.mean(count_10k))}/{total_people})")
            st.metric('Contributed >0', f"{np.mean(pct_gt0):.1f}% ({int(np.mean(count_gt0))}/{total_people})")
        else:
            st.metric('Contributed 10k', f"{pct_10k[0]:.1f}% ({count_10k[0]}/{total_people})")
            st.metric('Contributed >0', f"{pct_gt0[0]:.1f}% ({count_gt0[0]}/{total_people})")

    # Show date description above metrics
    if not selected_dates or set(selected_dates) == set(date_total_columns):
        date_desc = 'All Dates'
    else:
        date_desc = ', '.join([c.replace('_total','').replace('_delta','') for c in selected_dates])
    st.write(f"### Showing data for: {date_desc}")

    # Show metrics above chart/table (skip Contribution Metrics for Sewers)
    if selected_dataset_label != 'Sewers':
        if view_mode == 'Total':
            metric_cols = date_total_columns
        else:
            metric_cols = delta_columns

        # For delta view, always show only the selected date's values
        if view_mode == 'Delta' and selected_dates:
            show_contribution_metrics(filtered_df, metric_cols, selected_dates)
        # If showing all dates, use only the latest date for metrics
        elif not selected_dates or set(selected_dates) == set(metric_cols):
            latest_col = metric_cols[-1]  # Last column is the latest
            show_contribution_metrics(filtered_df, [latest_col], [latest_col])
        elif selected_dates:
            show_contribution_metrics(filtered_df, metric_cols, selected_dates)

    # If Sewers dataset and a single name is selected, show highest across all time
    if selected_dataset_label == 'Sewers' and selected_names and len(selected_names) == 1:
        selected_name = selected_names[0]
        try:
            # filtered_df should be already filtered to the selected name
            if len(filtered_df) > 0:
                # compute max across all total columns and find which date it occurred
                max_per_row = filtered_df[date_total_columns].max(axis=1)
                highest = max_per_row.max()
                if pd.notna(highest):
                    # Find which date column has the highest value
                    highest_col = filtered_df[date_total_columns].idxmax(axis=1).iloc[0]
                    date_label = highest_col.replace('_total', '')
                    st.metric('Highest (all time)', f"{int(highest):,}", delta=f"on {date_label}")
        except Exception:
            # don't break the app if something unexpected happens
            pass

    if selected_dates:
        # Show only the selected date columns and their deltas if available
        if view_mode == 'Total':
            # Always show the latest date on top in the stacked bar chart
            sorted_selected_dates = sorted(selected_dates, key=lambda x: date_total_columns.index(x) if x in date_total_columns else -1, reverse=True)
            cols_to_show = ['IGN'] + sorted_selected_dates
            chart_data = filtered_df.set_index('IGN')[sorted_selected_dates]
        else:
            delta_cols = [d.replace('_total', '_delta') for d in selected_dates]
            # Sort delta columns to match the order of selected_dates (latest first)
            sorted_delta_cols = [c for _, c in sorted(zip(selected_dates, delta_cols), key=lambda pair: date_total_columns.index(pair[0]) if pair[0] in date_total_columns else -1, reverse=True)]
            cols_to_show = ['IGN'] + [c for c in sorted_delta_cols if c in filtered_df.columns]
            chart_data = filtered_df.set_index('IGN')[cols_to_show[1:]] if len(cols_to_show) > 1 else None
        st.write(f"## Contribution on {', '.join([d.replace('_total','').replace('_delta','') for d in selected_dates])}")
        if chart_data is not None and not chart_data.empty:
            st.bar_chart(chart_data, use_container_width=True)
        # Sort by first date in cols_to_show descending for Sewers (exclude nulls)
        display_df = filtered_df[cols_to_show].copy()
        if selected_dataset_label == 'Sewers' and len(cols_to_show) > 1:
            sort_col = cols_to_show[1]  # First date column after IGN
            if sort_col in display_df.columns:
                display_df = display_df[display_df[sort_col].notna()]
                display_df = display_df.sort_values(by=sort_col, ascending=False)
        st.dataframe(display_df, use_container_width=True, height=600)
    else:
        # Show all dates (line chart)
        st.write(f"## {'Total' if view_mode == 'Total' else 'Daily'} Trends Over Time")
        chart_data = filtered_df.set_index('IGN')[chart_cols].T
        st.line_chart(chart_data, use_container_width=True)
        # Sort by latest date descending for Sewers (exclude nulls)
        display_df = filtered_df[['IGN'] + chart_cols].copy()
        if selected_dataset_label == 'Sewers':
            latest_col = chart_cols[-1]
            display_df = display_df[display_df[latest_col].notna()]
            display_df = display_df.sort_values(by=latest_col, ascending=False)
        st.dataframe(display_df, use_container_width=True, height=600)