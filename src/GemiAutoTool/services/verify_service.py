"""Client wrapper for SheerIDBot verification API v2."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from GemiAutoTool.exceptions import VerifyServiceError


VerifyProgressCallback = Callable[[dict[str, Any]], None]


class SheerIDBotVerifyService:
    """Submit and poll SheerID verification jobs."""

    TERMINAL_STATUSES = {
        "success",
        "failed",
        "rejected",
        "stale",
        "cancelled",
        "invalid_link",
    }

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://sheeridbot.com/api/v2",
        timeout_seconds: float = 20.0,
        poll_interval_seconds: float = 2.0,
        poll_timeout_seconds: float = 600.0,
    ) -> None:
        key = str(api_key or "").strip()
        if not key:
            raise VerifyServiceError("API Key 不能为空。")

        self._api_key = key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = float(timeout_seconds)
        self._poll_interval_seconds = max(0.2, float(poll_interval_seconds))
        self._poll_timeout_seconds = max(5.0, float(poll_timeout_seconds))
        self._session = requests.Session()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    @classmethod
    def is_terminal_status(cls, status: object) -> bool:
        return str(status or "").strip().lower() in cls.TERMINAL_STATUSES

    def submit_verify(self, url: str) -> dict[str, Any]:
        target_url = str(url or "").strip()
        if not target_url:
            raise VerifyServiceError("SheerID 链接不能为空。")

        resp = self._session.post(
            f"{self._base_url}/verify",
            headers=self.headers,
            json={"url": target_url},
            timeout=self._timeout_seconds,
        )
        data = self._decode_response_json(resp)
        self._raise_for_error_status(resp, data)

        job_id = str(data.get("job_id", "")).strip()
        if not job_id:
            raise VerifyServiceError("验证提交成功但返回中缺少 job_id。")
        return data

    def get_verify_status(self, job_id: str) -> dict[str, Any]:
        resolved_job_id = str(job_id or "").strip()
        if not resolved_job_id:
            raise VerifyServiceError("job_id 不能为空。")

        resp = self._session.get(
            f"{self._base_url}/verify/{resolved_job_id}",
            headers=self.headers,
            timeout=self._timeout_seconds,
        )
        data = self._decode_response_json(resp)
        self._raise_for_error_status(resp, data)
        return data

    def submit_and_poll(
        self,
        url: str,
        *,
        progress_callback: VerifyProgressCallback | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        submit_data = self.submit_verify(url)
        if progress_callback:
            progress_callback(self._build_progress_event("submitted", submit_data))

        job_id = str(submit_data.get("job_id", "")).strip()
        start = time.monotonic()

        while True:
            if should_stop and should_stop():
                raise VerifyServiceError("验证轮询已取消。")

            status_data = self.get_verify_status(job_id)
            if progress_callback:
                progress_callback(self._build_progress_event("polled", status_data))

            if self.is_terminal_status(status_data.get("status")):
                return submit_data, status_data

            if (time.monotonic() - start) >= self._poll_timeout_seconds:
                raise VerifyServiceError("验证轮询超时，请稍后在结果页重试。")

            time.sleep(self._poll_interval_seconds)

    @staticmethod
    def _build_progress_event(event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        progress = data.get("progress")
        if not isinstance(progress, dict):
            progress = {}
        return {
            "event_type": event_type,
            "job_id": str(data.get("job_id", "") or ""),
            "status": str(data.get("status", "") or ""),
            "progress": progress,
            "credits_charged": data.get("credits_charged"),
            "result": data.get("result"),
            "raw": data,
        }

    @staticmethod
    def _decode_response_json(resp: requests.Response) -> dict[str, Any]:
        try:
            data = resp.json()
        except Exception as e:
            raise VerifyServiceError(f"验证服务返回非 JSON 响应 (HTTP {resp.status_code})") from e
        if not isinstance(data, dict):
            raise VerifyServiceError(f"验证服务返回格式异常 (HTTP {resp.status_code})")
        return data

    @staticmethod
    def _raise_for_error_status(resp: requests.Response, data: dict[str, Any]) -> None:
        if 200 <= resp.status_code < 300:
            return

        error_obj = data.get("error")
        if isinstance(error_obj, dict):
            code = str(error_obj.get("code", "") or "").strip()
            message = str(error_obj.get("message", "") or "").strip()
            if code or message:
                if code and message:
                    raise VerifyServiceError(f"{code}: {message}")
                raise VerifyServiceError(code or message)

        raise VerifyServiceError(f"验证服务请求失败 (HTTP {resp.status_code})")

