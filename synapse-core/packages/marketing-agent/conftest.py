"""
Pytest configuration for marketing-agent tests.
Adds the package root to Python path for imports.
"""

import sys
from pathlib import Path

# Add the marketing-agent package directory to the Python path
package_root = Path(__file__).parent
sys.path.insert(0, str(package_root))
