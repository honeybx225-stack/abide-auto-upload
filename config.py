import os

CONTENT_ROOT = "/Users/changchuping/Downloads/耶穌音樂/耶穌爵士"
DB_PATH = os.path.join(os.path.dirname(__file__), "abide.db")
POST_HOUR = 8
POST_MINUTE = 30
TIMEZONE = "Asia/Taipei"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Meta Graph API (填入後 Phase 2 才會啟動)
META_PAGE_ID = os.environ.get("META_PAGE_ID", "")
META_IG_ID = os.environ.get("META_IG_ID", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
