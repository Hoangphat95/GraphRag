import os
from dotenv import load_dotenv
from google import genai
import time
from infra import metrics_prometheus as metrics
try:
    from opentelemetry import trace as ot_trace
except Exception:
    ot_trace = None

load_dotenv()


class LLMClient:
    def __init__(self, model_name=None, temperature=0.0, max_retries=2):
        api_key = os.getenv("GEMINI_API_KEY")
        mock_flag = os.getenv("LLM_MOCK", "0").strip().lower() in ("1", "true", "yes", "on")

        # Only mock when explicitly requested; otherwise use Gemini when an API key exists.
        if mock_flag or not api_key:
            self.client = None
            self._mock = True
        else:
            self.client = genai.Client(api_key=api_key)
            self._mock = False

        # 🔥 cho phép chọn model linh hoạt
        # Use a currently available model by default
        self.model = model_name or "models/gemini-3.1-flash-lite"
        # fallback candidates if the chosen model is not available
        self._fallback_models = [
            "models/gemini-3.5-flash",
            "models/gemini-3.1-flash-lite",
            "models/gemini-2.5-flash",
        ]

        self.temperature = temperature
        self.max_retries = max_retries

    def chat(self, prompt: str):

        if not prompt or len(prompt.strip()) == 0:
            print("⚠️ Empty prompt → skip LLM")
            return ""
        start = time.time()
        if self._mock:
            # lightweight deterministic mock for tests
            resp = "MOCK_RESPONSE"
            try:
                if metrics.llm_call_counter is not None:
                    metrics.llm_call_counter.labels(success="true").inc()
                if metrics.llm_latency is not None:
                    metrics.llm_latency.observe(round(time.time() - start, 3))
            except Exception:
                pass
            # trace mock call
            if ot_trace is not None:
                try:
                    tracer = ot_trace.get_tracer(__name__)
                    with tracer.start_as_current_span('llm.call', attributes={'llm.mock': True, 'model': self.model}):
                        pass
                except Exception:
                    pass
            return resp

        # Try the configured model and then fallback candidates if generation fails
        models_to_try = [self.model] + [m for m in self._fallback_models if m != self.model]
        for attempt in range(self.max_retries):
            for model_candidate in models_to_try:
                try:
                    if ot_trace is not None:
                        tracer = ot_trace.get_tracer(__name__)
                        import hashlib
                        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()[:12]
                        attrs = {
                            'llm.model': model_candidate,
                            'llm.prompt.hash': prompt_hash,
                            'llm.prompt.length': len(prompt),
                            'attempt': attempt,
                        }
                        with tracer.start_as_current_span('llm.call', attributes=attrs) as span:
                            response = self.client.models.generate_content(
                                model=model_candidate,
                                contents=prompt
                            )
                    else:
                        response = self.client.models.generate_content(
                            model=model_candidate,
                            contents=prompt
                        )

                    # handle missing/empty response
                    if not response or not hasattr(response, "text") or not getattr(response, 'text', '').strip():
                        # try next candidate
                        continue

                    resp_text = response.text.strip()
                    try:
                        if metrics.llm_call_counter is not None:
                            metrics.llm_call_counter.labels(success="true").inc()
                        if metrics.llm_latency is not None:
                            metrics.llm_latency.observe(round(time.time() - start, 3))
                    except Exception:
                        pass
                    if ot_trace is not None:
                        try:
                            tracer = ot_trace.get_tracer(__name__)
                            span = tracer.get_current_span()
                            if span is not None:
                                span.set_attribute('llm.success', True)
                        except Exception:
                            pass
                    return resp_text

                except Exception as e:
                    # If a model is not found, try next candidate; only log final errors
                    msg = str(e)
                    if attempt == self.max_retries - 1 and model_candidate == models_to_try[-1]:
                        print(f"❌ Gemini error (final):", e)
                    # record exception on trace if available
                    if ot_trace is not None:
                        try:
                            tracer = ot_trace.get_tracer(__name__)
                            span = tracer.get_current_span()
                            if span is not None:
                                span.record_exception(e)
                                span.set_attribute('llm.success', False)
                        except Exception:
                            pass
                    # continue to next model candidate
                    continue

            # simple backoff between attempts
            time.sleep(2 * (attempt + 1))

        # ❌ fail toàn bộ
        try:
            if metrics.llm_call_counter is not None:
                metrics.llm_call_counter.labels(success="false").inc()
            if metrics.llm_latency is not None:
                metrics.llm_latency.observe(round(time.time() - start, 3))
        except Exception:
            pass
        return ""