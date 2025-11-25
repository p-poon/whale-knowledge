"""LLM service for content generation using Anthropic Claude and OpenAI."""

import asyncio
from typing import Optional, Dict, Any, AsyncIterator
from enum import Enum
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMService:
    """Service for interacting with LLM APIs."""

    def __init__(self):
        """Initialize LLM service."""
        self._anthropic_client = None
        self._openai_client = None

    def _get_anthropic_client(self):
        """Get or create Anthropic client."""
        if self._anthropic_client is None:
            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            try:
                from anthropic import AsyncAnthropic
                self._anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        return self._anthropic_client

    def _get_openai_client(self):
        """Get or create OpenAI client."""
        if self._openai_client is None:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")
        return self._openai_client

    def get_default_model(self, provider: str) -> str:
        """Get default model for a provider."""
        if provider == LLMProvider.ANTHROPIC:
            return settings.anthropic_default_model
        elif provider == LLMProvider.OPENAI:
            return settings.openai_default_model
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate(
        self,
        prompt: str,
        provider: str = "anthropic",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using specified LLM provider.

        Args:
            prompt: The prompt to send to the LLM
            provider: 'anthropic' or 'openai'
            model: Model name (if None, uses default for provider)
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with:
                - content: Generated text
                - model: Model used
                - usage: Token usage dict
                - provider: Provider used
        """
        if model is None:
            model = self.get_default_model(provider)

        try:
            if provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic(
                    prompt, model, system_prompt, temperature, max_tokens, **kwargs
                )
            elif provider == LLMProvider.OPENAI:
                return await self._generate_openai(
                    prompt, model, system_prompt, temperature, max_tokens, **kwargs
                )
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.error(f"LLM generation failed for {provider}/{model}: {str(e)}")
            raise

    async def _generate_anthropic(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using Anthropic Claude."""
        client = self._get_anthropic_client()

        messages = [{"role": "user", "content": prompt}]

        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        # Add any additional kwargs
        request_params.update(kwargs)

        response = await client.messages.create(**request_params)

        return {
            "content": response.content[0].text,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            "provider": "anthropic",
            "stop_reason": response.stop_reason,
        }

    async def _generate_openai(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using OpenAI."""
        client = self._get_openai_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add any additional kwargs
        request_params.update(kwargs)

        response = await client.chat.completions.create(**request_params)

        choice = response.choices[0]

        return {
            "content": choice.message.content,
            "model": response.model,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "provider": "openai",
            "stop_reason": choice.finish_reason,
        }

    async def stream_generate(
        self,
        prompt: str,
        provider: str = "anthropic",
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream text generation using specified LLM provider.

        Args:
            Same as generate()

        Yields:
            Dict with:
                - type: 'content' | 'usage' | 'done'
                - content: Text chunk (if type='content')
                - usage: Token usage (if type='usage')
                - model: Model used (if type='done')
        """
        if model is None:
            model = self.get_default_model(provider)

        try:
            if provider == LLMProvider.ANTHROPIC:
                async for chunk in self._stream_anthropic(
                    prompt, model, system_prompt, temperature, max_tokens, **kwargs
                ):
                    yield chunk
            elif provider == LLMProvider.OPENAI:
                async for chunk in self._stream_openai(
                    prompt, model, system_prompt, temperature, max_tokens, **kwargs
                ):
                    yield chunk
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        except Exception as e:
            logger.error(f"LLM streaming failed for {provider}/{model}: {str(e)}")
            raise

    async def _stream_anthropic(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream text generation using Anthropic Claude."""
        client = self._get_anthropic_client()

        messages = [{"role": "user", "content": prompt}]

        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if system_prompt:
            request_params["system"] = system_prompt

        request_params.update(kwargs)

        async with client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                yield {
                    "type": "content",
                    "content": text,
                }

            # Get final message with usage
            message = await stream.get_final_message()
            yield {
                "type": "usage",
                "usage": {
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                    "total_tokens": message.usage.input_tokens + message.usage.output_tokens,
                },
            }

            yield {
                "type": "done",
                "model": message.model,
                "provider": "anthropic",
            }

    async def _stream_openai(
        self,
        prompt: str,
        model: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream text generation using OpenAI."""
        client = self._get_openai_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        request_params = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        request_params.update(kwargs)

        stream = await client.chat.completions.create(**request_params)

        total_tokens = 0
        async for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield {
                        "type": "content",
                        "content": delta.content,
                    }

            # Track usage if available
            if hasattr(chunk, 'usage') and chunk.usage:
                yield {
                    "type": "usage",
                    "usage": {
                        "input_tokens": chunk.usage.prompt_tokens,
                        "output_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    },
                }

        yield {
            "type": "done",
            "model": model,
            "provider": "openai",
        }

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        provider: str,
        model: str
    ) -> float:
        """
        Estimate cost for LLM usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            provider: LLM provider
            model: Model name

        Returns:
            Estimated cost in USD
        """
        # Convert to millions
        input_m = input_tokens / 1_000_000
        output_m = output_tokens / 1_000_000

        if provider == "anthropic":
            if "claude-3-5-sonnet" in model or "claude-3.5-sonnet" in model:
                input_cost = settings.anthropic_claude_35_sonnet_input_cost
                output_cost = settings.anthropic_claude_35_sonnet_output_cost
            else:
                # Default to Claude 3.5 Sonnet pricing
                input_cost = settings.anthropic_claude_35_sonnet_input_cost
                output_cost = settings.anthropic_claude_35_sonnet_output_cost

        elif provider == "openai":
            if "gpt-4" in model and "turbo" in model:
                input_cost = settings.openai_gpt4_turbo_input_cost
                output_cost = settings.openai_gpt4_turbo_output_cost
            elif "gpt-3.5" in model:
                input_cost = settings.openai_gpt35_turbo_input_cost
                output_cost = settings.openai_gpt35_turbo_output_cost
            else:
                # Default to GPT-4 Turbo pricing (conservative estimate)
                input_cost = settings.openai_gpt4_turbo_input_cost
                output_cost = settings.openai_gpt4_turbo_output_cost
        else:
            logger.warning(f"Unknown provider {provider}, returning 0 cost")
            return 0.0

        total_cost = (input_m * input_cost) + (output_m * output_cost)
        return round(total_cost, 6)


# Global instance
llm_service = LLMService()
