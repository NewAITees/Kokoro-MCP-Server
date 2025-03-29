"""
Kokoro TTSサービスの実装
"""

import logging
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import librosa
import numpy as np
import soundfile as sf
import torch
from numpy.typing import NDArray
from torch import Tensor

from kokoro_mcp_server.kokoro.base import BaseTTSService, TTSRequest


class KokoroTTSService(BaseTTSService):
    """Kokoro TTSサービスの実装クラス"""

    def __init__(self):
        """サービスの初期化"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"KokoroTTSService initialized with device: {self.device}")

        try:
            # 日本語用のパイプラインを初期化
            self.pipeline = self._create_pipeline(lang_code="j")
            self.logger.info("Successfully initialized KPipeline with lang_code='j'")
        except Exception as e:
            self.logger.error(f"Failed to initialize KPipeline: {e}", exc_info=True)
            raise

    def _create_pipeline(self, lang_code: str):
        """パイプラインを作成する"""
        try:
            from kokoro import KPipeline
            return KPipeline(lang_code=lang_code)
        except ImportError:
            self.logger.error("Kokoro package is not installed")
            raise

    def generate(self, request: TTSRequest) -> tuple[bool, str | None]:
        """音声を生成する

        Args:
            request: TTSリクエスト

        Returns:
            tuple[bool, Optional[str]]: 成功したかどうかとファイルパス
        """
        try:
            self.logger.info(
                f"Starting voice generation for text: {request.text[:50]}..."
            )

            # 出力ディレクトリの作成
            voice_folder = Path("output/audio")
            voice_folder.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Voice folder created/confirmed: {voice_folder}")

            # 出力ファイル名の生成
            base_filename = request.voice or "output"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.logger.debug(f"Base filename: {base_filename}, Timestamp: {timestamp}")

            # 音声生成
            speed = request.speed if request.speed is not None else 1.0
            self.logger.debug(f"Speed set to: {speed}")

            # 高品質な日本語音声を使用
            voice = "jf_alpha" if not request.voice else request.voice
            self.logger.info(f"Using voice: {voice}")

            # 出力ファイル名の生成
            filename = voice_folder / f"{base_filename}_{timestamp}.wav"
            self.logger.debug(f"Generated filename: {filename}")

            self.logger.debug("Starting pipeline generation...")
            # 分割せずに一度に生成
            gs, ps, audio = next(
                self.pipeline(
                    request.text,
                    voice=voice,
                    speed=cast(Any, speed),
                    split_pattern=None,  # 分割を行わない
                )
            )

            try:
                if audio is not None:
                    # 音声データをNumPy配列に変換して保存
                    self.logger.debug("Converting audio to numpy array...")
                    # audioはTensorなのでcpu()とnumpy()が使える
                    audio_tensor: Tensor = cast(Tensor, audio)
                    audio_np: NDArray[np.float64] = audio_tensor.cpu().numpy()

                    # 24000Hzから44100Hzにリサンプリング
                    self.logger.debug("Resampling audio from 24000Hz to 44100Hz...")
                    # リサンプリング時は1次元配列が必要
                    if len(audio_np.shape) > 1:
                        audio_np = audio_np.squeeze()
                    audio_resampled: NDArray[np.float64] = librosa.resample(
                        y=audio_np, orig_sr=24000, target_sr=44100
                    )

                    self.logger.debug(f"Writing audio to file: {filename}")
                    sf.write(str(filename), audio_resampled, 44100)

                    self.logger.info(f"Successfully generated audio file: {filename}")
                    self.logger.debug(f"Graphemes: {gs}")
                    self.logger.debug(f"Phonemes: {ps}")
                    return True, str(filename)
                self.logger.warning("No audio was generated")
                return False, None

            except Exception as e:
                self.logger.error(f"Error processing audio: {e}", exc_info=True)
                return False, None

        except Exception as e:
            self.logger.error(f"Kokoro TTS Error: {e}", exc_info=True)
            return False, None

    def generate_audio(
        self,
        text: str,
        voice: str = "jf_alpha",  # デフォルトを高品質な日本語音声に変更
        speed: float = 1.0,
    ) -> Generator[tuple[str, str, torch.Tensor], None, None]:
        """音声生成の実行

        Args:
            text: 変換するテキスト
            voice: 使用する音声
            speed: 音声の速度

        Yields:
            Generator[Tuple[str, str, torch.Tensor], None, None]:
                生成された音声データ、グラフェーム、音素のタプルのジェネレータ
        """
        try:
            self.logger.info(f"Starting audio generation for text: {text[:50]}...")
            self.logger.debug(f"Parameters - Voice: {voice}, Speed: {speed}")

            # パイプラインの実行
            generator = self.pipeline(
                text,
                voice=voice,
                speed=cast(Any, speed),
                split_pattern=r"[。、．，!?！？\n]+",  # より自然な区切りのためのパターン
            )

            for gs, ps, audio in generator:
                if audio is not None:
                    self.logger.debug(
                        f"Generated audio chunk - Graphemes: {gs[:30]}..."
                    )
                    yield gs, ps, audio

        except Exception as e:
            self.logger.error(f"Error in generate_audio: {e}", exc_info=True)
            raise
