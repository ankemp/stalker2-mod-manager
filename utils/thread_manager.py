"""
Thread Manager for tracking and managing background operations.
Provides centralized tracking of all background threads and graceful shutdown.
"""

import threading
import time
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field


class TaskType(Enum):
    """Types of background tasks"""
    DOWNLOAD = "download"
    INSTALL = "install"
    UPDATE_CHECK = "update_check"
    DEPLOY = "deploy"
    UPDATE_MOD = "update_mod"
    API_VALIDATION = "api_validation"
    RATE_LIMIT_CHECK = "rate_limit_check"


class TaskStatus(Enum):
    """Status of background tasks"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Represents a background task"""
    task_id: str
    task_type: TaskType
    description: str
    thread: threading.Thread
    status: TaskStatus = TaskStatus.RUNNING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    progress: float = 0.0
    can_cancel: bool = True
    cancel_callback: Optional[Callable] = None
    
    @property
    def duration(self) -> float:
        """Get task duration in seconds"""
        end = self.end_time or time.time()
        return end - self.start_time
    
    @property
    def is_running(self) -> bool:
        """Check if task is still running"""
        return self.status == TaskStatus.RUNNING and self.thread.is_alive()


class ThreadManager:
    """Centralized manager for background threads and tasks"""
    
    def __init__(self):
        self._tasks: Dict[str, BackgroundTask] = {}
        self._task_counter = 0
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        
    def create_task(self, 
                   task_type: TaskType, 
                   description: str,
                   target: Callable,
                   args: tuple = (),
                   kwargs: dict = None,
                   can_cancel: bool = True,
                   cancel_callback: Optional[Callable] = None) -> str:
        """
        Create and start a new background task.
        
        Args:
            task_type: Type of task
            description: Human-readable description
            target: Function to run in background
            args: Arguments for target function
            kwargs: Keyword arguments for target function
            can_cancel: Whether task can be cancelled
            cancel_callback: Function to call when task is cancelled
            
        Returns:
            Task ID string
        """
        with self._lock:
            self._task_counter += 1
            task_id = f"{task_type.value}_{self._task_counter}"
            
            # Wrap the target function to handle completion
            def wrapped_target():
                try:
                    if kwargs:
                        target(*args, **kwargs)
                    else:
                        target(*args)
                    self._mark_task_completed(task_id, TaskStatus.COMPLETED)
                except Exception as e:
                    self._mark_task_completed(task_id, TaskStatus.FAILED)
                    print(f"Task {task_id} failed: {e}")
            
            # Create thread (not daemon - we want to track them)
            thread = threading.Thread(
                target=wrapped_target,
                name=f"Task-{task_id}",
                daemon=False
            )
            
            # Create task record
            task = BackgroundTask(
                task_id=task_id,
                task_type=task_type,
                description=description,
                thread=thread,
                can_cancel=can_cancel,
                cancel_callback=cancel_callback
            )
            
            self._tasks[task_id] = task
            
            # Start the thread
            thread.start()
            
            return task_id
    
    def _mark_task_completed(self, task_id: str, status: TaskStatus):
        """Mark a task as completed or failed"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = status
                self._tasks[task_id].end_time = time.time()
    
    def update_task_progress(self, task_id: str, progress: float):
        """Update task progress (0.0 to 1.0)"""
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].progress = min(max(progress, 0.0), 1.0)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a specific task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if task was cancelled, False if it couldn't be cancelled
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            
            if not task.can_cancel or not task.is_running:
                return False
            
            # Call cancel callback if provided
            if task.cancel_callback:
                try:
                    task.cancel_callback()
                except Exception as e:
                    print(f"Error calling cancel callback for task {task_id}: {e}")
            
            # Mark as cancelled
            task.status = TaskStatus.CANCELLED
            task.end_time = time.time()
            
            # Note: We can't actually stop the thread forcibly in Python
            # The thread function should check for cancellation regularly
            
            return True
    
    def get_running_tasks(self) -> List[BackgroundTask]:
        """Get list of currently running tasks"""
        with self._lock:
            return [task for task in self._tasks.values() if task.is_running]
    
    def get_all_tasks(self) -> List[BackgroundTask]:
        """Get list of all tasks"""
        with self._lock:
            return list(self._tasks.values())
    
    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get specific task by ID"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def cleanup_completed_tasks(self, max_age_seconds: float = 3600):
        """Remove completed tasks older than specified age"""
        with self._lock:
            current_time = time.time()
            to_remove = []
            
            for task_id, task in self._tasks.items():
                if (task.status != TaskStatus.RUNNING and 
                    task.end_time and 
                    current_time - task.end_time > max_age_seconds):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
    
    def has_running_tasks(self) -> bool:
        """Check if there are any running tasks"""
        return len(self.get_running_tasks()) > 0
    
    def wait_for_all_tasks(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all tasks to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if all tasks completed, False if timeout occurred
        """
        start_time = time.time()
        
        while self.has_running_tasks():
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)
        
        return True
    
    def cancel_all_tasks(self) -> int:
        """
        Cancel all running tasks.
        
        Returns:
            Number of tasks that were cancelled
        """
        running_tasks = self.get_running_tasks()
        cancelled_count = 0
        
        for task in running_tasks:
            if self.cancel_task(task.task_id):
                cancelled_count += 1
        
        return cancelled_count
    
    def get_task_summary(self) -> Dict[str, int]:
        """Get summary of task counts by status"""
        with self._lock:
            summary = {
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0
            }
            
            for task in self._tasks.values():
                if task.is_running:
                    summary["running"] += 1
                elif task.status == TaskStatus.COMPLETED:
                    summary["completed"] += 1
                elif task.status == TaskStatus.FAILED:
                    summary["failed"] += 1
                elif task.status == TaskStatus.CANCELLED:
                    summary["cancelled"] += 1
            
            return summary
    
    def shutdown(self, timeout: float = 10.0) -> bool:
        """
        Gracefully shutdown all tasks.
        
        Args:
            timeout: Maximum time to wait for tasks to complete
            
        Returns:
            True if all tasks completed gracefully, False if forced shutdown
        """
        self._shutdown_event.set()
        
        # First, try to cancel all tasks
        cancelled_count = self.cancel_all_tasks()
        print(f"Cancelled {cancelled_count} background tasks")
        
        # Wait for tasks to complete
        if self.wait_for_all_tasks(timeout):
            print("All background tasks completed gracefully")
            return True
        else:
            print(f"Some tasks didn't complete within {timeout} seconds")
            # Force completion by marking remaining tasks as cancelled
            running_tasks = self.get_running_tasks()
            for task in running_tasks:
                task.status = TaskStatus.CANCELLED
                task.end_time = time.time()
            return False


# Global thread manager instance
_thread_manager = None

def get_thread_manager() -> ThreadManager:
    """Get the global thread manager instance"""
    global _thread_manager
    if _thread_manager is None:
        _thread_manager = ThreadManager()
    return _thread_manager