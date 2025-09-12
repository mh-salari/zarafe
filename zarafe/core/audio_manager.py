"""Simple audio playback for video synchronization."""

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer


class AudioManager:
    """Simple audio manager using Qt multimedia."""

    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.is_muted = False
        self.volume_before_mute = 1.0

    def load_video(self, video_path: str) -> None:
        """Load video file for audio playback."""
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
        """Set playback position in milliseconds."""
        self.player.setPosition(position_ms)

    def set_volume(self, volume: float) -> None:
        """Set volume (0.0 to 1.0)."""
        if not self.is_muted:
            self.volume_before_mute = volume
        self.audio_output.setVolume(volume)

    def toggle_mute(self) -> bool:
        """Toggle mute state and return current mute status."""
        if self.is_muted:
            # Unmute - restore previous volume
            self.audio_output.setVolume(self.volume_before_mute)
            self.is_muted = False
        else:
            # Mute - save current volume and set to 0
            self.volume_before_mute = self.audio_output.volume()
            self.audio_output.setVolume(0.0)
            self.is_muted = True
        return self.is_muted

    def cleanup(self) -> None:
        """Clean up resources."""
        self.player.stop()
