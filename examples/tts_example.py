"""
Example script demonstrating the usage of Kokoro TTS.
"""

import os
from pathlib import Path
from kokoro_mcp_server.tts import KokoroTTS

def main():
    """Run the TTS example."""
    # Initialize TTS
    tts = KokoroTTS(lang_code='ja', voice='af_heart')
    
    # Sample text
    text = """
    [Kokoro](/kˈOkəɹO/)は、8200万パラメータを持つオープンウェイトのTTSモデルです。
    軽量なアーキテクチャにもかかわらず、より大きなモデルと同等の品質を提供し、
    大幅に高速でコスト効率が良いのが特徴です。
    Apacheライセンスの重み付けにより、[Kokoro](/kˈOkəɹO/)は本番環境から個人プロジェクトまで
    どこでも展開できます。
    """
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate and save audio
    print("Generating audio...")
    for i, gs, ps, audio in tts.generate_audio(text, output_dir=str(output_dir)):
        print(f"Segment {i}:")
        print(f"  Grapheme sequence: {gs}")
        print(f"  Phoneme sequence: {ps}")
        print(f"  Audio saved to: {output_dir}/{i}.wav")
    
    print("\nAudio generation completed!")

if __name__ == "__main__":
    main() 