import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from loguru import logger

from weather_api.config import get_settings
from weather_api.services.cache import WeatherDataUnavailable
from weather_api.services.maps import MapLayerError
from weather_api.services.weather import WeatherService
from weather_api.telemetry import configure_logging, record_request, render_metrics

REFRESH_BACKOFF_INITIAL_SECONDS = 1.0
REFRESH_BACKOFF_MAX_SECONDS = 60.0


async def _weather_refresh_loop(service: WeatherService, interval_seconds: float) -> None:
    """Keep the weather cache populated without depending on inbound traffic.

    ``/health/ready`` only reports ready once a refresh has succeeded. Without this
    loop the pod never becomes ready on its own, so it is never added to the Service
    endpoints, so nothing ever calls it -- a startup deadlock that makes every
    rollout time out.
    """
    backoff = REFRESH_BACKOFF_INITIAL_SECONDS
    while True:
        try:
            await service.get_dashboard_weather()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - refresh must never kill the loop
            logger.warning(
                "background weather refresh failed",
                error=str(exc),
                retry_in_seconds=backoff,
            )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, REFRESH_BACKOFF_MAX_SECONDS)
            continue

        backoff = REFRESH_BACKOFF_INITIAL_SECONDS
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("weather-api starting", log_level=settings.log_level)
    service = WeatherService(settings)
    app.state.weather_service = service
    app.state.weather_refresh_task = asyncio.create_task(
        _weather_refresh_loop(service, settings.cache_ttl_seconds)
    )
    yield
    logger.info("weather-api shutting down")
    refresh_task = app.state.weather_refresh_task
    refresh_task.cancel()
    try:
        await refresh_task
    except asyncio.CancelledError:
        pass
    await service.shutdown()


app = FastAPI(title="weather-api", version="0.1.2", lifespan=lifespan)


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


@app.get("/api/v1/maps/tiles/{layer_id}/{z}/{x}/{y}.png")
async def get_map_tile(request: Request, layer_id: str, z: int, x: int, y: int):
    service = _get_service(request)
    try:
        tile_payload, content_type = await service.get_map_tile(layer_id=layer_id, z=z, x=x, y=y)
    except MapLayerError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": "map_layer_error", "message": str(error)},
        ) from error
    return Response(
        content=tile_payload,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=300"},
    )


@app.get("/api/v1/maps/fires")
async def get_map_fires(request: Request):
    service = _get_service(request)
    try:
        return await service.get_fires_overlay()
    except MapLayerError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": "map_layer_error", "message": str(error)},
        ) from error


@app.get("/api/v1/maps/air-quality")
async def get_map_air_quality(request: Request):
    service = _get_service(request)
    try:
        return await service.get_air_quality_overlay()
    except MapLayerError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": "map_layer_error", "message": str(error)},
        ) from error


@app.get("/api/v1/maps/observations/{metric}")
async def get_map_observations(request: Request, metric: str):
    if metric not in {"temperature", "wind"}:
        raise HTTPException(
            status_code=404,
            detail={"code": "map_layer_error", "message": f"Unknown observation metric: {metric}"},
        )

    service = _get_service(request)
    observation_metric = "temperature" if metric == "temperature" else "wind"
    try:
        return await service.get_observation_overlay(observation_metric)
    except MapLayerError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": "map_layer_error", "message": str(error)},
        ) from error
