from textual.app import App
from textual.widgets import Footer, Header, Input, Label, ListView, ListItem

class TodoApp(App):
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add_todo", "Add Todo"),
        ("d", "delete_todo", "Delete Selected Todo")
    ]

    def __init__(self, todos: list[str]):
        super().__init__()
        self.todos = todos        
        self.todo_list_view = ListView()
        self.input = Input() 
    
    def compose(self):
        yield Header()
        yield Footer()
        yield self.todo_list_view
        yield self.input

    def on_mount(self):
        self.display_todos()
            
    def display_todos(self):
        self.todo_list_view.clear()
        for index, todo in enumerate(self.todos):
            list_item = ListItem(Label(todo, id=f"index-{index}"))
            self.todo_list_view.append(list_item)
            
    def save_todos(self):
        export_todo_list(todos)

    def on_input_submitted(self, submitted: Input.Submitted) -> None:
        self.input.visible = False
        self.todos.append(submitted.value)
        self.save_todos()
        self.display_todos()

    def action_add_todo(self):
        self.input.visible = True
        self.input.focus()
        
    def action_delete_todo(self):
        selected = self.todo_list_view.highlighted_child
        if selected != None:
            index = int(selected.children[0].id[6:])
            self.todos.pop(index)
            self.save_todos()
            self.display_todos()

def import_todo_list():
    file = open("todo.txt")
    return [i.strip() for i in file.readlines()]

def export_todo_list(todos: list[str]):
    with open("todo.txt", "w") as file:
        for todo in todos:
            file.write(todo + "\n")

if __name__ == "__main__":
    todos = import_todo_list()
    app = TodoApp(todos)
    app.run()