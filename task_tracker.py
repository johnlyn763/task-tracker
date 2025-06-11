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
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
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

    def get_full_display(self) -> str:
        """Returns full task info including description if available"""
        if self.description:
            return f"{self.name} - {self.description}"
        return self.name

    def edit_name(self, new_name: str):
        """Edit the task name"""
        self.name = new_name

    def edit_description(self, new_description: str):
        """Edit the task description"""
        self.description = new_description

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
        self.undo_stack: List[Dict] = []  # Stack for undo operations
        self.max_undo_history = 10  # Limit undo history
        self.update_prompt()

    def save_state_for_undo(self, action: str, data: Dict = None):
        """Save current state for undo functionality"""
        state = {
            'action': action,
            'timestamp': time.time(),
            'task_stack': [
                {
                    'name': task.name,
                    'description': task.description,
                    'start_time': task.start_time,
                    'start_datetime': task.start_datetime,
                    'elapsed_time': task.elapsed_time,
                    'is_paused': task.is_paused,
                    'pause_time': task.pause_time
                } for task in self.task_stack
            ],
            'data': data or {}
        }
        
        self.undo_stack.append(state)
        
        # Limit undo history
        if len(self.undo_stack) > self.max_undo_history:
            self.undo_stack.pop(0)

    def restore_task_from_state(self, task_data: Dict) -> Task:
        """Restore a Task object from saved state data"""
        task = Task(task_data['name'], task_data['description'])
        task.start_time = task_data['start_time']
        task.start_datetime = task_data['start_datetime']
        task.elapsed_time = task_data['elapsed_time']
        task.is_paused = task_data['is_paused']
        task.pause_time = task_data['pause_time']
        return task

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
        """Start a new task, pushing the current one (if any) onto the stack
        Usage: start <task_name> [description]
        Example: start "Fix bug" "Debug the login issue"
        """
        if not arg:
            print("Please provide a task name")
            return
        
        # Save state for undo
        self.save_state_for_undo('start')
        
        # Parse task name and optional description
        parts = arg.split(' ', 1)
        task_name = parts[0].strip('"')
        description = parts[1].strip('"') if len(parts) > 1 else ""
        
        if self.task_stack:
            self.task_stack[-1].pause()
        
        new_task = Task(task_name, description)
        self.task_stack.append(new_task)
        
        if description:
            print(f"Started task: {task_name} - {description}")
        else:
            print(f"Started task: {task_name}")
        
        self.update_prompt()

    def do_done(self, arg):
        """Complete the current task, logging it and resuming the previous task"""
        if not self.task_stack:
            print("No active task")
            return

        # Save state for undo (including the completed task data)
        completed_task = self.task_stack[-1]
        self.save_state_for_undo('done', {
            'completed_task': {
                'name': completed_task.name,
                'description': completed_task.description,
                'start_time': completed_task.start_time,
                'start_datetime': completed_task.start_datetime,
                'elapsed_time': completed_task.elapsed_time,
                'is_paused': completed_task.is_paused,
                'pause_time': completed_task.pause_time
            }
        })

        completed_task = self.task_stack.pop()
        self.log_completed_task(completed_task)
        print(f"Completed task: {completed_task.get_full_display()} [{completed_task.format_elapsed_time(include_seconds=True)}]")

        if self.task_stack:
            self.task_stack[-1].resume()
        
        self.update_prompt()

    def log_completed_task(self, task: Task):
        log_entry = {
            "task_name": task.name,
            "description": task.description,
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
            status = "PAUSED" if task.is_paused else task.format_elapsed_time()
            full_display = task.get_full_display()
            print(f"{i+1}. {full_display} [{status}]")

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
                    task_display = entry['task_name']
                    if entry.get('description'):
                        task_display += f" - {entry['description']}"
                    print(f"{task_display} - {entry['elapsed_time']}")
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
        known_commands = ['start', 'done', 'pause', 'resume', 'list', 'history', 'killall', 
                         'cls', 'clear', 'export', 'quit', 'help', '?', 'edit', 'info', 'undo']
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

    def do_edit(self, arg):
        """Edit the current task's name or description
        Usage: 
          edit name <new_name>     - Change task name
          edit desc <description>  - Change task description
          edit <new_name>          - Change task name (shortcut)
        """
        if not self.task_stack:
            print("No active task to edit")
            return
        
        if not arg:
            print("Usage: edit name <new_name> | edit desc <description> | edit <new_name>")
            return
        
        current_task = self.task_stack[-1]
        
        # Save state for undo
        self.save_state_for_undo('edit', {
            'old_name': current_task.name,
            'old_description': current_task.description
        })
        
        parts = arg.split(' ', 1)
        
        if parts[0].lower() == 'name' and len(parts) > 1:
            new_name = parts[1].strip('"')
            old_name = current_task.name
            current_task.edit_name(new_name)
            print(f"Task name changed from '{old_name}' to '{new_name}'")
        elif parts[0].lower() in ['desc', 'description'] and len(parts) > 1:
            new_description = parts[1].strip('"')
            current_task.edit_description(new_description)
            print(f"Task description updated: {new_description}")
        else:
            # Treat the entire argument as a new name
            new_name = arg.strip('"')
            old_name = current_task.name
            current_task.edit_name(new_name)
            print(f"Task name changed from '{old_name}' to '{new_name}'")
        
        self.update_prompt()

    def do_info(self, arg):
        """Show detailed information about the current task"""
        if not self.task_stack:
            print("No active task")
            return
        
        current_task = self.task_stack[-1]
        print(f"\nCurrent Task Information:")
        print(f"Name: {current_task.name}")
        if current_task.description:
            print(f"Description: {current_task.description}")
        print(f"Started: {datetime.fromisoformat(current_task.start_datetime).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed: {current_task.format_elapsed_time(include_seconds=True)}")
        print(f"Status: {'PAUSED' if current_task.is_paused else 'ACTIVE'}")

    def do_undo(self, arg):
        """Undo the last action (start, done, edit, etc.)"""
        if not self.undo_stack:
            print("Nothing to undo")
            return
        
        last_state = self.undo_stack.pop()
        action = last_state['action']
        
        # Restore the task stack from the saved state
        self.task_stack = [
            self.restore_task_from_state(task_data) 
            for task_data in last_state['task_stack']
        ]
        
        # Handle special undo cases
        if action == 'done' and 'completed_task' in last_state['data']:
            # Remove the last entry from completed tasks log if it exists
            self._remove_last_completed_task()
            print(f"Undid task completion")
        elif action == 'start':
            print(f"Undid task start")
        elif action == 'edit':
            data = last_state['data']
            print(f"Undid task edit (restored: '{data.get('old_name', 'N/A')}')")
        else:
            print(f"Undid {action}")
        
        self.update_prompt()

    def _remove_last_completed_task(self):
        """Remove the last completed task from the log file"""
        if not os.path.exists(self.log_file):
            return
        
        try:
            with open(self.log_file, 'r') as f:
                entries = json.load(f)
            
            if entries:
                entries.pop()  # Remove the last entry
                
                with open(self.log_file, 'w') as f:
                    json.dump(entries, f, indent=2)
        except (json.JSONDecodeError, IOError):
            pass  # Ignore errors when trying to undo log changes

if __name__ == '__main__':
    try:
        TaskTracker().cmdloop()
    except KeyboardInterrupt:
        print('\nTo exit cleanly, use the "quit" command or "killall" to end all tasks.')
