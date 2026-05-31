"""Route registration for the voicebox API."""

from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    """Include the retained domain routers on the application."""
    from .audio import router as audio_router
    from .audio_library import router as audio_library_router
    from .channels import router as channels_router
    from .cuda import router as cuda_router
    from .effects import router as effects_router
    from .generations import router as generations_router
    from .health import router as health_router
    from .history import router as history_router
    from .models import router as models_router
    from .profiles import router as profiles_router
    from .settings import router as settings_router
    from .stories import router as stories_router
    from .tasks import router as tasks_router

    app.include_router(health_router)
    app.include_router(profiles_router)
    app.include_router(channels_router)
    app.include_router(generations_router)
    app.include_router(history_router)
    app.include_router(stories_router)
    app.include_router(effects_router)
    app.include_router(audio_router)
    app.include_router(audio_library_router)
    app.include_router(models_router)
    app.include_router(settings_router)
    app.include_router(tasks_router)
    app.include_router(cuda_router)
