import unittest
import tempfile
from pathlib import Path

import dropzone


class TestDropzone(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to isolate tests from the real file system."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

        original_dropzone_dir = dropzone.DROPZONE_DIR
        self.addCleanup(setattr, dropzone, "DROPZONE_DIR", original_dropzone_dir)
        dropzone.DROPZONE_DIR = Path(self.test_dir.name)
        self.test_file = dropzone.DROPZONE_DIR / "test_payload.py"

    def test_auto_increment(self):
        """Verify filenames increment properly when duplicates exist."""
        self.test_file.touch()

        new_path_1 = dropzone.get_unique_filename("test_payload.py")
        self.assertEqual(new_path_1.name, "test_payload(1).py")
        new_path_1.touch()

        new_path_2 = dropzone.get_unique_filename("test_payload.py")
        self.assertEqual(new_path_2.name, "test_payload(2).py")

    def test_empty_size(self):
        """Test directory size calculation handles empty files."""
        self.test_file.touch()
        size = dropzone.get_dir_size_mb(dropzone.DROPZONE_DIR)
        self.assertGreaterEqual(size, 0.0)


if __name__ == "__main__":
    unittest.main()
