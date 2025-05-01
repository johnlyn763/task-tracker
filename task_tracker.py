import cmd
import time
from datetime import datetime, timedelta
import json
import os
import signal
import sys
import csv
from typing import List, Dict, Optional

class Task:
    def __init__(self, name: str):
        self.name = name
        self.start_time = time.time()
        self.start_datetime = datetime.now().isoformat()
        self.elapsed_time = 0.0
        self.is_paused = False
        self.pause_time: Optional[float] = None

    def get_display_name(self, max_length: int = 30) -> str:
        """Returns a shortened version of the task name for display purposes"""
        if len(self.name) <= max_length:
            return self.name
        return self.name[:max_length-3] + "..."

    def pause(self):
        if not self.is_paused:
            self.pause_time = time.time()
            self.elapsed_time += self.pause_time - self.start_time
            self.is_paused = True

    def resume(self):
        if self.is_paused:
            self.start_time = time.time()
            self.is_paused = False
            self.pause_time = None

    def get_elapsed_time(self) -> float:
        if self.is_paused:
            return self.elapsed_time
        return self.elapsed_time + (time.time() - self.start_time)

    def format_elapsed_time(self, include_seconds: bool = False) -> str:
        total_seconds = int(self.get_elapsed_time())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if include_seconds:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{hours:02d}:{minutes:02d}"

