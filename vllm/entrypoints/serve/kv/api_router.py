# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

from http import HTTPStatus

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from vllm.engine.protocol import EngineClient
from vllm.logger import init_logger

logger = init_logger(__name__)

router = APIRouter()


def engine_client(request: Request) -> EngineClient:
    return request.app.state.engine_client


@router.post("/v1/kv/pin")
async def pin_kv(raw_request: Request) -> JSONResponse:
    """Pin a workflow's KV cache blocks to prevent eviction."""
    body = await raw_request.json()
    workflow_id = body.get("workflow_id")
    if not workflow_id:
        return JSONResponse(
            content={"error": "workflow_id is required"},
            status_code=HTTPStatus.BAD_REQUEST.value,
        )
    try:
        count = await engine_client(raw_request).pin_kv_workflow(workflow_id)
        return JSONResponse(
            content={"workflow_id": workflow_id, "pinned_blocks": count},
        )
    except Exception as err:
        logger.exception("Failed to pin KV workflow %s", workflow_id)
        return JSONResponse(
            content={"error": f"Failed to pin KV workflow: {err}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )


@router.post("/v1/kv/unpin")
async def unpin_kv(raw_request: Request) -> JSONResponse:
    """Unpin a workflow's KV cache blocks."""
    body = await raw_request.json()
    workflow_id = body.get("workflow_id")
    if not workflow_id:
        return JSONResponse(
            content={"error": "workflow_id is required"},
            status_code=HTTPStatus.BAD_REQUEST.value,
        )
    try:
        count = await engine_client(raw_request).unpin_kv_workflow(workflow_id)
        return JSONResponse(
            content={"workflow_id": workflow_id, "unpinned_blocks": count},
        )
    except Exception as err:
        logger.exception("Failed to unpin KV workflow %s", workflow_id)
        return JSONResponse(
            content={"error": f"Failed to unpin KV workflow: {err}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )


@router.post("/v1/kv/evict")
async def evict_kv(raw_request: Request) -> JSONResponse:
    """Force-evict a workflow's KV cache (force recompute on next step)."""
    body = await raw_request.json()
    workflow_id = body.get("workflow_id")
    if not workflow_id:
        return JSONResponse(
            content={"error": "workflow_id is required"},
            status_code=HTTPStatus.BAD_REQUEST.value,
        )
    try:
        count = await engine_client(raw_request).force_evict_kv_workflow(
            workflow_id
        )
        return JSONResponse(
            content={"workflow_id": workflow_id, "evicted_blocks": count},
        )
    except Exception as err:
        logger.exception("Failed to evict KV workflow %s", workflow_id)
        return JSONResponse(
            content={"error": f"Failed to evict KV workflow: {err}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )


@router.get("/v1/kv/stats")
async def kv_stats(raw_request: Request) -> JSONResponse:
    """Return KV cache usage stats as block counts."""
    try:
        stats = await engine_client(raw_request).get_kv_stats()
        return JSONResponse(content=stats)
    except Exception as err:
        logger.exception("Failed to get KV stats")
        return JSONResponse(
            content={"error": f"Failed to get KV stats: {err}"},
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )


def attach_router(app: FastAPI):
    app.include_router(router)
