# Task Tracker

A console-based task tracking application that helps you manage and time your tasks using a stack-based approach. Perfect for developers who need to track time spent on tasks, handle interruptions, and maintain a log of completed work.

## Features

- Interactive shell interface with visual task hierarchy
- Stack-based task management (push/pop) for handling interruptions
- Automatic time tracking with pause/resume functionality
- Task history logging with start and completion times
- Smart prompt with truncated task names for readability
- Emergency killswitch to end all tasks cleanly
- Persistent JSON-based task history

## Commands

- `start <task_name>`: Start a new task (pushes current task to stack if one exists)
- `done`: Complete current task and resume previous task
- `pause`: Pause the current task's timer (e.g., for breaks)
- `resume`: Resume a paused task
- `list`: Show all tasks in the stack
- `history`: View completed tasks
- `killall`: End all active tasks immediately and log them
- `cls` or `clear`: Clear the screen
- `export [filename] [days_back]`: Export tasks to CSV (e.g., `export tasks.csv 7` for last week)
- `quit`: Exit the application (only if no active tasks)
- `help`: Show available commands

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/task-tracker.git
cd task-tracker
```

2. No additional dependencies required - uses Python standard library only!

## Usage

### Direct Launch
```bash
python task_tracker.py
```

### Using the Shortcut (Windows)
Double-click the `start_task_tracker.bat` file or create a shortcut to it for easy access.

### Example Session
```
no active task> start "Write documentation"
Write documentation [00:00]> start "Answer urgent email"  # Interruption
> Answer urgent email [00:00]> pause  # Take a break
> Answer urgent email [PAUSED]> resume
> Answer urgent email [00:05]> done
Write documentation [00:15]> done
no active task> quit
```

### Task History
Completed tasks are logged to `completed_tasks.json` with:
- Task name
- Start time
- Completion time
- Total time spent

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
