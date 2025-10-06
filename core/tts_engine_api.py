import io
import wave
import numpy as np
import requests
import json

from .tts_base import TTSBase


class TTSEngineAPI(TTSBase):
    """
    TTS engine that connects to remote TTS-WebUI API.
    Uses direct requests to OpenAI-compatible endpoint.
    """
    def __init__(self, base_url: str = "http://localhost:7778/v1"):
        """
        Initializes the TTS API client.
        """
        self.base_url = base_url.rstrip('/')
        self.speech_endpoint = f"{self.base_url}/audio/speech"
        self.server_root = "http://localhost:7778"

    def generate_speech(
        self,
        text: str,
        model: str,
        voice: str,
        exaggeration: float,
        cfg_weight: float,
        temperature: float,
        seed: int,
        split_chunks: bool,
        halve_first_chunk: bool,
        desired_length: int,
        max_length: int,
        device: str,
        data_type: str,
        use_compilation: bool,
        max_new_tokens: int,
        cache_length: int
    ) -> bytes:
        """
        Generates speech from text using the TTS API.
        (Keep existing implementation)
        """
        print("=" * 60)
        print("Sending request to TTS API...")
        print(f"Endpoint: {self.speech_endpoint}")
        print(f"Model: {model}")
        print(f"Voice: {voice}")
        print(f"Text length: {len(text)} characters")

        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": "wav",
            "speed": 1.0,
            "stream": False,
            
            "params": {
                "exaggeration": exaggeration,
                "cfg_weight": cfg_weight,
                "temperature": temperature,
                "seed": seed if seed != -1 else None,
                "split_prompt": split_chunks,
                "halve_first_chunk": halve_first_chunk,
                "desired_length": desired_length,
                "max_length": max_length,
                "device": device,
                "dtype": data_type,
                "compile": use_compilation,
                "max_new_tokens": max_new_tokens,
                "cache_length": cache_length,
            }
        }

        print("\nRequest payload:")
        print(f"  model: {payload['model']}")
        print(f"  voice: {payload['voice']}")
        print(f"  response_format: {payload['response_format']}")
        print(f"  stream: {payload['stream']}")
        print(f"\n  params:")
        for key, value in payload['params'].items():
            print(f"    {key}: {value}")
        print(f"\nInput text preview: {text[:100]}..." if len(text) > 100 else f"Input text: {text}")
        print("=" * 60)

        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            response = requests.post(
                self.speech_endpoint,
                json=payload,
                headers=headers,
                timeout=None
            )
            
            if response.status_code == 200:
                print(f"\n✓ Audio received successfully! Size: {len(response.content)} bytes")
                return response.content
            else:
                error_msg = f"API returned status code {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f"\nDetails: {json.dumps(error_detail, indent=2)}"
                except:
                    error_msg += f"\nResponse: {response.text[:500]}"
                
                print(f"\n✗ Error: {error_msg}")
                raise Exception(error_msg)
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out. The server at {self.base_url} took too long to respond."
            print(f"\n✗ {error_msg}")
            raise Exception(error_msg)
            
        except requests.exceptions.ConnectionError:
            error_msg = f"Could not connect to server at {self.base_url}. Is the server running?"
            print(f"\n✗ {error_msg}")
            raise Exception(error_msg)
            
        except Exception as e:
            if "Exception" not in str(type(e).__name__):
                error_msg = f"Unexpected error: {str(e)}"
                print(f"\n✗ {error_msg}")
                raise Exception(error_msg)
            else:
                raise

    def test_connection(self) -> bool:
        """Test if the TTS server is reachable."""
        try:
            response = requests.get(self.server_root, timeout=5)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return 'info' in data or 'documentation' in data
                except:
                    return False
            return False
        except:
            return False
    
    def cleanup(self):
        """No cleanup needed for API client"""
        pass