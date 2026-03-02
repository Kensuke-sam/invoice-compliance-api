from __future__ import annotations

import json
from typing import Any

import httpx

from app import models
from app.core.config import get_settings
from app.core.errors import ExternalServiceError
from app.schemas import InvoiceReviewDraft


class OpenAIJsonGateway:
    def __init__(self, *, api_key: str, base_url: str, model: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalServiceError("AI provider request failed.") from exc

        body = response.json()
        if not isinstance(body, dict):
            raise ExternalServiceError("AI provider returned an invalid response body.")
        choices = body.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ExternalServiceError("AI provider returned no choices.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ExternalServiceError("AI provider returned an invalid choice payload.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise ExternalServiceError("AI provider returned an invalid message payload.")
        content = message.get("content")
        if not isinstance(content, str):
            raise ExternalServiceError("AI provider returned an unsupported payload.")

        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise ExternalServiceError("AI provider returned non-JSON content.")

        try:
            parsed = json.loads(content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ExternalServiceError("AI provider returned invalid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ExternalServiceError("AI provider returned a non-object JSON payload.")
        return parsed


class InvoiceAiService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.gateway = self._build_gateway()

    def _build_gateway(self) -> OpenAIJsonGateway | None:
        if self.settings.ai_provider == "mock":
            return None
        if self.settings.ai_provider != "openai":
            raise ExternalServiceError("Unsupported AI provider.")
        if not self.settings.openai_api_key:
            raise ExternalServiceError("OPENAI_API_KEY is not configured.")
        return OpenAIJsonGateway(
            api_key=self.settings.openai_api_key,
            base_url=self.settings.openai_base_url,
            model=self.settings.openai_model,
            timeout_seconds=self.settings.ai_timeout_seconds,
        )

    def generate(self, invoice: models.InvoiceRecord) -> InvoiceReviewDraft:
        if self.gateway is None:
            return self._mock(invoice)

        system_prompt = (
            "You are supporting Invoice Compliance API. "
            "Return only JSON that matches the requested schema."
        )
        user_prompt = "\n".join(
            [
                "Goal: 経理が目視する前に高リスク請求を先に見つける",
                "Output fields:",
                (
                    "- risk_level: Review risk level\n"
                    "- flags: Compliance flags\n"
                    "- reviewer_note: Reviewer note\n"
                    "- approval_hint: Suggested next step"
                ),
                "",
                "Record:",
                *self._render_record(invoice),
            ],
        )
        payload = self.gateway.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
        return InvoiceReviewDraft.model_validate(payload)

    def _render_record(self, invoice: models.InvoiceRecord) -> list[str]:
        return [
            "vendor_name: " + str(invoice.vendor_name),
            "invoice_number: " + str(invoice.invoice_number),
            "currency: " + str(invoice.currency),
            "total_amount: " + str(invoice.total_amount),
            "line_items: " + str(json.dumps(invoice.line_items, ensure_ascii=False)),
        ]

    def _mock(self, invoice: models.InvoiceRecord) -> InvoiceReviewDraft:
        flags = ["High total amount"] if invoice.total_amount >= 100000 else ["Routine amount"]
        approval_hint = (
            "needs_manual_review" if invoice.total_amount >= 100000 else "auto_approve_candidate"
        )
        return InvoiceReviewDraft(
            risk_level="medium" if invoice.total_amount >= 100000 else "low",
            flags=flags,
            reviewer_note="Verify the purchase order reference and confirm any surcharge before approval.",
            approval_hint=approval_hint,
        )
