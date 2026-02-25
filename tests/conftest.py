"""
Pytest configuration and fixtures for GUI and core functionality tests
"""
import pytest
import sys
import threading
import time


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "gui: mark test as GUI test (can hang if not careful)"
    )
    config.addinivalue_line(
        "markers", "live: mark test as live download test (requires network)"
    )


@pytest.fixture(autouse=True)
def cleanup_gui_threads():
    """Ensure GUI threads are properly cleaned up after each test"""
    initial_threads = set(threading.enumerate())
    yield
    # Give a moment for cleanup
    time.sleep(0.1)
    # Kill any remaining daemon threads (but don't wait forever)
    final_threads = set(threading.enumerate()) - initial_threads
    for thread in final_threads:
        if thread.daemon:
            thread.join(timeout=0.5)


@pytest.fixture
def tk_cleanup():
    """Fixture to properly clean up Tkinter windows after test"""
    windows = []
    
    def register_window(window):
        windows.append(window)
        return window
    
    yield register_window
    
    # Cleanup all registered windows
    for window in windows:
        try:
            if hasattr(window, 'app'):
                # It's a MainWindow instance
                if hasattr(window.app, 'quit'):
                    try:
                        window.app.quit()
                    except:
                        pass
                if hasattr(window.app, 'destroy'):
                    try:
                        window.app.destroy()
                    except:
                        pass
            elif hasattr(window, 'quit'):
                # It's a Tk instance directly
                try:
                    window.quit()
                except:
                    pass
                try:
                    window.destroy()
                except:
                    pass
        except Exception:
            pass
        time.sleep(0.05)
