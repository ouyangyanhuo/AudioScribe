import { useCallback, useEffect, useRef, useState } from 'react';
import { Pause, Play, RotateCcw } from 'lucide-react';

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

/** Downsample the raw channel data to a fixed number of bars. */
function downsample(data: Float32Array, bars: number): Float32Array {
  const result = new Float32Array(bars);
  const step = data.length / bars;
  for (let i = 0; i < bars; i++) {
    const start = Math.floor(i * step);
    const end = Math.floor((i + 1) * step);
    let peak = 0;
    for (let j = start; j < end; j++) {
      const abs = Math.abs(data[j]);
      if (abs > peak) peak = abs;
    }
    result[i] = peak;
  }
  return result;
}

export function AudioWaveformPlayer({
  audioUrl,
  fileName,
  onRemove,
}: {
  audioUrl: string;
  fileName: string | null;
  onRemove?: () => void;
}) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [peaks, setPeaks] = useState<Float32Array | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [canvasWidth, setCanvasWidth] = useState(400);

  const bars = 120;

  // Decode audio and extract peaks
  useEffect(() => {
    let cancelled = false;
    setPeaks(null);
    setDuration(0);
    setCurrentTime(0);
    setIsPlaying(false);

    const ctx = new AudioContext();

    fetch(audioUrl)
      .then((r) => r.arrayBuffer())
      .then((buf) => ctx.decodeAudioData(buf))
      .then((buffer) => {
        if (cancelled) return;
        setDuration(buffer.duration);
        // Mix down to mono
        const raw =
          buffer.numberOfChannels === 1
            ? buffer.getChannelData(0)
            : (() => {
                const ch0 = buffer.getChannelData(0);
                const ch1 = buffer.getChannelData(1);
                const mixed = new Float32Array(ch0.length);
                for (let i = 0; i < ch0.length; i++) mixed[i] = (ch0[i] + ch1[i]) / 2;
                return mixed;
              })();
        setPeaks(downsample(raw, bars));
      })
      .catch(() => {});

    return () => {
      cancelled = true;
      ctx.close();
    };
  }, [audioUrl]);

  // Resize observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setCanvasWidth(Math.floor(entry.contentRect.width));
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Draw waveform
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !peaks) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const w = canvasWidth;
    const h = 64;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, w, h);

    const barWidth = Math.max(2, (w / bars) * 0.7);
    const gap = w / bars;
    const midY = h / 2;
    const progress = duration > 0 ? currentTime / duration : 0;
    const progressX = w * progress;

    for (let i = 0; i < bars; i++) {
      const x = i * gap + gap / 2;
      const amp = peaks[i] * (h * 0.85);
      const barH = Math.max(2, amp);

      // Color: played vs unplayed
      if (x < progressX) {
        ctx.fillStyle = getComputedStyle(document.documentElement)
          .getPropertyValue('--accent')
          .trim() || '#b39a3d';
      } else {
        ctx.fillStyle = getComputedStyle(document.documentElement)
          .getPropertyValue('--text-muted')
          .trim() || '#938f84';
        ctx.globalAlpha = 0.45;
      }

      // Top bar
      ctx.beginPath();
      ctx.roundRect(x - barWidth / 2, midY - barH / 2, barWidth, barH, 1);
      ctx.fill();

      ctx.globalAlpha = 1;
    }

    // Playhead
    if (duration > 0) {
      const phX = progressX;
      ctx.fillStyle = getComputedStyle(document.documentElement)
        .getPropertyValue('--accent-light')
        .trim() || '#d7bd57';
      ctx.fillRect(phX - 1, 2, 2, h - 4);
    }
  }, [peaks, canvasWidth, currentTime, duration]);

  useEffect(() => {
    drawWaveform();
  }, [drawWaveform]);

  // Animation frame for smooth progress
  useEffect(() => {
    let raf: number;
    const tick = () => {
      const audio = audioRef.current;
      if (audio) setCurrentTime(audio.currentTime);
      raf = requestAnimationFrame(tick);
    };
    if (isPlaying) raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [isPlaying]);

  // Seek by clicking/dragging on canvas
  const seekFromX = useCallback(
    (clientX: number) => {
      const canvas = canvasRef.current;
      const audio = audioRef.current;
      if (!canvas || !audio || !duration) return;
      const rect = canvas.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      audio.currentTime = ratio * duration;
      setCurrentTime(audio.currentTime);
    },
    [duration],
  );

  const handleCanvasMouseDown = useCallback(
    (e: React.MouseEvent) => {
      setIsDragging(true);
      seekFromX(e.clientX);
    },
    [seekFromX],
  );

  useEffect(() => {
    if (!isDragging) return;
    const handleMove = (e: MouseEvent) => seekFromX(e.clientX);
    const handleUp = () => setIsDragging(false);
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };
  }, [isDragging, seekFromX]);

  const togglePlayback = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
  }, [isPlaying]);

  const handleRestart = useCallback(() => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = 0;
    setCurrentTime(0);
  }, []);

  return (
    <div className="waveform-player" ref={containerRef}>
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="auto"
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
        onLoadedMetadata={() => {
          const audio = audioRef.current;
          if (audio) setDuration(audio.duration);
        }}
      />

      {/* Waveform canvas */}
      <div
        className="waveform-canvas-wrap"
        onMouseDown={handleCanvasMouseDown}
        role="slider"
        tabIndex={0}
        aria-label="Audio seek"
      >
        <canvas ref={canvasRef} className="waveform-canvas" />
      </div>

      {/* Controls row */}
      <div className="waveform-controls">
        <div className="waveform-controls-left">
          <button
            className="waveform-btn"
            onClick={togglePlayback}
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause size={15} /> : <Play size={15} />}
          </button>
          <button className="waveform-btn waveform-btn-ghost" onClick={handleRestart} title="Restart">
            <RotateCcw size={13} />
          </button>
        </div>

        <div className="waveform-time">
          <span>{formatTime(currentTime)}</span>
          <span className="waveform-time-sep">/</span>
          <span>{formatTime(duration)}</span>
        </div>

        <div className="waveform-controls-right">
          {fileName && <span className="waveform-filename">{fileName}</span>}
          {onRemove && (
            <button className="waveform-btn waveform-btn-ghost waveform-btn-danger" onClick={onRemove}>
              ×
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
