import os
import sys

# Make the project root importable from inside test/ (resume.py, analyzer.py,
# databse.py, job_scraper.py, llm.py all live at the project root, not in a package).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))