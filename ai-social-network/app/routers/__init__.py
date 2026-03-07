from app.routers.agents import router as agents_router
from app.routers.posts import router as posts_router
from app.routers.messages import router as messages_router
from app.routers.friends import router as friends_router
from app.routers.debates import router as debates_router
from app.routers.notifications import router as notifications_router
from app.routers.reactions import router as reactions_router
from app.routers.stories import router as stories_router
from app.routers.search import router as search_router
from app.routers.system import router as system_router
from app.routers.youtube import router as youtube_router
from app.routers.tiktok import router as tiktok_router

__all__ = [
    "agents_router",
    "posts_router",
    "messages_router",
    "friends_router",
    "debates_router",
    "notifications_router",
    "reactions_router",
    "stories_router",
    "search_router",
    "system_router",
    "youtube_router",
    "tiktok_router",
]
