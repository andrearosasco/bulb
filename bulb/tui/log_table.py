import copy
import json
from pathlib import Path
from typing import Callable, List
import pandas as pd
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Input, Static
from textual import on
from textual.reactive import var
from textual.widgets import DataTable, Footer, Header, Input, Label, Select, Button, TabbedContent, TabPane
from textual.widget import Widget
from textual.containers import Horizontal, Vertical, HorizontalScroll
from textual.screen import ModalScreen

import bulb.utils.config as cfg

class LogViewerApp(App):

    def __init__(self):
        super().__init__()
        self.log_dir = Path.cwd() if cfg.bulb_config.Runner.logs_path is None else cfg.bulb_config.Runner.logs_path

        self.meta_df = self.load_df('meta.json')
        self.config_df = self.load_df('config.json')
        self.results_df = self.load_df('eval_log.json')

        self.all_df = pd.merge(
            self.meta_df, 
            self.config_df,
            on='id',
            how='inner'
        )

        self.all_df = pd.merge(
            self.all_df, 
            self.results_df,
            on='id',
            how='inner'
        )

    def load_df(self, log_name) -> None:
        log_dir = self.log_dir
        json_files = list(log_dir.glob(f"*/{log_name}"))
        
        data, ids = [], []
        for json_file in json_files:
            with open(json_file) as f:
                try:
                    json_data = json.load(f)
                    if log_name == 'eval_log.json':
                        json_data = {'success_rate': json_data.get('test/mean_score')}

                    json_data = flatten_dict(json_data, sep='/')

                    data.append(json_data)
                    ids.append(json_file.parent.name)
                except json.JSONDecodeError:
                    continue

        df = pd.DataFrame(data)

        df.insert(0, 'id', ids)
        df.set_index('id', inplace=True)
        return df
        

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Meta"):
                yield LogTable(self.meta_df)
            with TabPane("Config"):
                yield LogTable(self.config_df)
            with TabPane("Results"):
                yield LogTable(self.results_df)
            with TabPane("All"):
                yield LogTable(self.all_df)
        # yield Footer()

    

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

class LogTable(DataTable):
    # CSS = """
    # #table-container {
    #     height: 100%;  # Critical for layout
    #     overflow: auto;
    # }
    # """

    # DataTable {
    #     height: 100%;  # Required for visibility
    # }
    # """
    
    BINDINGS = [
        ("ctrl+r", "reset_filters", "Reset Filters"),
        ("ctrl+t", "toggle_columns", "Toggle Columns"),
        ("ctrl+s", "toggle_sorter", "Toggle Sorter"),
    ]

    def __init__(self, original_data: pd.DataFrame):
        super().__init__()

        self.filter_query = var("")
        self.original_data = pd.DataFrame()
        self.filtered_data = pd.DataFrame()

        self.columns_visibility = None
        self.sorting_keys = None

        self.original_data = original_data

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Filter:"),
            Input(id="filter-input", placeholder="Type to filter..."),
            HorizontalScroll(  # <-- Add HorizontalScroll container
                DataTable(id="data-table", cursor_type='row', zebra_stripes=True)
            ),
            id="table-container"
        )

    def on_mount(self) -> None:

        self.filtered_data = self.original_data.copy()

        self.columns_visibility = {col: True for col in self.original_data.columns.tolist()}
        self.sorting_keys = {col: False for col in self.original_data.columns.tolist()}
        self.update_table()


    def update_table(self) -> None:
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        
        if not self.filtered_data.empty:
            # Convert only visible columns to strings for display
            display_data = self.filtered_data[[k for k, v in self.columns_visibility.items() if v]].astype(str)
            display_data = display_data.sort_values([k for k, v in self.sorting_keys.items() if v], ascending=True)
            
            # Add columns
            table.add_columns(*display_data.columns.tolist())
            
            # Add rows
            for _, row in display_data.iterrows():
                table.add_row(*row.tolist())

    @on(Input.Changed, "#filter-input")
    def handle_filter(self, event: Input.Changed) -> None:
        self.filter_query = event.value.lower()
        self.apply_filters()

    def apply_filters(self) -> None:
        if self.filter_query:
            # Split the query into parts
            query_parts = self.filter_query.lower().split()
            
            # Initialize mask as all True
            mask = pd.Series(True, index=self.original_data.index)
            
            # For each part, update mask to require that part to match
            for part in query_parts:
                part_mask = self.original_data.astype(str).apply(
                    lambda row: row.str.contains(part, case=False).any(),
                    axis=1
                )
                mask &= part_mask
            
            self.filtered_data = self.original_data.loc[mask]
        else:
            self.filtered_data = self.original_data.copy()
        
        self.update_table()

    def action_reset_filters(self) -> None:
        self.filter_query = ""
        self.query_one("#filter-input", Input).value = ""
        self.filtered_data = self.original_data.copy()
        self.update_table()

    def action_toggle_columns(self) -> None:
        """Open a dialog to select visible columns."""
        def update_column_visibility(columns: dict[str, bool]) -> None:
            self.columns_visibility = columns
            self.update_table()
        # Create a Dialog with checkboxes
        dialog = FilterScreen(self.columns_visibility)
        self.app.push_screen(dialog, update_column_visibility)

    def action_toggle_sorter(self) -> None:
        """Open a dialog to select visible columns."""
        def update_sorting_keys(columns: dict[str, bool]) -> None:
            self.sorting_keys = columns
            self.update_table()
        # Create a Dialog with checkboxes
        dialog = FilterScreen(self.sorting_keys)
        self.app.push_screen(dialog, update_sorting_keys)


