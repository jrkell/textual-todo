from textual.app import App
from textual.widgets import Footer, Header, Input, Label, ListView, ListItem
import sys
sys.stdout.reconfigure(encoding='utf-8')


### CONFIG ###
from pathlib import Path
current_dir = Path(__file__).parent
SAVE_FILE_PATH = f"{current_dir}/todo.txt"
APP_TITLE = "Jarry's TODO"

##############


class TodoApp(App):
    TITLE = "Jared's Todo List"
    
    BINDINGS = [
        ("q", "quit", "quit"),
        ("a", "add_todo", "add"),
        ("d", "delete_todo", "delete"),
        ("e", "edit_todo", "edit"),
        ("shift+up", "move_todo_up", "move up"),
        ("shift+down", "move_todo_down", "move down")
    ]

    # CSS_PATH = f"{current_dir}/synthwave.tcss"

    theme = "dracula"

    def __init__(self, todos: list[str]):
        super().__init__()
        self.todos = todos        
        self.todo_list_view = ListView(initial_index=1)
        # self.todo_list_view.BORDER_TITLE = APP_TITLE
        # self.todo_list_view.css
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
            self.todo_list_view.append(ListItem(Label("No todos in list! Press 'a' to add one.", id="empty")))
            return

        for index, todo in enumerate(self.todos):
            list_item = ListItem(Label(todo, id=f"index-{index}"))
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

    # # bit of trickery to an edited item back in the same spot
    # def move_last_todo_to_index(self, index: int):
    #     self.todos.pop(index)
    #     new = self.todos.pop(len(self.todos)-1)
    #     self.todos.insert(index, new)
        
    def action_delete_todo(self):
        index = self.todo_list_view.index
        self.todos.pop(index)
        self.save_todos()
        self.display_todos()

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


class TodoListView(ListView):
        #     self.todo_list_view = ListView(initial_index=1)
        # self.todo_list_view.BORDER_TITLE = APP_TITLE
        # self.todo_list_view.css
    def __init__(self):
        super().__init__(initial_index=1)
        self.BORDER_TITLE = APP_TITLE

class TodoListItem(ListItem):
    pass

def import_todo_list():
    file = open(SAVE_FILE_PATH, "r", encoding='utf-8')
    return [i.strip() for i in file.readlines()]

def export_todo_list(todos: list[str]):
    with open(SAVE_FILE_PATH, "w", encoding='utf-8') as file:
        for todo in todos:
            file.write(todo + "\n")

if __name__ == "__main__":
    todos = import_todo_list()
    app = TodoApp(todos)
    app.run()