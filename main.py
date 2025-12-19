import json
import socket


class ToDoServer:
    def __init__(self):
        self.tasks = []
        self.load_tasks()

    def load_tasks(self):
        try:
            with open("tasks.txt", "r") as f:
                data = f.read()
                if data:
                    self.tasks = json.loads(data)
        except FileNotFoundError:
            self.tasks = []
        except json.JSONDecodeError:
            self.tasks = []

    def save_tasks(self):
        with open("tasks.txt", "w") as f:
            json.dump(self.tasks, f, indent=2)

    def get_next_id(self):
        if not self.tasks:
            return 1
        max_id = max(task["id"] for task in self.tasks)
        return max_id + 1

    def handle_connection(self, conn):
        data = conn.recv(5000).decode("utf-8")

        if not data:
            conn.close()
            return

        lines = data.split("\n")
        if not lines:
            conn.close()
            return

        first_line_parts = lines[0].split()
        if len(first_line_parts) < 2:
            conn.close()
            return

        method = first_line_parts[0]
        path = first_line_parts[1]

        body = ""
        for i in range(len(lines)):
            if lines[i] == "" and i + 1 < len(lines):
                body = lines[i + 1]
                break

        if path == "/tasks" and method == "GET":
            response = f"HTTP/1.1 200 OK\n\n{json.dumps(self.tasks)}"
            conn.send(response.encode())

        elif path == "/tasks" and method == "POST":
            if body:
                try:
                    task_data = json.loads(body)
                except:
                    conn.send(b"HTTP/1.1 200 OK\n\n")
                    conn.close()
                    return

                if "title" in task_data:
                    priority = task_data.get("priority", "normal")
                    if priority not in ["low", "normal", "high"]:
                        priority = "normal"

                    new_task = {
                        "id": self.get_next_id(),
                        "title": task_data["title"],
                        "priority": priority,
                        "isDone": False
                    }

                    self.tasks.append(new_task)
                    self.save_tasks()

                    response = f"HTTP/1.1 200 OK\n\n{json.dumps(new_task)}"
                    conn.send(response.encode())
                else:
                    conn.send(b"HTTP/1.1 200 OK\n\n")
            else:
                conn.send(b"HTTP/1.1 200 OK\n\n")

        elif method == "POST" and path.startswith("/tasks/") and path.endswith("/complete"):
            try:
                parts = path.split("/")
                task_id = int(parts[2])
            except:
                conn.send(b"HTTP/1.1 404 Not Found\n\n")
                conn.close()
                return

            for task in self.tasks:
                if task["id"] == task_id:
                    task["isDone"] = True
                    self.save_tasks()
                    conn.send(b"HTTP/1.1 200 OK\n\n")
                    conn.close()
                    return

            conn.send(b"HTTP/1.1 404 Not Found\n\n")

        else:
            conn.send(b"HTTP/1.1 404 Not Found\n\n")

        conn.close()

    def start(self, port=8000):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", port))
        server.listen(5)

        print(f"To-Do сервер запущен на порту {port}")
        print(f"Загружено задач: {len(self.tasks)}")

        try:
            while True:
                conn, addr = server.accept()
                self.handle_connection(conn)
        except KeyboardInterrupt:
            print("\nСервер остановлен")
        finally:
            server.close()


app = ToDoServer()
app.start()