import sys
from collections import defaultdict
from datetime import datetime, date
from os import listdir
from textual.app import App
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, ListView, ListItem, Static
sys.stdout.reconfigure(encoding='utf-8')

### CONFIG ###
from pathlib import Path
current_dir = Path(__file__).parent
SAVE_FILE_DIR = f"{current_dir}/todo-lists"
CURRENT_LIST_FILE = f"{current_dir}/current-list.txt"
APP_TITLE = "Jared's Todo List"
##############

global CURRENT_LIST

class TodoApp(App):
    CSS = """
        Horizontal {
            height: 1fr;
        }

        Horizontal Label {
            width: 1fr;
        }

        Input {
            width: 100%;
        }
    """

    TITLE = APP_TITLE
    
    BINDINGS = [
        ("q", "quit", "quit")
    ]

    theme = "dracula"

    def __init__(self):
        super().__init__()
        self.list_manager = ListManager(self)
        self.todo_list_view = TodoListView(self.list_manager)
        self.done_list_view = DoneListView(self.list_manager)
        self.input = Input()
    
    def compose(self):
        yield Header(show_clock=True, icon='🖊️')
        with Vertical():
            with Horizontal():
                yield self.todo_list_view
                yield self.done_list_view
            yield self.input

        yield Footer()

    def on_mount(self):
        self.update_lists()

    def update_lists(self):
        self.todo_list_view.update_list_display()
        self.done_list_view.update_list_display()

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        self.todo_list_view.save_or_edit_todo(submitted.value)
        self.input.value = ""
    
    def focus_list_view(self, index: int):
        self.todo_list_view.index = index
        self.todo_list_view.focus()

    def focus_input(self, text=""):
        self.input.value = text
        self.input.focus()
        
    def action_select_category(self):
        self.push_screen(SelectCategoryScreen())

class ListManager():
    def __init__(self, app: TodoApp):
        self.app = app
        self.current_list_name: str = open(CURRENT_LIST_FILE, "r", encoding='utf-8').read()

        with open(f"{SAVE_FILE_DIR}/{self.current_list_name}.txt", "r", encoding='utf-8') as file:
            self.todo_list = [i.strip() for i in file.readlines()]

        with open(f"{SAVE_FILE_DIR}/{self.current_list_name}.done.txt", "r", encoding='utf-8') as file:
            self.done_list: list[str] = [i.strip()for i in file.readlines()]

    def save_todo_list(self):
        with open(f"{SAVE_FILE_DIR}/{self.current_list_name}.txt", "w", encoding='utf-8') as file:
            for todo in self.todo_list:
                file.write(todo + "\n")

    def save_done_list(self):
        with open(f"{SAVE_FILE_DIR}/{self.current_list_name}.done.txt", "w", encoding='utf-8') as file:
            for done in self.done_list:
                file.write(done + "\n")

    def add_todo(self, todo: str):
        self.todo_list.append(todo)
        self.save_todo_list()

    def move_todo(self, index: int, move_by: int):
        item = self.todo_list.pop(index)
        self.todo_list.insert(index+move_by, item)
        self.save_todo_list()

    def move_todo_to_done(self, todo_index: int):
        item = self.todo_list.pop(todo_index)
        item_with_date = f"{datetime.now().isoformat()}::{item}"
        self.done_list.append(item_with_date)
        self.save_todo_list()
        self.save_done_list()
        self.app.update_lists()

    def edit_todo(self, index: int, new_todo: str):
        self.todo_list[index] = new_todo
        self.save_todo_list()