from textual.screen import ModalScreen
from textual.widgets import Checkbox, Button, Label
from textual.containers import Vertical, VerticalScroll
from textual import on
from textual.app import ComposeResult
class FilterScreen(ModalScreen):
    """Screen for toggling column visibility."""
    CSS = """
    FilterScreen {
        align: center middle;
    }
    .dialog {
        padding: 0 1;
        width: 50%;  /* Increased width */
        height: 50%;  /* Increased height */
        border: thick $background 80%;
        background: $surface;
    }
    .grid-layout {
        layout: grid;
        width: 100%;
        grid-gutter: 1 1;
        grid-size: 2;  /* Changed to 4 columns */
        grid-rows: auto;  /* Dynamic rows */
        overflow-y: auto;  /* Add scrolling if needed */
        max-height: 70%;  /* Limit height */
    }
    .dialog-checkbox {
        width: 100%;
    }
    """

    BINDINGS = [("escape", "apply_changes", "Cancel")]
    
    def __init__(self, columns_visibility: dict[str, bool]):
        super().__init__()
        columns_visibility = columns_visibility
        columns = list(columns_visibility.keys())

        self.columns_visibility_list = ReorderableSelectionList[str](
                    *((column, column, columns_visibility[column]) 
                    for column in columns)
                )
    
    def compose(self) -> ComposeResult:
        yield Vertical(
                Label(
                    "Toggle Columns",
                    classes="dialog-title",
                ),
                self.columns_visibility_list,
                classes="dialog",
            )
    
    @on(Button.Pressed, "#apply_button")
    def action_apply_changes(self) -> None:
        visibility_states = {
            opt.value: opt.value in self.columns_visibility_list.selected
            for opt in self.columns_visibility_list.options
        }
        self.dismiss(visibility_states)

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, SelectionList
from textual import events
from typing import TypeVar, Generic

T = TypeVar('T')

class ReorderableSelectionList(SelectionList[T], Generic[T]):
    """
    A SelectionList that allows reordering items using W/S keys.
    """
    
    def key_w(self) -> None:
        """Handle W key to move items up."""
        self._reorder_items(True)

    def key_s(self) -> None:
        """Handle S key to move items down."""
        self._reorder_items(False)

    def _reorder_items(self, move_up: bool) -> None:
        selected_values = self.selected

        if not selected_values:
            return
        
        new_index = self.highlighted - 1 if move_up else self.highlighted + 1
        self.options[new_index], self.options[self.highlighted] = self.options[self.highlighted], self.options[new_index]

        options = self.options.copy()

        # Rebuild the list while preserving selection
        self.clear_options()
        for opt in options:
            self.add_option(opt)

        self.highlighted = new_index
        



def log_table_tui():
    app = LogViewerApp()
    app.run()

if __name__ == "__main__":
    log_table_tui()