"""
Kokoro TTS Service implementation
"""

import logging
from pathlib import Path
from datetime import datetime
import numpy as np
from numpy.typing import NDArray
import librosa
import soundfile as sf
import torch

from torch import Tensor
from typing import cast, Any, Generator, Tuple, Optional, List
from .base import BaseTTSService, TTSRequest

logger = logging.getLogger(__name__)

class KokoroTTSService(BaseTTSService):
    """Kokoro TTS Service implementation"""
    
    def __init__(self):
        """Initialize the service"""
        self.logger = logger
        self.pipeline = self._create_pipeline()
        
    def _create_pipeline(self):
        """Create TTS pipeline"""
        try:
            from transformers import VitsModel, AutoTokenizer
            
            # モデルとトークナイザーの初期化
            model = VitsModel.from_pretrained("facebook/mms-tts-jpn")
            tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-jpn")
            
            def pipeline(
                text: str,
                voice: str = "jf_alpha",
                speed: float = 1.0,
                split_pattern: Optional[str] = None
            ) -> Generator[Tuple[list, list, Optional[Tensor]], None, None]:
                """
                テキストから音声を生成するパイプライン
                
                Args:
                    text: 変換するテキスト
                    voice: 使用する音声ID
                    speed: 音声の速度
                    split_pattern: テキストの分割パターン
                    
                Yields:
                    tuple[list, list, Optional[Tensor]]: グラフェム、音素、音声データ
                """
                try:
                    # テキストのトークン化
                    inputs = tokenizer(text, return_tensors="pt")
                    
                    # 音声生成
                    with torch.no_grad():
                        output = model(**inputs)
                        
                    # 音声データの取得
                    audio = output.audio[0]
                    
                    # 速度調整
                    if speed != 1.0:
                        audio = self._adjust_speed(audio, speed)
                        
                    yield (
                        output.graphemes[0],
                        output.phonemes[0],
                        audio
                    )
                    
                except Exception as e:
                    self.logger.error(f"Pipeline error: {e}", exc_info=True)
                    yield [], [], None
                    
            return pipeline
            
        except Exception as e:
            self.logger.error(f"Pipeline creation error: {e}", exc_info=True)
            return None
            
    def _adjust_speed(self, audio: Tensor, speed: float) -> Tensor:
        """
        音声の速度を調整する
        
        Args:
            audio: 音声データ
            speed: 速度（0.5〜2.0）
            
        Returns:
            Tensor: 速度調整後の音声データ
        """
        try:
            # 音声データをNumPy配列に変換
            audio_np = audio.cpu().numpy()
            
            # librosaを使用して速度を調整
            audio_stretched = librosa.effects.time_stretch(audio_np, rate=1/speed)
            
            # テンソルに戻す
            return torch.from_numpy(audio_stretched)
            
        except Exception as e:
            self.logger.error(f"Speed adjustment error: {e}", exc_info=True)
            return audio
            
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
