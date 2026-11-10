import logging
from typing import Dict, Any, List, Optional
from faster_whisper import WhisperModel
from backend.config import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_CPU_THREADS,
    MODELS_DIR
)

logger = logging.getLogger(__name__)

class WhisperTranscriber:
    _instance: Optional["WhisperTranscriber"] = None
    _model: Optional[WhisperModel] = None

    @classmethod
    def get_instance(cls) -> "WhisperTranscriber":
        if cls._instance is None:
            cls._instance = WhisperTranscriber()
        return cls._instance

    def __init__(self):
        self.model_name = WHISPER_MODEL
        self.device = WHISPER_DEVICE
        self.compute_type = WHISPER_COMPUTE_TYPE
        self.cpu_threads = WHISPER_CPU_THREADS
        self.download_root = str(MODELS_DIR)

    def load_model(self) -> WhisperModel:
        """Lazy loader for WhisperModel to prevent unnecessary memory consumption."""
        if self._model is None:
            logger.info(
                f"Loading Faster-Whisper model '{self.model_name}' on {self.device} "
                f"({self.compute_type}) with {self.cpu_threads} CPU threads..."
            )
            self._model = WhisperModel(
                model_size_or_path=self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.cpu_threads,
                download_root=self.download_root
            )
            logger.info("Faster-Whisper model successfully loaded into memory.")
        return self._model

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        task: str = "transcribe",
        beam_size: int = 5
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file into timestamped segments and words.
        """
        model = self.load_model()
        logger.info(f"Starting transcription for {audio_path}...")

        segments_generator, info = model.transcribe(
            audio_path,
            language=language,
            task=task,
            beam_size=beam_size,
            word_timestamps=True,
            vad_filter=True  # Voice activity detection to ignore silence
        )

        segments_list: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []

        segment_idx = 0
        for seg in segments_generator:
            words_data = []
            if seg.words:
                for w in seg.words:
                    words_data.append({
                        "word": w.word,
                        "start": round(w.start, 2),
                        "end": round(w.end, 2),
                        "probability": round(w.probability, 3)
                    })

            segment_data = {
                "id": segment_idx,
                "start": round(seg.start, 2),
                "end": round(seg.end, 2),
                "text": seg.text.strip(),
                "avg_logprob": round(seg.avg_logprob, 3),
                "no_speech_prob": round(seg.no_speech_prob, 3),
                "words": words_data
            }
            segments_list.append(segment_data)
            full_text_parts.append(seg.text.strip())
            segment_idx += 1

        full_text = " ".join(full_text_parts)

        result = {
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
            "full_text": full_text,
            "segments": segments_list
        }
        logger.info(f"Transcription complete: {len(segments_list)} segments, {result['duration']}s.")
        return result

def get_transcriber() -> WhisperTranscriber:
    return WhisperTranscriber.get_instance()
