import os
import tempfile
import threading
import time
import pytest
from mimecast_sdk.file_utils import FileManager, FileLockException


@pytest.fixture
def temp_file():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


def test_atomic_write(temp_file):
    manager = FileManager(temp_file)
    test_data = "test content"
    manager.atomic_write(test_data)
    
    with open(temp_file, 'r') as f:
        assert f.read() == test_data


def test_atomic_write_binary(temp_file):
    manager = FileManager(temp_file)
    test_data = b"binary content"
    manager.atomic_write(test_data, binary=True)
    
    with open(temp_file, 'rb') as f:
        assert f.read() == test_data


def test_atomic_update(temp_file):
    manager = FileManager(temp_file)
    
    with manager.atomic_update() as f:
        f.write("test content")
    
    with open(temp_file, 'r') as f:
        assert f.read() == "test content"


def test_safe_read(temp_file):
    test_data = "test content"
    with open(temp_file, 'w') as f:
        f.write(test_data)
    
    manager = FileManager(temp_file)
    assert manager.safe_read() == test_data


def test_safe_read_binary(temp_file):
    test_data = b"binary content"
    with open(temp_file, 'wb') as f:
        f.write(test_data)
    
    manager = FileManager(temp_file)
    assert manager.safe_read(binary=True) == test_data


def test_file_lock_blocking(temp_file):
    manager = FileManager(temp_file)
    lock_acquired = threading.Event()
    lock_released = threading.Event()
    
    def lock_file():
        with manager.lock():
            lock_acquired.set()
            time.sleep(0.5)  # Hold the lock for a bit
        lock_released.set()
    
    thread = threading.Thread(target=lock_file)
    thread.start()
    
    # Wait for the lock to be acquired
    lock_acquired.wait()
    
    # Try to acquire the lock (should block)
    with pytest.raises(FileLockException):
        with manager.lock(blocking=False):
            pass
    
    # Wait for the lock to be released
    lock_released.wait()
    thread.join()
    
    # Now we should be able to acquire the lock
    with manager.lock(blocking=False):
        pass


def test_file_lock_timeout(temp_file):
    manager = FileManager(temp_file)
    lock_acquired = threading.Event()
    
    def lock_file():
        with manager.lock():
            lock_acquired.set()
            time.sleep(1)  # Hold the lock longer than the timeout
    
    thread = threading.Thread(target=lock_file)
    thread.start()
    
    # Wait for the lock to be acquired
    lock_acquired.wait()
    
    # Try to acquire the lock with timeout
    start_time = time.time()
    with pytest.raises(FileLockException):
        with manager.lock(timeout=0.5):
            pass
    elapsed_time = time.time() - start_time
    
    assert 0.4 <= elapsed_time <= 0.6  # Check if timeout was respected
    thread.join()


def test_safe_copy(temp_file):
    manager = FileManager(temp_file)
    test_data = "test content"
    manager.atomic_write(test_data)
    
    # Create temporary destination file
    dst_fd, dst_path = tempfile.mkstemp()
    os.close(dst_fd)
    
    try:
        manager.safe_copy(dst_path)
        
        with open(dst_path, 'r') as f:
            assert f.read() == test_data
    finally:
        try:
            os.unlink(dst_path)
        except OSError:
            pass