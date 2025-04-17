import copy
import json
from pathlib import Path
from typing import Callable, Dict, List, Optional
import pandas as pd
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Input, Static
from textual import on
from textual.reactive import var
from textual.widgets import DataTable, Footer, Header, Input, Label, Select, Button, TabbedContent, TabPane
from textual.widget import Widget
from textual.events import Event
from textual.widgets.tabbed_content import ContentTabs
from textual.containers import Horizontal, Vertical, HorizontalScroll
from textual.screen import ModalScreen

import bulb.utils.config as cfg


class TabNameScreen(ModalScreen[Optional[str]]):
    """Screen to prompt for a new tab name."""
    CSS = """
    TabNameScreen {
        align: center middle;
    }
    .dialog {
        padding: 1;
        width: 50%;
        height: 10;
        border: thick $background 80%;
        background: $surface;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Input(placeholder="Enter tab name", id="tab-name-input")
            with Horizontal():
                yield Button("OK", id="ok-button")
                yield Button("Cancel", id="cancel-button")
    
    @on(Input.Submitted, "#tab-name-input")
    @on(Button.Pressed, "#ok-button")
    def submit_name(self) -> None:
        name = self.query_one("#tab-name-input", Input).value.strip()
        if name:
            self.dismiss(name)
        else:
            self.dismiss(None)
    
    @on(Button.Pressed, "#cancel-button")
    def cancel(self) -> None:
        self.dismiss(None)

class Remove(Event):
    def __init__(self, await_remove) -> None:
        super().__init__()
        self.await_remove = await_remove

class AutoClosingTabPane(TabPane):
    async def on_remove(self, event: Remove) -> None:
        
        """Handle table closure and check if empty"""
        await event.await_remove
        if len(self.children[0].children) == 0:
            if tabs := self.app.query_one("#tabs-container", TabbedContent):
                tabs.remove_pane(self.id)
                # return
        # return super().render()

        
class LogViewerApp(App):
    BINDINGS = [
        ("ctrl+s", "create_table", "New Table"),
        ("ctrl+n", "new_tab", "New Tab"),
    ]

    def __init__(self):
        super().__init__()
        self.log_dir = Path.cwd() if cfg.bulb_config is None or cfg.bulb_config.Runner.logs_path is None else cfg.bulb_config.Runner.logs_path

        self.meta_df = self.load_df('meta.json')
        self.config_df = self.load_df('config.json')
        self.results_df = self.load_df('eval_log.json')

        self.all_df = pd.merge(
            self.meta_df, 
            self.config_df,
            on='id',
            how='outer'
        )

        self.all_df = pd.merge(
            self.all_df, 
            self.results_df,
            on='id',
            how='outer'
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
        yield Header()
        with TabbedContent(id="tabs-container"):
            with AutoClosingTabPane("Main"):
                with HorizontalScroll(classes="tables-container"):
                    yield LogTable(self.all_df)
        yield Footer()

    def save_state(self) -> None:
        """Save current app state to ~/.config/log_viewer_config.json."""
        tabs_container = self.query_one("#tabs-container", TabbedContent)
        active_tab = tabs_container.active or "Main"
        state = {
            "version": 1,
            "active_tab": active_tab,
            "tabs": []
        }

        for pane in tabs_container.query(AutoClosingTabPane):
            tab_name = pane._title.plain
            container = pane.query_one(".tables-container", HorizontalScroll)
            tables = []
            for table in container.query(LogTable):
                tables.append(table.get_config())
            state["tabs"].append({"name": tab_name, "tables": tables})

        config_path = Path.home() / ".config" / "log_viewer_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(config_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.log.error(f"Failed to save state: {e}")

    def load_state(self, state: dict) -> None:
        """Load app state from configuration."""
        tabs_container = self.query_one("#tabs-container", TabbedContent)
        # Remove existing tabs
        tabs_container.clear_panes()
        # Add saved tabs
        for tab_info in state.get("tabs", []):
            tab_name = tab_info["name"]
            tables_configs = tab_info["tables"]
            container = HorizontalScroll(*[LogTable(self.all_df, config) for config in tables_configs], classes="tables-container")
                
            tabs_container.add_pane(AutoClosingTabPane(tab_name, container))
        # Set active tab
        if "active_tab" in state and state["active_tab"] in [pane._title.plain for pane in tabs_container.query(AutoClosingTabPane)]:
            tabs_container.active = state["active_tab"]

    def on_mount(self) -> None:
        """Load saved state on startup if available."""
        config_path = Path.home() / ".config" / "log_viewer_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    self.load_state(json.load(f))
            except Exception as e:
                self.log.error(f"Error loading state: {e}")
                self.setup_default_view()
        else:
            self.setup_default_view()
        self.query_one(LogTable).focus()

    def setup_default_view(self) -> None:
        """Initialize default view if no saved state exists."""
        tabs_container = self.query_one("#tabs-container", TabbedContent)
        tabs_container.add_pane(AutoClosingTabPane("Main", HorizontalScroll(LogTable(self.all_df), classes="tables-container")))

    def action_quit(self) -> None:
        """Save state and exit."""
        self.save_state()
        self.exit()

    def action_new_tab(self) -> None:
        """Create a new tab with a LogTable."""
        def handle_tab_name(name: Optional[str]) -> None:
            if name:
                tabs = self.query_one("#tabs-container", TabbedContent)

                new_table = LogTable(self.all_df)
                new_container = HorizontalScroll(new_table, classes="tables-container")
                
                tabs.add_pane(AutoClosingTabPane(name, new_container))
                new_table.focus()
                
        self.push_screen(TabNameScreen(), handle_tab_name)

    def action_create_table(self) -> None:
        """Add a new table to the current tab."""
        current_tab = self.query_one("#tabs-container", TabbedContent).active_pane
        if current_tab:
            container = current_tab.query_one(".tables-container", HorizontalScroll)
            new_table = LogTable(self.all_df)
            container.mount(new_table)
            new_table.focus()


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
    BINDINGS = [
        ("ctrl+r", "reset_filters", "Reset Filters"),
        ("ctrl+t", "toggle_columns", "Toggle Columns"),
        ("ctrl+s", "toggle_sorter", "Toggle Sorter"),
        ("ctrl+w", "close_table", "Close Table"),
        ("ctrl+d", "delete_row", "Delete Row"),
    ]

    def __init__(self, original_data: pd.DataFrame, config=None):
        super().__init__()
        self.filter_query = ""

        self.columns_visibility = None
        self.sorting_keys = None

        self.original_data = original_data
        self.filtered_data = pd.DataFrame()
        self.config = config

    def get_config(self) -> dict:
        """Return current table configuration."""
        return {
            "columns_visibility": copy.deepcopy(self.columns_visibility),
            "sorting_keys": copy.deepcopy(self.sorting_keys),
            "filter_query": self.filter_query,
        }

    def apply_config(self, config: dict) -> None:
        """Apply saved configuration to the table."""
        current_columns = self.original_data.columns.tolist()
        # Update columns visibility
        self.columns_visibility = {
            col: config.get("columns_visibility", {}).get(col, False)
            for col in current_columns
        }
        # Update sorting keys
        self.sorting_keys = {
            col: config.get("sorting_keys", {}).get(col, False)
            for col in current_columns
        }
        # Update filter query
        self.filter_query = config.get("filter_query", "")
        # Set filter input value
        filter_input = self.query_one("#filter-input", Input)
        filter_input.value = self.filter_query
        # Apply filters and refresh
        self.apply_filters()
        self.update_table()

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
        if self.config is not None:
            self.apply_config(self.config)
        else:

            self.filtered_data = self.original_data.copy()

            self.columns_visibility = {col: False for col in self.original_data.columns.tolist()}
            self.sorting_keys = {col: False for col in self.original_data.columns.tolist()}
            self.update_table()

    def action_close_table(self) -> None:
        """Close the currently focused table."""
        await_remove = self.remove()
        self.post_message(Remove(await_remove))
        


    def update_table(self) -> None:
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        
        if not self.filtered_data.empty:
            # Convert only visible columns to strings for display
            display_data = self.filtered_data[[k for k, v in self.columns_visibility.items() if v]].astype(str)
            display_data = display_data.sort_values([k for k, v in self.sorting_keys.items() if v], ascending=False)
            
            # Add columns
            table.add_columns(*display_data.columns.tolist())
            
            # Add rows
            for _, row in display_data.iterrows():
                table.add_row(*row.tolist())

            self.display_data = display_data

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
                # Handle negation with ~ prefix
                is_negated = part.startswith('~')
                search_term = part[1:] if is_negated else part
                
                # Convert data to string and check if any column contains the search term
                part_mask = self.original_data.astype(str).apply(
                    lambda row: row.str.contains(search_term, case=False).any(),
                    axis=1
                )
                
                # Apply negation if needed
                if is_negated:
                    part_mask = ~part_mask
                    
                # Update the combined mask with AND operation
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
        dialog = ColumnScreen(self.columns_visibility)
        self.app.push_screen(dialog, update_column_visibility)

    def action_toggle_sorter(self) -> None:
        """Open a dialog to select visible columns."""
        def update_sorting_keys(columns: dict[str, bool]) -> None:
            self.sorting_keys = columns
            self.update_table()
        # Create a Dialog with checkboxes
        dialog = SortingScreen(self.sorting_keys, self.columns_visibility)
        self.app.push_screen(dialog, update_sorting_keys)

    def action_delete_row(self) -> None:
        """Delete the currently selected row."""
        table = self.query_one("#data-table", DataTable)
        selected_row = table.cursor_coordinate.row
        if selected_row is not None:
            action_id = self.display_data.index[table.cursor_row]  # Get action_id field
            log_dir = self.app.log_dir / action_id  # Construct path to directory
            if log_dir.exists():
                shutil.rmtree(log_dir)  # Delete directory and contents
            table.remove_row(table.coordinate_to_cell_key(table.cursor_coordinate)[0])  # Remove from table view
            self.original_data.drop(action_id, inplace=True)  # Remove from DataFrame
            self.display_data.drop(action_id, inplace=True)  # Remove from filtered view
            



class ColumnScreen(ModalScreen):
    """Screen for toggling column visibility."""
    CSS = """
    ColumnScreen {
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

    BINDINGS = [("escape", "apply_changes", "Apply Changes")]
    
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
                Footer(),
                classes="dialog",
            )
    
    @on(Button.Pressed, "#apply_button")
    def action_apply_changes(self) -> None:
        visibility_states = {
            opt.value: opt.value in self.columns_visibility_list.selected
            for opt in self.columns_visibility_list.options
        }
        self.dismiss(visibility_states)

