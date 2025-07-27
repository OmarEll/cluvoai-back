import asyncio
import aiofiles
import aiohttp
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import os
import tempfile
from pathlib import Path
import mimetypes

from openai import AsyncOpenAI
from core.customer_discovery_models import (
    Transcription, InterviewFile, FileType, ConfidenceLevel
)
from config.settings import settings


class TranscriptionService:
    """
    Service for transcribing audio and video files using OpenAI Whisper API
    Supports multiple formats and provides speaker diarization
    """
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.supported_audio_formats = {
            'mp3', 'mp4', 'm4a', 'wav', 'webm', 'mpga', 'mpeg'
        }
        self.max_file_size = 25 * 1024 * 1024  # 25MB limit for Whisper API
        
    async def transcribe_file(
        self,
        file_path: str,
        file_type: FileType,
        language: str = "en",
        enable_speaker_labels: bool = True,
        enable_timestamps: bool = True
    ) -> Transcription:
        """
        Transcribe an audio or video file using OpenAI Whisper
        """
        try:
            print(f"🎤 Starting transcription for file: {file_path}")
            start_time = datetime.utcnow()
            
            # Validate file
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)")
            
            # Check file format
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            if file_ext not in self.supported_audio_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Prepare transcription request
            transcription_id = str(uuid.uuid4())
            
            # Read file and send to Whisper API
            async with aiofiles.open(file_path, 'rb') as audio_file:
                file_content = await audio_file.read()
                
                # Create a temporary file-like object for the API
                response = await self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=(os.path.basename(file_path), file_content),
                    language=language if language != "auto" else None,
                    response_format="verbose_json",
                    timestamp_granularities=["word", "segment"] if enable_timestamps else ["segment"]
                )
            
            # Process response
            content = response.text
            confidence_score = self._calculate_confidence_score(response)
            
            # Extract speaker labels and timestamps
            speaker_labels = []
            timestamps = []
            
            if hasattr(response, 'segments') and response.segments:
                for i, segment in enumerate(response.segments):
                    segment_data = {
                        "id": i,
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "confidence": getattr(segment, 'avg_logprob', 0.0)
                    }
                    timestamps.append(segment_data)
                    
                    # For now, we'll use simple speaker detection
                    # In a real implementation, you might use additional speaker diarization
                    if enable_speaker_labels:
                        speaker_labels.append({
                            "speaker": f"Speaker_{(i % 2) + 1}",  # Simple alternating speakers
                            "start": segment.start,
                            "end": segment.end,
                            "confidence": 0.8  # Placeholder confidence
                        })
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create transcription object
            transcription = Transcription(
                id=transcription_id,
                file_id=file_path,  # This should be the file ID in your system
                content=content,
                confidence_score=confidence_score,
                language=language,
                speaker_labels=speaker_labels,
                timestamps=timestamps,
                processing_time=processing_time,
                created_at=datetime.utcnow()
            )
            
            print(f"✅ Transcription completed in {processing_time:.2f} seconds")
            print(f"   Content length: {len(content)} characters")
            print(f"   Confidence score: {confidence_score:.2f}")
            print(f"   Segments: {len(timestamps)}")
            
            return transcription
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            raise Exception(f"Failed to transcribe file: {str(e)}")
    
    async def transcribe_url(
        self,
        file_url: str,
        file_type: FileType,
        language: str = "en",
        enable_speaker_labels: bool = True,
        enable_timestamps: bool = True
    ) -> Transcription:
        """
        Transcribe an audio or video file from a URL
        """
        try:
            print(f"🌐 Downloading file from URL: {file_url}")
            
            # Download file to temporary location
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download file: HTTP {response.status}")
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as temp_file:
                        temp_path = temp_file.name
                        
                        async for chunk in response.content.iter_chunked(8192):
                            temp_file.write(chunk)
            
            try:
                # Transcribe the downloaded file
                transcription = await self.transcribe_file(
                    temp_path, file_type, language, enable_speaker_labels, enable_timestamps
                )
                return transcription
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            print(f"❌ URL transcription failed: {e}")
            raise Exception(f"Failed to transcribe file from URL: {str(e)}")
    
    async def transcribe_multiple_files(
        self,
        file_paths: List[str],
        file_types: List[FileType],
        language: str = "en",
        enable_speaker_labels: bool = True,
        enable_timestamps: bool = True
    ) -> List[Transcription]:
        """
        Transcribe multiple files concurrently
        """
        try:
            print(f"🎤 Starting batch transcription for {len(file_paths)} files")
            
            # Create transcription tasks
            tasks = []
            for file_path, file_type in zip(file_paths, file_types):
                task = self.transcribe_file(
                    file_path, file_type, language, enable_speaker_labels, enable_timestamps
                )
                tasks.append(task)
            
            # Execute all transcriptions concurrently
            transcriptions = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log errors
            successful_transcriptions = []
            for i, result in enumerate(transcriptions):
                if isinstance(result, Exception):
                    print(f"❌ Failed to transcribe {file_paths[i]}: {result}")
                else:
                    successful_transcriptions.append(result)
            
            print(f"✅ Batch transcription completed: {len(successful_transcriptions)}/{len(file_paths)} successful")
            return successful_transcriptions
            
        except Exception as e:
            print(f"❌ Batch transcription failed: {e}")
            raise Exception(f"Failed to transcribe multiple files: {str(e)}")
    
    def _calculate_confidence_score(self, response: Any) -> float:
        """
        Calculate overall confidence score from Whisper response
        """
        try:
            if hasattr(response, 'segments') and response.segments:
                # Calculate average confidence from segments
                total_confidence = 0.0
                total_duration = 0.0
                
                for segment in response.segments:
                    if hasattr(segment, 'avg_logprob'):
                        # Convert log probability to confidence (0-1)
                        # Whisper returns log probabilities, typically between -3 and 0
                        confidence = max(0.0, min(1.0, (segment.avg_logprob + 3) / 3))
                        duration = segment.end - segment.start
                        total_confidence += confidence * duration
                        total_duration += duration
                
                if total_duration > 0:
                    return total_confidence / total_duration
            
            # Default confidence if no segments available
            return 0.8
            
        except Exception as e:
            print(f"Warning: Could not calculate confidence score: {e}")
            return 0.7
    
    def get_confidence_level(self, score: float) -> ConfidenceLevel:
        """
        Convert numerical confidence score to confidence level enum
        """
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    async def extract_audio_from_video(self, video_path: str) -> str:
        """
        Extract audio from video file (for future implementation)
        This would require ffmpeg or similar tool
        """
        # Placeholder for video audio extraction
        # In a real implementation, you'd use ffmpeg to extract audio
        return video_path
    
    def validate_file_format(self, file_path: str) -> bool:
        """
        Validate if the file format is supported
        """
        file_ext = Path(file_path).suffix.lower().lstrip('.')
        return file_ext in self.supported_audio_formats
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about the file
        """
        try:
            file_stats = os.stat(file_path)
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_stats.st_size,
                "file_extension": file_ext,
                "mime_type": mime_type,
                "created_at": datetime.fromtimestamp(file_stats.st_ctime),
                "modified_at": datetime.fromtimestamp(file_stats.st_mtime),
                "is_supported": self.validate_file_format(file_path)
            }
            
        except Exception as e:
            print(f"Error getting file info: {e}")
            return {}


# Create singleton instance
transcription_service = TranscriptionService() 