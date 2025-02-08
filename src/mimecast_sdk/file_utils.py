import os
import fcntl
import errno
import tempfile
from contextlib import contextmanager
from typing import Optional, Union, BinaryIO, TextIO, Any
import shutil


class FileLockException(Exception):
    """Exception raised when file locking fails."""
    pass


class FileManager:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self._lock_file = f"{self.path}.lock"

    @contextmanager
    def lock(self, blocking: bool = True, timeout: Optional[float] = None) -> None:
        """
        Context manager for file locking.
        
        Args:
            blocking: If True, wait for lock to be acquired. If False, raise FileLockException if lock cannot be acquired.
            timeout: Maximum time to wait for lock acquisition in seconds. None means wait indefinitely.
        
        Raises:
            FileLockException: If lock cannot be acquired
        """
        lock_file = None
        try:
            lock_file = open(self._lock_file, 'w')
            
            # Set appropriate flags based on blocking mode
            flags = fcntl.LOCK_EX
            if not blocking:
                flags |= fcntl.LOCK_NB
                
            if timeout is not None and timeout > 0:
                import time
                end_time = time.time() + timeout
                while True:
                    try:
                        fcntl.flock(lock_file.fileno(), flags)
                        break
                    except (IOError, OSError) as e:
                        if e.errno != errno.EAGAIN:
                            raise
                        if time.time() > end_time:
                            raise FileLockException("Timeout waiting for file lock")
                        time.sleep(0.1)
            else:
                try:
                    fcntl.flock(lock_file.fileno(), flags)
                except (IOError, OSError) as e:
                    if e.errno == errno.EAGAIN:
                        raise FileLockException("File is locked by another process")
                    raise
                    
            yield
            
        finally:
            if lock_file is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
                try:
                    os.unlink(self._lock_file)
                except OSError:
                    pass

    def atomic_write(self, data: Union[str, bytes], binary: bool = False, **kwargs: Any) -> None:
        """
        Write data atomically to the file.
        
        Args:
            data: Content to write to the file
            binary: If True, write in binary mode
            **kwargs: Additional arguments to pass to open()
        """
        mode = 'wb' if binary else 'w'
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(self.path))
        
        try:
            with os.fdopen(tmp_fd, mode) as tmp_file:
                if isinstance(data, str) and binary:
                    data = data.encode()
                tmp_file.write(data)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                
            # Atomic rename
            os.replace(tmp_path, self.path)
            
        except:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    @contextmanager
    def atomic_update(self, binary: bool = False, **kwargs: Any) -> Union[TextIO, BinaryIO]:
        """
        Context manager for atomic file updates.
        
        Args:
            binary: If True, open in binary mode
            **kwargs: Additional arguments to pass to open()
            
        Yields:
            A file object that can be used to write the updates
        """
        mode = 'wb' if binary else 'w'
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(self.path))
        tmp_file = None
        
        try:
            tmp_file = os.fdopen(tmp_fd, mode)
            yield tmp_file
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            tmp_file.close()
            tmp_file = None
            
            # Atomic rename
            os.replace(tmp_path, self.path)
            
        finally:
            if tmp_file is not None:
                tmp_file.close()
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def safe_read(self, binary: bool = False, **kwargs: Any) -> Union[str, bytes]:
        """
        Safely read file contents with locking.
        
        Args:
            binary: If True, read in binary mode
            **kwargs: Additional arguments to pass to open()
            
        Returns:
            File contents as string or bytes
        """
        mode = 'rb' if binary else 'r'
        with self.lock():
            with open(self.path, mode, **kwargs) as f:
                return f.read()

    def safe_copy(self, dst_path: str) -> None:
        """
        Safely copy file with locking.
        
        Args:
            dst_path: Destination path
        """
        with self.lock():
            shutil.copy2(self.path, dst_path)