class SortingScreen(ModalScreen):
    """Screen for toggling column visibility."""
    CSS = """
    SortingScreen {
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

    BINDINGS = [("escape", "apply_changes", "Apply Changes"),
                ("ctrl+i", "column_order", "Use column order"),]
    
    def __init__(self, lines_sorting: dict[str, bool], columns_visibility: dict[str, bool]):
        super().__init__()
        self.lines_sorting = lines_sorting
        self.columns_visibility = columns_visibility

    
    def compose(self) -> ComposeResult:
        self.lines_sorting_list = ReorderableSelectionList[str](
                    *((column, column, self.lines_sorting[column]) 
                    for column in list(self.lines_sorting.keys()))
                )
        yield Vertical(
                Label(
                    "Toggle Columns",
                    classes="dialog-title",
                ),
                self.lines_sorting_list,
                Footer(),
                classes="dialog",
            )
    
    def action_apply_changes(self) -> None:
        visibility_states = {
            opt.value: opt.value in self.lines_sorting_list.selected
            for opt in self.lines_sorting_list.options
        }
        self.dismiss(visibility_states)

    def action_column_order(self) -> None:
        # Update the data source
        self.lines_sorting = dict(self.columns_visibility)  # Create a copy
        
        # Create new list with updated data
        new_list = ReorderableSelectionList(
            *((column, column, self.lines_sorting[column]) 
            for column in self.lines_sorting)
        )
        
        # Get the vertical container
        vertical = self.query_one(".dialog")
        
        # Remove old list
        old_list = self.lines_sorting_list
        old_list.remove()  # Correct method to remove widget
        
        # Mount new list in the correct position (after Label, before Footer)
        vertical.mount(new_list, after=vertical.query_one(Label))
        
        # Update reference
        self.lines_sorting_list = new_list
        
        # Refresh layout
        self.refresh(layout=True)
    

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, SelectionList
from textual import events
from typing import TypeVar, Generic
import shutil

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

