# Audiobook Maker Pro

A desktop application for turning text, PDF, and EPUB content into audiobooks with Chatterbox TTS.

## Features

- Fast local Chatterbox inference without a TTS-WebUI server
- English and multilingual Chatterbox models
- Voice-reference management
- TXT, PDF, and EPUB input
- Built-in ebook chapter editor and audio preview
- Optional remote TTS-WebUI API compatibility

## Requirements

- Python 3.10 or 3.11
- Windows 10/11, Linux, or macOS
- An NVIDIA CUDA GPU is strongly recommended for audiobook generation

## Installation

Create and activate a virtual environment first:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

For an NVIDIA GPU, install the same PyTorch generation used by the current TTS-WebUI setup:

```powershell
python -m pip install torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128
```

Then install the application:

```powershell
python -m pip install -r requirements.txt
python main.py
```

For CPU, macOS, AMD, or Intel GPU installation commands, use the [PyTorch installation selector](https://pytorch.org/get-started/locally/) before installing `requirements.txt`.

### Updating an existing installation

Older versions of this repository installed a different package under the `chatterbox-tts` name. Remove both possible distributions once, then reinstall so that shared `chatterbox` module files cannot overlap:

```powershell
python -m pip uninstall -y chatterbox-tts tts-webui.chatterbox-tts
python -m pip install -r requirements.txt
```

## Usage

### Local mode (recommended)

1. Select **Local Chatterbox (Direct)**.
2. Choose `chatterbox` or `multilingual`, a precision, and an optional voice reference.
3. Enter text or open a supported file.
4. Generate the audio.

Local CUDA generation uses the optimized Chatterbox 0.4.4 inference package and its manual CUDA-graph token backend—the same performance path used by the TTS-WebUI Chatterbox extension. TTS-WebUI itself is not imported or required. The first generation can take longer while CUDA graphs and caches are prepared; later chunks reuse them.

### API mode (optional)

Use API mode only when you want to generate on another machine or keep compatibility with an existing TTS-WebUI server. Activate its OpenAI-compatible API and use the default endpoint, `http://localhost:7778/v1`, or enter a remote endpoint.

## Acknowledgements

- [Chatterbox](https://github.com/resemble-ai/chatterbox) by Resemble AI
- [TTS-WebUI Chatterbox performance fork](https://github.com/rsxdalv/chatterbox)
- [TTS-WebUI](https://github.com/rsxdalv/TTS-WebUI) for API compatibility