class TodoListView(ListView):
    BINDINGS = {
        ("a", "add_todo", "add"),
        ("d", "move_to_done", "move to done"),
        ("e", "edit_todo", "edit"),
        # ("c", "select_category", "select category"),
        ("shift+up", "move_todo_up", "move up"),
        ("shift+down", "move_todo_down", "move down")
    }

    def __init__(self, list_manager: ListManager):
        super().__init__(initial_index=1)
        self.list_manager = list_manager
        self.border_title = "Todo"
        self.styles.border = ("heavy", "white")
        self.editing: int = -1 

    def action_edit_todo(self):
        label = self.children[self.index].children[0]
        self.editing = self.index
        self.app.focus_input(label.content)

    def action_move_to_done(self):
        self.list_manager.move_todo_to_done(self.index)
        self.update_list_display()

    def action_add_todo(self):
        self.app.focus_input()

    def save_or_edit_todo(self, todo: str):
        if self.editing == -1:
            self.list_manager.add_todo(todo)
        else:
            self.list_manager.edit_todo(self.editing, todo)
        
        self.update_list_display()
        self.call_after_refresh(self.app.focus_list_view, self.editing)
        self.editing = -1 # set back to "add" mode

    def update_list_display(self):
        self.clear()

        todos = self.list_manager.todo_list

        if len(todos) == 0:
            self.append(TodoListItem("No todos in list! Press 'a' to add one."))
            return

        for todo in todos:
            list_item = TodoListItem(todo)
            self.append(list_item)
    
    def move_todo(self, move_by: int):
        current_index = self.index
        self.list_manager.move_todo(self.index, move_by)
        self.update_list_display()
        self.call_after_refresh(self.app.focus_list_view, current_index + move_by)

    def action_move_todo_up(self):
        self.move_todo(-1)

    def action_move_todo_down(self):
        self.move_todo(1)

class DoneListView(ListView):
    def __init__(self, list_manager: ListManager):
        super().__init__(initial_index=1)
        self.list_manager = list_manager
        self.border_title = "Done"
        self.styles.border = ("heavy", "white")

    def update_list_display(self):
        self.clear()

        dones = self.list_manager.done_list

        if len(dones) == 0:
            self.append(TodoListItem("No completed tasks yet!"))
            return
        
        # ["date::blah", "date::blah2", "date2::bleh"]
        date_groups = defaultdict(list)
        for done in dones:
            split_done = done.split("::")
            date = datetime.fromisoformat(split_done[0]).strftime("%Y-%m-%d")
            item = split_done[1]
            date_groups[date].append(item)

        for date, items in date_groups.items():
            self.append(ListItem(Label(date)))
            for item in items:
                list_item = ListItem(Label(f" ✅ {item}"))
                self.append(list_item)
            self.append(ListItem(Label(" ")))

class SelectCategoryScreen(ModalScreen[None]):
    BINDINGS = [
        ("q", "app.pop_screen", "close window"),
        ("enter", "select_category", "select category")    
    ]
    
    DEFAULT_CSS = """
    SelectListScreen {
        align: center middle;
    }
    
    #select-list-screen {
        align: center middle;
        width: auto;
        max-width: 70%;
        height: auto;
        max-height: 80%;
    }
    """
    
    list_view = ListView(initial_index=1)

    def compose(self):
        with Container(id="select-list-screen"):
            yield self.list_view
            yield Footer()
            
    def _on_mount(self):
        list_items = [ListItem(Label(i)) for i in get_category_names()]
        for item in list_items:
            self.list_view.append(item)
            
    def action_select_category(self):
        index = self.list_view.index
        label = self.list_view.children[index].children[0]
        set_category(label)

class TodoListItem(ListItem):
    def __init__(self, label: str):
        super().__init__(Label(label))

def set_category(category: str) -> None:
    CURRENT_LIST = category # todo fix
    with open(f"{CURRENT_LIST_FILE}.txt", "w", encoding='utf-8') as file:
        file.write(category)

def get_category_names() -> list[str]:
    files = listdir(SAVE_FILE_DIR)
    return [f.split(".txt")[0] for f in files]

if __name__ == "__main__":
    CURRENT_LIST = open(CURRENT_LIST_FILE, "r", encoding='utf-8').read() 
    app = TodoApp()
    app.run()