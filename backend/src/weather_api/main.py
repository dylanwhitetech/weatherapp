import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from weather_api.config import get_settings
from weather_api.services.cache import WeatherDataUnavailable
from weather_api.services.weather import WeatherService
from weather_api.telemetry import record_request, render_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.weather_service = WeatherService(settings)
    yield
    await app.state.weather_service.shutdown()


app = FastAPI(title="weather-api", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_seconds = time.perf_counter() - started
        record_request(
            route=request.url.path,
            method=request.method,
            status_code=500,
            duration_seconds=duration_seconds,
        )
        raise

    record_request(
        route=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_seconds=time.perf_counter() - started,
    )
    return response


def _get_service(request: Request) -> WeatherService:
    return request.app.state.weather_service


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready(request: Request) -> JSONResponse:
    service = _get_service(request)
    ready, message = service.ready_status()
    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if ready else "not_ready", "message": message},
    )


@app.get("/metrics")
async def metrics() -> Response:
    payload, content_type = render_metrics()
    return Response(content=payload, media_type=content_type)


@app.get("/api/v1/weather")
async def get_weather(request: Request):
    service = _get_service(request)
    try:
        return await service.get_dashboard_weather()
    except WeatherDataUnavailable as error:
        raise HTTPException(
            status_code=503,
            detail={"code": "weather_unavailable", "message": str(error)},
        ) from error


@app.get("/api/v1/current")
async def get_current(request: Request):
    weather = await get_weather(request)
    return weather.current


@app.get("/api/v1/hourly")
async def get_hourly(request: Request, hours: int = 24):
    weather = await get_weather(request)
    clamped_hours = max(1, min(48, hours))
    return {"hourly": weather.hourly[:clamped_hours]}


@app.get("/api/v1/forecast")
async def get_forecast(request: Request):
    weather = await get_weather(request)
    return {"daily": weather.daily}


@app.get("/api/v1/alerts")
async def get_alerts(request: Request):
    weather = await get_weather(request)
    return {"alerts": weather.alerts}


@app.get("/api/v1/recommendations")
async def get_recommendations(request: Request):
    weather = await get_weather(request)
    return weather.recommendations
