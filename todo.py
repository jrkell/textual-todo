from os import listdir
from textual.app import App
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Label, ListView, ListItem
import sys
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
    TITLE = APP_TITLE
    
    BINDINGS = [
        ("q", "quit", "quit"),
        ("a", "add_todo", "add"),
        ("d", "delete_todo", "delete"),
        ("e", "edit_todo", "edit"),
        ("c", "select_category", "select category"),
        ("shift+up", "move_todo_up", "move up"),
        ("shift+down", "move_todo_down", "move down")
    ]

    theme = "dracula"

    def __init__(self, todos: list[str]):
        super().__init__()
        self.todos = todos        
        self.todo_list_view = TodoListView()
        self.input = Input()
        self.editing: int = -1 
    
    def compose(self):
        yield Header(show_clock=True, icon='🖊️')
        yield Footer()
        yield self.todo_list_view
        yield self.input

    def on_mount(self):
        self.display_todos()
            
    def display_todos(self):
        self.todo_list_view.clear()

        if len(self.todos) == 0:
            self.todo_list_view.append(TodoListItem("No todos in list! Press 'a' to add one."))
            return

        for todo in self.todos:
            list_item = TodoListItem(todo)
            self.todo_list_view.append(list_item)
            
    def save_todos(self):
        export_todo_list(todos)

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        self.input.visible = False
        
        if self.editing == -1:
            self.todos.append(submitted.value)
        else:
            self.todos[self.editing] = submitted.value
        
        self.editing = -1 # set back to "add" mode
        self.save_todos()
        self.display_todos()

    def action_add_todo(self):
        self.input.value = ""
        self.input.visible = True
        self.input.focus()

    def action_edit_todo(self):
        index = self.todo_list_view.index
        label = self.todo_list_view.children[index].children[0]
        self.editing = index
        self.input.value = label.content
        self.input.visible = True
        self.input.focus()
        
    def action_delete_todo(self):
        index = self.todo_list_view.index
        self.todos.pop(index)
        self.save_todos()
        self.display_todos()
        
    def action_select_category(self):
        self.push_screen(SelectCategoryScreen())

    def move_todo(self, move_by: int):
        index = self.todo_list_view.index
        item = self.todos.pop(index)
        self.todos.insert(index+move_by, item)
        self.save_todos()
        self.display_todos()
        self.call_after_refresh(self.restore_focus, index + move_by)

    def restore_focus(self, index: int):
        self.todo_list_view.index = index
        self.todo_list_view.focus()

    def action_move_todo_up(self):
        self.move_todo(-1)

    def action_move_todo_down(self):
        self.move_todo(1)
        
    def reload_todos(self):
        todos = import_todo_list()

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
        
        

class TodoListView(ListView):
    def __init__(self):
        super().__init__(initial_index=1)
        self.border_title = APP_TITLE
        self.styles.border = ("heavy", "white")

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

def import_todo_list():
    file = open(f"{SAVE_FILE_DIR}/{CURRENT_LIST}.txt", "r", encoding='utf-8')
    return [i.strip() for i in file.readlines()]

def export_todo_list(todos: list[str]):
    with open(f"{SAVE_FILE_DIR}/{CURRENT_LIST}.txt", "w", encoding='utf-8') as file:
        for todo in todos:
            file.write(todo + "\n")

if __name__ == "__main__":
    CURRENT_LIST = open(CURRENT_LIST_FILE, "r", encoding='utf-8').read() 
    todos = import_todo_list()
    app = TodoApp(todos)
    app.run()