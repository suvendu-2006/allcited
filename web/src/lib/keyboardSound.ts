// Mechanical Switch Audio Synthesizer via Web Audio API
// Exclusively triggers on dark/light mode toggle. All general button clicks and typing are strictly silent.

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  try {
    if (!audioCtx) {
      const AudioContextClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === "suspended") {
      audioCtx.resume().catch(() => {});
    }
  } catch {
    // AudioContext initialization fallback
  }
  return audioCtx;
}

export function isSoundEnabled(): boolean {
  if (typeof window === "undefined") return true;
  const stored = localStorage.getItem("allcited_sound_fx");
  return stored !== "false";
}

export function setSoundEnabled(enabled: boolean): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("allcited_sound_fx", enabled ? "true" : "false");
  }
}

/**
 * Play a crisp, punchy, tactile mechanical switch sound ONLY when toggling between dark and light mode.
 */
export function playToggleClick(isDarkNext: boolean): void {
  if (!isSoundEnabled()) return;

  try {
    const ctx = getAudioContext();
    if (!ctx) return;

    const play = () => {
      try {
        const now = ctx.currentTime;
        const pitch = isDarkNext ? 0.95 : 1.3;

        // 1. Crisp mechanical latch snap (contact transient)
        const sampleRate = ctx.sampleRate;
        const bufferSize = Math.floor(sampleRate * 0.02); // 20ms
        const buffer = ctx.createBuffer(1, bufferSize, sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
          data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.22));
        }

        const noise = ctx.createBufferSource();
        noise.buffer = buffer;

        const filter = ctx.createBiquadFilter();
        filter.type = "bandpass";
        filter.frequency.setValueAtTime(3000 * pitch, now);
        filter.Q.setValueAtTime(3.2, now);

        const noiseGain = ctx.createGain();
        noiseGain.gain.setValueAtTime(0.85, now);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.025);

        noise.connect(filter);
        filter.connect(noiseGain);
        noiseGain.connect(ctx.destination);
        noise.start(now);

        // 2. Resonant mechanical switch body "thock"
        const osc = ctx.createOscillator();
        const oscGain = ctx.createGain();

        osc.type = "triangle";
        const baseFreq = isDarkNext ? 220 : 340;
        osc.frequency.setValueAtTime(baseFreq, now);
        osc.frequency.exponentialRampToValueAtTime(baseFreq * 0.45, now + 0.07);

        oscGain.gain.setValueAtTime(0.75, now);
        oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);

        osc.connect(oscGain);
        oscGain.connect(ctx.destination);

        osc.start(now);
        osc.stop(now + 0.085);
      } catch {
        // Fallback for audio restrictions
      }
    };

    if (ctx.state === "suspended") {
      ctx.resume().then(play).catch(() => {});
    } else {
      play();
    }
  } catch {
    // Audio context error fallback
  }
}
