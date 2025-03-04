import json
from pathlib import Path
from typing import Callable, List
import pandas as pd
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import DataTable, Input, Static
from textual import on
from textual.reactive import var
from textual.widgets import DataTable, Footer, Header, Input, Label, Select, Button
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen

class LogViewerApp(App):
    CSS = """
    Container {
        layout: vertical;
        padding: 1;
    }
    #filter-input {
        margin-bottom: 1;
    }
    #table-container {
        height: 1fr;
    }
    DataTable {
        height: 1fr;
    }
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
        yield Container(
            Static("Filter (fuzzy match):"),
            Input(id="filter-input", placeholder="Type to filter..."),
            Static("Click column headers to sort", id="sort-instruction"),
            DataTable(id="log-table"),
            id="table-container"
        )

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
        # column_visibility = [(col, col in self.visible_columns) for col in columns]
        
        # Create a Dialog with checkboxes
        dialog = FilterScreen(columns)
        self.push_screen(dialog)

    def on_dialog_submitted(self, value: str) -> None:
        if value == "OK":
            # Update visible_columns based on user selection
            # (This is a simplified version; you might need to implement the actual selection logic)
            pass  # Add your logic here to update self.visible_columns

class FilterScreen(ModalScreen):
    """Screen for setting up filters."""
    
    BINDINGS = [("escape", "app.pop_screen", "Cancel")]
    
    def __init__(self, columns: List[str]):
        super().__init__()
        self.columns = columns
        
    def compose(self) -> ComposeResult:
        with Vertical(id="filter_container"):
            yield Label("Filter Table", id="filter_title")
            with Horizontal():
                yield Label("Column:")
                yield Select([(col, col) for col in self.columns], id="filter_column", value=self.columns[0])
            with Horizontal():
                yield Label("Contains:")
                yield Input(id="filter_value", placeholder="Filter value")
            with Horizontal(id="filter_buttons"):
                yield Button("Apply", id="apply_button")
                yield Button("Cancel", id="cancel_button")
    
    @on(Input.Submitted)
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when the user presses Enter in the filter value input."""
        self.apply_filter_and_close()
    
    @on(Button.Pressed, "#apply_button")
    def on_apply_button(self, event: Button.Pressed) -> None:
        """Handle when the apply button is pressed."""
        self.apply_filter_and_close()
    
    @on(Button.Pressed, "#cancel_button")
    def on_cancel_button(self, event: Button.Pressed) -> None:
        """Handle when the cancel button is pressed."""
        self.app.pop_screen()
    
    def apply_filter_and_close(self) -> None:
        """Apply the filter and close the screen."""
        column = self.query_one("#filter_column").value
        value = self.query_one("#filter_value").value
        self.apply_filter(column, value)
        self.app.pop_screen()

if __name__ == "__main__":
    app = LogViewerApp()
    app.run()