class TaskTracker(cmd.Cmd):
    intro = 'Welcome to TaskTracker! Type help or ? to list commands.\nUse Ctrl+C or type "quit" to exit.\n'
    
    def __init__(self):
        super().__init__()
        self.task_stack: List[Task] = []
        self.log_file = "completed_tasks.json"
        self.running = True
        self.update_prompt()

    def update_prompt(self):
        indent = "> " * (len(self.task_stack) - 1) if self.task_stack else ""
        if self.task_stack:
            current_task = self.task_stack[-1]
            status = "PAUSED" if current_task.is_paused else current_task.format_elapsed_time()
            display_name = current_task.get_display_name()
            self.prompt = f"{indent}{display_name} [{status}]> "
        else:
            self.prompt = "no active task> "

    def do_start(self, arg):
        """Start a new task, pushing the current one (if any) onto the stack"""
        if not arg:
            print("Please provide a task name")
            return
        
        if self.task_stack:
            self.task_stack[-1].pause()
        
        new_task = Task(arg)
        self.task_stack.append(new_task)
        self.update_prompt()

    def do_done(self, arg):
        """Complete the current task, logging it and resuming the previous task"""
        if not self.task_stack:
            print("No active task")
            return

        completed_task = self.task_stack.pop()
        self.log_completed_task(completed_task)

        if self.task_stack:
            self.task_stack[-1].resume()
        
        self.update_prompt()

    def log_completed_task(self, task: Task):
        log_entry = {
            "task_name": task.name,
            "started_at": task.start_datetime,
            "completed_at": datetime.now().isoformat(),
            "elapsed_time": task.format_elapsed_time(include_seconds=True)
        }

        existing_entries = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                try:
                    existing_entries = json.load(f)
                except json.JSONDecodeError:
                    pass

        existing_entries.append(log_entry)
        
        with open(self.log_file, 'w') as f:
            json.dump(existing_entries, f, indent=2)

    def do_list(self, arg):
        """List all tasks in the stack from bottom to top"""
        if not self.task_stack:
            print("No active tasks")
            return

        print("\nTask stack (bottom to top):")
        for i, task in enumerate(self.task_stack):
            print(f"{i+1}. {task.name} [{task.format_elapsed_time()}]")

    def do_history(self, arg):
        """Show completed tasks history"""
        if not os.path.exists(self.log_file):
            print("No completed tasks yet")
            return

        with open(self.log_file, 'r') as f:
            try:
                entries = json.load(f)
                print("\nCompleted tasks:")
                for entry in entries:
                    print(f"{entry['task_name']} - {entry['elapsed_time']}")
            except json.JSONDecodeError:
                print("Error reading history file")

    def do_pause(self, arg):
        """Pause the current task's timer"""
        if not self.task_stack:
            print("No active task to pause")
            return
        
        current_task = self.task_stack[-1]
        if current_task.is_paused:
            print("Task is already paused")
            return
            
        current_task.pause()
        print(f"Paused task: {current_task.name}")
        self.update_prompt()

    def do_resume(self, arg):
        """Resume the current task's timer"""
        if not self.task_stack:
            print("No active task to resume")
            return
            
        current_task = self.task_stack[-1]
        if not current_task.is_paused:
            print("Task is not paused")
            return
            
        current_task.resume()
        print(f"Resumed task: {current_task.name}")
        self.update_prompt()

    def do_killall(self, arg):
        """End all tasks immediately and log them"""
        if not self.task_stack:
            print("No active tasks")
            return

        print("\nEnding all active tasks:")
        while self.task_stack:
            task = self.task_stack.pop()
            if task.is_paused:
                task.resume()  # Resume to get final time
            print(f"- {task.name} [{task.format_elapsed_time()}]")
            self.log_completed_task(task)

        print("\nAll tasks completed and logged")
        self.update_prompt()

    def do_quit(self, arg):
        """Exit the application"""
        if self.task_stack:
            print("Warning: You have active tasks. Use 'done' to complete them or 'killall' to end all tasks.")
            return False
        return True

    def preloop(self):
        """Set up any initial state"""
        pass

    def emptyline(self):
        """Override empty line behavior to do nothing instead of repeating last command"""
        pass

    def postcmd(self, stop, line):
        """Update the prompt after each command"""
        self.update_prompt()
        return stop

    def do_EOF(self, arg):
        """Handle Ctrl+D (EOF)"""
        return self.do_quit(arg)

    def default(self, line):
        """Handle unknown commands by treating them as new task names"""
        # Don't treat empty lines as tasks
        if not line.strip():
            return
            
        # Check if the line starts with any known command
        known_commands = ['start', 'done', 'pause', 'resume', 'list', 'history', 'killall', 'cls', 'clear', 'export', 'quit', 'help', '?']
        if any(line.startswith(cmd) for cmd in known_commands):
            print(f"*** Unknown syntax: {line}")
            return

        # Treat the input as a task name
        print(f"Starting task: {line}")
        self.do_start(line)

    def do_cls(self, arg):
        """Clear the screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    # Add alias for cls command
    do_clear = do_cls

    def do_export(self, arg):
        """Export completed tasks to a CSV file. Usage: export [filename] [days_back]
        Example: export tasks.csv 7 (exports last 7 days of tasks)
        If days_back is not specified, exports all tasks."""
        # Parse arguments
        args = arg.split()
        filename = args[0] if args else 'task_summary.csv'
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        try:
            days_back = int(args[1]) if len(args) > 1 else None
        except ValueError:
            print("Error: days_back must be a number")
            return

        # Read completed tasks
        if not os.path.exists(self.log_file):
            print("No completed tasks found")
            return

        try:
            with open(self.log_file, 'r') as f:
                tasks = json.load(f)
        except json.JSONDecodeError:
            print("Error reading task history")
            return

        # Filter tasks by date if days_back is specified
        if days_back is not None:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            tasks = [
                task for task in tasks
                if datetime.fromisoformat(task['started_at']) >= cutoff_date
            ]

        if not tasks:
            print("No tasks found in the specified time period")
            return

        # Sort tasks by start time
        tasks.sort(key=lambda x: x['started_at'])

        # Write to CSV
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Task Name', 'Started At', 'Completed At', 'Time Spent'])
                
                for task in tasks:
                    # Convert ISO timestamps to more readable format
                    started = datetime.fromisoformat(task['started_at']).strftime('%Y-%m-%d %H:%M')
                    completed = datetime.fromisoformat(task['completed_at']).strftime('%Y-%m-%d %H:%M')
                    
                    # Parse and reformat time to ensure consistent HH:MM:SS format
                    if ':' in task['elapsed_time']:
                        parts = task['elapsed_time'].split(':')
                        if len(parts) == 2:  # HH:MM format
                            h, m = map(int, parts)
                            elapsed = f"{h:02d}:{m:02d}:00"
                        else:  # HH:MM:SS format
                            h, m, s = map(int, parts)
                            elapsed = f"{h:02d}:{m:02d}:{s:02d}"
                    else:
                        elapsed = task['elapsed_time']  # Handle any legacy format
                    
                    writer.writerow([
                        task['task_name'],
                        started,
                        completed,
                        elapsed
                    ])

            print(f"\nExported {len(tasks)} tasks to {filename}")
            
            # Calculate and show some basic statistics
            total_tasks = len(tasks)
            unique_days = len(set(datetime.fromisoformat(t['started_at']).date() for t in tasks))
            print(f"Summary:")
            print(f"- Total tasks: {total_tasks}")
            print(f"- Unique days: {unique_days}")
            print(f"- Tasks per day: {total_tasks/unique_days:.1f}")
            
        except Exception as e:
            print(f"Error writing CSV file: {e}")

if __name__ == '__main__':
    try:
        TaskTracker().cmdloop()
    except KeyboardInterrupt:
        print('\nTo exit cleanly, use the "quit" command or "killall" to end all tasks.')
