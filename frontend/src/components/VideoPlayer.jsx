import React, { useRef, useState, useEffect, useCallback } from 'react';
import {
  Play, Pause, Volume2, VolumeX, Maximize, Minimize,
  SkipBack, SkipForward, Settings, Loader2
} from 'lucide-react';

/**
 * VideoPlayer — HTML5 video player với đầy đủ controls.
 * Props:
 *   src           : string  — URL stream video
 *   title         : string  — tên phim/tập
 *   episodeLabel  : string  — "Tập 1", "Phim lẻ", ...
 *   initialTime   : number  — giây bắt đầu (resume)
 *   onProgress    : fn(currentSecs, durationSecs) — callback lưu tiến độ
 *   onEnded       : fn()   — callback khi xem xong
 */
export default function VideoPlayer({
  src,
  title        = '',
  episodeLabel = '',
  initialTime  = 0,
  onProgress,
  onEnded,
}) {
  const videoRef      = useRef(null);
  const containerRef  = useRef(null);
  const progressRef   = useRef(null);
  const hideTimer     = useRef(null);

  const [playing,       setPlaying]      = useState(false);
  const [currentTime,   setCurrentTime]  = useState(0);
  const [duration,      setDuration]     = useState(0);
  const [volume,        setVolume]       = useState(1);
  const [muted,         setMuted]        = useState(false);
  const [fullscreen,    setFullscreen]   = useState(false);
  const [showControls,  setShowControls] = useState(true);
  const [buffering,     setBuffering]    = useState(false);
  const [showSettings,  setShowSettings] = useState(false);

  // ── Init: seek to resume position ──────────────────────────
  useEffect(() => {
    const v = videoRef.current;
    if (!v) return;
    const onLoaded = () => {
      if (initialTime > 0 && initialTime < v.duration - 5) {
        v.currentTime = initialTime;
      }
    };
    v.addEventListener('loadedmetadata', onLoaded);
    return () => v.removeEventListener('loadedmetadata', onLoaded);
  }, [initialTime, src]);

  // ── Auto-hide controls ──────────────────────────────────────
  const resetHideTimer = useCallback(() => {
    setShowControls(true);
    clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => {
      if (playing) setShowControls(false);
    }, 3000);
  }, [playing]);

  useEffect(() => {
    return () => clearTimeout(hideTimer.current);
  }, []);

  // ── Save progress every 10 seconds ─────────────────────────
  useEffect(() => {
    if (!onProgress || !playing) return;
    const interval = setInterval(() => {
      const v = videoRef.current;
      if (v && v.duration > 0) {
        onProgress(Math.floor(v.currentTime), Math.floor(v.duration));
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [playing, onProgress]);

  // ── Fullscreen change listener ──────────────────────────────
  useEffect(() => {
    const handler = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

  // ── Video event handlers ────────────────────────────────────
  const handleTimeUpdate = () => {
    const v = videoRef.current;
    if (!v) return;
    setCurrentTime(v.currentTime);
  };

  const handleLoadedMetadata = () => {
    setDuration(videoRef.current?.duration || 0);
  };

  const handleEnded = () => {
    setPlaying(false);
    setShowControls(true);
    const v = videoRef.current;
    if (onProgress && v) onProgress(Math.floor(v.duration), Math.floor(v.duration));
    if (onEnded) onEnded();
  };

  // ── Controls ────────────────────────────────────────────────
  const togglePlay = () => {
    const v = videoRef.current;
    if (!v) return;
    if (v.paused) { v.play(); setPlaying(true); }
    else          { v.pause(); setPlaying(false); setShowControls(true); }
    resetHideTimer();
  };

  const handleProgressClick = (e) => {
    const rect = progressRef.current.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    const v = videoRef.current;
    if (v) {
      v.currentTime = ratio * v.duration;
      setCurrentTime(v.currentTime);
    }
  };

  const handleVolumeChange = (e) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) videoRef.current.volume = val;
    setMuted(val === 0);
  };

  const toggleMute = () => {
    const v = videoRef.current;
    if (!v) return;
    v.muted = !v.muted;
    setMuted(v.muted);
  };

  const skip = (secs) => {
    const v = videoRef.current;
    if (!v) return;
    v.currentTime = Math.max(0, Math.min(v.currentTime + secs, v.duration));
    resetHideTimer();
  };

  const toggleFullscreen = () => {
    if (!fullscreen) {
      containerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  // ── Format helpers ──────────────────────────────────────────
  const fmt = (secs) => {
    if (!secs || isNaN(secs)) return '0:00';
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    return `${m}:${String(s).padStart(2, '0')}`;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className="relative w-full bg-black rounded-2xl overflow-hidden group select-none"
      style={{ aspectRatio: '16/9' }}
      onMouseMove={resetHideTimer}
      onMouseLeave={() => playing && setShowControls(false)}
      onClick={togglePlay}
    >
      {/* Video element */}
      <video
        ref={videoRef}
        src={src}
        className="w-full h-full object-contain"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onWaiting={() => setBuffering(true)}
        onPlaying={() => setBuffering(false)}
        onCanPlay={() => setBuffering(false)}
        preload="metadata"
      />

      {/* Buffering spinner */}
      {buffering && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <Loader2 size={48} className="text-white animate-spin opacity-80" />
        </div>
      )}

      {/* Center play/pause indicator */}
      {!playing && !buffering && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-20 h-20 rounded-full bg-black/40 backdrop-blur-sm
                          flex items-center justify-center border border-white/20">
            <Play size={36} className="text-white ml-1" />
          </div>
        </div>
      )}

      {/* Controls overlay */}
      <div
        className={`absolute inset-0 flex flex-col justify-end
                    transition-opacity duration-300 pointer-events-none
                    ${showControls ? 'opacity-100' : 'opacity-0'}`}
        onClick={e => e.stopPropagation()}
        style={{ pointerEvents: showControls ? 'auto' : 'none' }}
      >
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/20 pointer-events-none" />

        {/* Top bar — title */}
        <div className="relative z-10 px-5 pt-4 pb-2">
          <p className="text-white font-semibold text-sm drop-shadow">
            {title}
            {episodeLabel && <span className="text-white/60 ml-2 font-normal">{episodeLabel}</span>}
          </p>
        </div>

        <div className="flex-1" />

        {/* Bottom controls */}
        <div className="relative z-10 px-4 pb-4 space-y-2">
          {/* Progress bar */}
          <div
            ref={progressRef}
            className="w-full h-1.5 bg-white/20 rounded-full cursor-pointer
                       hover:h-2.5 transition-all duration-150 group/prog"
            onClick={handleProgressClick}
          >
            <div
              className="h-full bg-gradient-to-r from-amber-400 to-orange-500 rounded-full
                         relative"
              style={{ width: `${progressPercent}%` }}
            >
              <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5
                              bg-white rounded-full shadow-md opacity-0 group-hover/prog:opacity-100
                              transition-opacity" />
            </div>
          </div>

          {/* Buttons row */}
          <div className="flex items-center gap-3">
            {/* Play/Pause */}
            <button
              id="video-play-btn"
              onClick={togglePlay}
              className="text-white hover:text-amber-400 transition-colors p-1"
            >
              {playing ? <Pause size={22} /> : <Play size={22} />}
            </button>

            {/* Skip -10s */}
            <button
              onClick={() => skip(-10)}
              className="text-white/70 hover:text-white transition-colors p-1"
              title="Lùi 10s"
            >
              <SkipBack size={18} />
            </button>

            {/* Skip +10s */}
            <button
              onClick={() => skip(10)}
              className="text-white/70 hover:text-white transition-colors p-1"
              title="Tiến 10s"
            >
              <SkipForward size={18} />
            </button>

            {/* Volume */}
            <div className="flex items-center gap-2">
              <button onClick={toggleMute} className="text-white/70 hover:text-white transition-colors p-1">
                {muted || volume === 0 ? <VolumeX size={18} /> : <Volume2 size={18} />}
              </button>
              <input
                type="range" min="0" max="1" step="0.05"
                value={muted ? 0 : volume}
                onChange={handleVolumeChange}
                className="w-20 accent-amber-400 cursor-pointer"
              />
            </div>

            {/* Time */}
            <span className="text-white/70 text-xs font-mono ml-1 tabular-nums">
              {fmt(currentTime)} / {fmt(duration)}
            </span>

            <div className="flex-1" />

            {/* Fullscreen */}
            <button
              id="video-fullscreen-btn"
              onClick={toggleFullscreen}
              className="text-white/70 hover:text-white transition-colors p-1"
            >
              {fullscreen ? <Minimize size={18} /> : <Maximize size={18} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
