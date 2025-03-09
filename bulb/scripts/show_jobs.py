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
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen

class LogViewerApp(App):
    CSS = """
    # Container {
    #     layout: vertical;
    #     padding: 1;
    # }
    # #filter-input {
    #     margin-bottom: 1;
    # }
    # #table-container {
    #     height: 1fr;
    # }
    # DataTable {
    #     height: 1fr;
    # }
    """
    
    BINDINGS = [
        ("ctrl+r", "reset_filters", "Reset Filters"),
        ("ctrl+c", "toggle_columns", "Toggle Columns"),
    ]

    filter_query = var("")
    original_data = pd.DataFrame()
    filtered_data = pd.DataFrame()
    visible_columns = set()

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Meta"):
                yield Container(
                    Static("Filter (fuzzy match):"),
                    Input(id="filter-input", placeholder="Type to filter..."),
                    Static("Click column headers to sort", id="sort-instruction"),
                    DataTable(id="log-table", cursor_type='row'),
                    id="table-container"
                )
            with TabPane("Config"):
                yield Container()
            with TabPane("Results"):
                yield Container()
            with TabPane("All"):
                yield Container()

    def on_mount(self) -> None:
        self.load_data()
        self.visible_columns = set(self.original_data.columns.tolist())
        self.update_table()

    def load_data(self) -> None:
        log_dir = Path("/home/aros/projects/diffusion_policy/.bulb/robodiff_logs")
        meta_files = list(log_dir.glob("*/meta.json"))
        
        data = []
        for meta_file in meta_files:
            with open(meta_file) as f:
                try:
                    meta_data = json.load(f)
                    meta_data["directory"] = meta_file.parts[-2]
                    data.append(meta_data)
                except json.JSONDecodeError:
                    continue
        
        if data:
            self.original_data = pd.DataFrame(data)
            self.filtered_data = self.original_data.copy()

    def update_table(self) -> None:
        table = self.query_one("#log-table", DataTable)
        table.clear(columns=True)
        
        if not self.filtered_data.empty:
            # Convert only visible columns to strings for display
            display_data = self.filtered_data[list(self.visible_columns)].astype(str)
            
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
            mask = self.original_data.astype(str).apply(
                lambda row: row.str.contains(self.filter_query, case=False).any(),
                axis=1
            )
            self.filtered_data = self.original_data[mask]
        else:
            self.filtered_data = self.original_data.copy()
        
        self.update_table()

    @on(DataTable.HeaderSelected)
    def handle_sort(self, event: DataTable.HeaderSelected) -> None:
        column_name = self.filtered_data.columns[event.column_index]
        # Check if the first non-null value determines the sort order
        first_value = self.filtered_data[column_name].dropna().iloc[0]
        if first_value is not None:
            ascending = True
        else:
            ascending = False
        self.filtered_data = self.filtered_data.sort_values(
            column_name,
            ascending=ascending,
        )
        self.update_table()

    def action_reset_filters(self) -> None:
        self.filter_query = ""
        self.query_one("#filter-input", Input).value = ""
        self.filtered_data = self.original_data.copy()
        self.update_table()

    def action_toggle_columns(self) -> None:
        """Open a dialog to select visible columns."""
        columns = self.original_data.columns.tolist()
        # Create a list of tuples with column names and their visibility status
        column_visibility = {col: col in self.visible_columns for col in columns}
        def update_column_visibility(column_visibility: dict[str, bool]) -> None:
            self.visible_columns = {col for col, visible in column_visibility.items() if visible}
            self.update_table()
        # Create a Dialog with checkboxes
        dialog = FilterScreen(column_visibility)
        self.push_screen(dialog, update_column_visibility)

    def on_dialog_submitted(self, value: str) -> None:
        if value == "OK":
            # Update visible_columns based on user selection
            # (This is a simplified version; you might need to implement the actual selection logic)
            pass  # Add your logic here to update self.visible_columns

from textual.screen import ModalScreen
from textual.widgets import Checkbox, Button, Label
from textual.containers import Vertical, Horizontal, VerticalScroll
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
        self.columns_visibility = columns_visibility
        self.columns = list(columns_visibility.keys())
    
    def compose(self) -> ComposeResult:
        yield Vertical(
                Label(
                    "Toggle Columns",
                    classes="dialog-title",
                ),
                VerticalScroll(
                        *(
                            Checkbox(
                                column,
                                value=self.columns_visibility[column],
                                id=f"checkbox_{column}",
                                classes="dialog-checkbox",
                            )
                            for column in self.columns
                        ),
                        classes="grid-layout",
                ),
                classes="dialog",
            )
    
    @on(Button.Pressed, "#apply_button")
    def action_apply_changes(self) -> None:
        visibility_states = {
            column: self.query_one(f"#checkbox_{column}", Checkbox).value
            for column in self.columns
        }
        self.dismiss(visibility_states)

if __name__ == "__main__":
    app = LogViewerApp()
    app.run()