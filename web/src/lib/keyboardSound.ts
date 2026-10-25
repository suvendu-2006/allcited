// Keyboard / Switch Audio Synthesizer
// Intentionally silent per user feedback to ensure whisper-quiet, zero-artifact time switching.

export function isSoundEnabled(): boolean {
  return false;
}

export function setSoundEnabled(): void {
  // Silent
}

export function playButtonClick(): void {
  // Silent
}

export function playKeyboardClick(): void {
  // Silent
}

/**
 * Kept strictly silent to eliminate audio clicks/pops on time scrubbing and theme switches.
 */
export function playToggleClick(): void {
  // Silent
}
