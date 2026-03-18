import sys
from collections import defaultdict
from datetime import datetime, date
from os import listdir
from textual.app import App
from textual.containers import Container, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, ListView, ListItem, Static
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

### CONFIG ###
from pathlib import Path
current_dir = Path(__file__).parent
SAVE_FILE_DIR = f"{current_dir}/todo-lists"
CURRENT_LIST_FILE = f"{current_dir}/current-list.txt"
APP_TITLE = "Jared's Todo List"
##############

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
        ("q", "quit", "quit"),
        ("c", "select_category", "select category"),
    ]

    theme = "dracula"

    def __init__(self):
        super().__init__()
        self.category_manager = CategoryManager()
        self.list_manager = ListManager(self, self.category_manager)
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

    def reload_lists_from_files(self):
        self.list_manager.load_lists()
        self.todo_list_view.update_list_display()
        self.done_list_view.update_list_display()

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
        self.push_screen(SelectCategoryScreen(self.category_manager))

class CategoryManager():
    def __init__(self):
        self.current_list_name: str = open(CURRENT_LIST_FILE, "r", encoding='utf-8').read()
        self.list_names = self.get_list_names()

    def get_list_names(self):
        list_names = []
        for file in listdir(SAVE_FILE_DIR):
            if file.endswith(".txt") and not file.endswith(".done.txt"):
                list_names.append(file.split(".txt")[0])
        return list_names

    def switch_list(self, index: int):
        self.current_list_name = self.list_names[index]
        with open(CURRENT_LIST_FILE, "w", encoding='utf-8') as file:
            file.write(self.current_list_name)

    def add_new_list(self, name: str):
        Path(f"{SAVE_FILE_DIR}/{name}.txt").touch()
        Path(f"{SAVE_FILE_DIR}/{name}.done.txt").touch()

class ListManager():
    def __init__(self, app: TodoApp, category_manager: CategoryManager):
        self.app = app
        self.category_manager = category_manager
        # self.current_list_name: str = category_manager.current_list_name
        self.load_lists()

    def load_lists(self):
        current_list_name = self.category_manager.current_list_name
        with open(f"{SAVE_FILE_DIR}/{current_list_name}.txt", "r", encoding='utf-8') as file:
            self.todo_list = [i.strip() for i in file.readlines()]

        with open(f"{SAVE_FILE_DIR}/{current_list_name}.done.txt", "r", encoding='utf-8') as file:
            self.done_list: list[str] = [i.strip()for i in file.readlines()]

    def save_todo_list(self):
        current_list_name = self.category_manager.current_list_name
        with open(f"{SAVE_FILE_DIR}/{current_list_name}.txt", "w", encoding='utf-8') as file:
            for todo in self.todo_list:
                file.write(todo + "\n")

    def save_done_list(self):
        current_list_name = self.category_manager.current_list_name
        with open(f"{SAVE_FILE_DIR}/{current_list_name}.done.txt", "w", encoding='utf-8') as file:
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
        
        sorted_dones = sorted(dones, reverse=True) # sort by most recent
        
        date_groups = defaultdict(list)
        for done in sorted_dones:
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
        ("space", "switch_category", "select category")    
    ]
    
    DEFAULT_CSS = """
    SelectCategoryScreen {
        align: center middle;
    }

    #select-list-screen {
        width: auto;
        max-width: 70%;
        height: auto;
        max-height: 80%;
    }
    """
    
    list_view = ListView(initial_index=1)
    list_view.styles.border = ("heavy", "white")
    list_view.border_title = "Select Category"
    
    def __init__(self, category_manager: CategoryManager):
        super().__init__()
        self.category_manager = category_manager

    def compose(self):
        with Container(id="select-list-screen"):
            yield self.list_view
            yield Footer()
            
    def _on_mount(self):
        list_items = [ListItem(Label(i)) for i in self.category_manager.get_list_names()]
        for item in list_items:
            self.list_view.append(item)
            
    def action_switch_category(self):
        self.category_manager.switch_list(self.list_view.index)
        self.app.reload_lists_from_files()
        self.app.pop_screen()

class TodoListItem(ListItem):
    def __init__(self, label: str):
        super().__init__(Label(label))


if __name__ == "__main__":
    app = TodoApp()
    app.run()