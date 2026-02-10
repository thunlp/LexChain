import asyncio
import aiohttp
import os
import json
import logging
from dotenv import load_dotenv

class LLMPipeline:
    def __init__(self, model="gpt-3.5-turbo", env_path=".env", opensource=True, log_path="../etd1000.log", cot=False,
                 streaming=False,temperature=0.7):
        # 1. Handle API URL and Key based on opensource flag
        if opensource:
            self.api_url = "http://localhost:8000/v1/chat/completions"
            self.api_key = None
        else:
            if env_path and os.path.exists(env_path):
                load_dotenv(env_path)
                logging.info(f"Loaded environment variables from: {env_path}")
            else:
                logging.warning(f"Failed to load environment file: {env_path}")

            self.api_key = os.getenv("API_KEY")
            url = os.getenv("URL")
            if not url:
                raise ValueError("Environment variable URL not set")
            # Ensure the URL points to the completion endpoint
            self.api_url = url + "/chat/completions"

        self.model = model
        self.total_token_usage = 0
        self.streaming_enabled = streaming
        self.cot = cot
        self.temperature = temperature

        print(f"Loading model: {model}...")

        # 2. Logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json"
        }

        # 3. Concurrency control: limit simultaneous requests to 10
        self.semaphore = asyncio.Semaphore(10)

    async def _fetch(self, session, input_text, max_retries=5):
        # Use semaphore to control concurrency
        async with self.semaphore:
            messages = [{"role": "user", "content": input_text}]

            # Parameter adaptation for reasoning models (o-series)
            is_reasoning_model = self.model.startswith("o")
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": self.streaming_enabled
            }

            if is_reasoning_model:
                payload["max_completion_tokens"] = 4096
                payload["temperature"] = self.temperature
            else:
                payload["max_tokens"] = 4096
                payload["temperature"] = self.temperature

            if self.cot:
                # extra_body is supported by certain backends like vLLM
                payload["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}

            retry_interval = 1
            for attempt in range(max_retries):
                try:
                    timeout = aiohttp.ClientTimeout(total=300)
                    async with session.post(self.api_url, headers=self.headers, json=payload, timeout=timeout) as resp:
                        if resp.status == 200:
                            if self.streaming_enabled:
                                output_text = ""
                                async for line in resp.content:
                                    decoded_line = line.decode("utf-8").strip()
                                    if not decoded_line or decoded_line == "data: [DONE]":
                                        continue
                                    if decoded_line.startswith("data: "):
                                        try:
                                            content = decoded_line.removeprefix("data: ")
                                            parsed = json.loads(content)
                                            delta = parsed["choices"][0].get("delta", {})
                                            if "content" in delta:
                                                output_text += delta["content"]
                                        except json.JSONDecodeError:
                                            continue
                                return output_text
                            else:
                                data = await resp.json()
                                response = data["choices"][0]["message"]["content"]
                                # Update token usage
                                self.total_token_usage += data.get("usage", {}).get("total_tokens", 0)
                                return response

                        elif resp.status in (429, 504, 524):
                            logging.warning(f"Status {resp.status}, retrying #{attempt + 1}...")
                        else:
                            text = await resp.text()
                            logging.error(f"Error {resp.status}: {text}")
                            return "Request failed"

                except Exception as e:
                    logging.error(f"Attempt {attempt + 1} failed: {str(e)}")

                await asyncio.sleep(retry_interval)
                retry_interval *= 2  # Exponential backoff

            return "Request failed"

    async def call_batch_async(self, inputs):
        # Set a longer connection pool limit
        conn = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(connector=conn) as session:
            tasks = [self._fetch(session, text) for text in inputs]
            # Use return_exceptions=True to prevent one failure from stopping the whole batch
            return await asyncio.gather(*tasks, return_exceptions=True)