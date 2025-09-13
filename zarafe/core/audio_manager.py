"""Audio playback for video synchronization."""

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

# Audio constants
DEFAULT_VOLUME = 1.0
MUTE_VOLUME = 0.0


class AudioManager:
    """Audio manager using Qt multimedia."""

    def __init__(self) -> None:
        """Initialize the audio manager."""
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.is_muted = False
        self.volume_before_mute = DEFAULT_VOLUME

    def load_video(self, video_path: str) -> None:
        """Load video for audio playback."""
        url = QUrl.fromLocalFile(video_path)
        self.player.setSource(url)

    def play(self) -> None:
        """Start audio playback."""
        self.player.play()

    def pause(self) -> None:
        """Pause audio playback."""
        self.player.pause()

    def stop(self) -> None:
        """Stop audio playback."""
        self.player.stop()

    def set_position(self, position_ms: int) -> None:
        """Set audio playback position."""
        self.player.setPosition(position_ms)

    def set_volume(self, volume: float) -> None:
        """Set audio volume."""
        if not self.is_muted:
            self.volume_before_mute = volume
        self.audio_output.setVolume(volume)

    def toggle_mute(self) -> bool:
        """Toggle audio mute state."""
        if self.is_muted:
            self.audio_output.setVolume(self.volume_before_mute)
            self.is_muted = False
        else:
            self.volume_before_mute = self.audio_output.volume()
            self.audio_output.setVolume(MUTE_VOLUME)
            self.is_muted = True
        return self.is_muted

    def cleanup(self) -> None:
        """Clean up audio resources."""
        self.player.stop()
