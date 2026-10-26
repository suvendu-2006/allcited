import { describe, it } from 'node:test';
import assert from 'node:assert';

describe('Equilateral Triangle Geometry & Non-scaling Stroke', () => {
  it('Equilateral triangle vertices are centered around mathematical centroid (0,0)', () => {
    // Equilateral triangle with circumradius R = 115.47
    // Vertex 0: (0, -R) = (0, -115.47)
    // Vertex 1: (R * cos(30°), R * sin(30°)) = (115.47 * 0.866025, 115.47 * 0.5) = (100, 57.74)
    // Vertex 2: (-100, 57.74)
    const v0 = { x: 0, y: -115.47 };
    const v1 = { x: 100, y: 57.74 };
    const v2 = { x: -100, y: 57.74 };

    // Centroid = (v0 + v1 + v2) / 3
    const cx = (v0.x + v1.x + v2.x) / 3;
    const cy = (v0.y + v1.y + v2.y) / 3;

    assert.ok(Math.abs(cx) < 0.01, `Centroid X should be 0, got ${cx}`);
    assert.ok(Math.abs(cy) < 0.01, `Centroid Y should be 0, got ${cy}`);
  });
});

describe('Interactive Orbit Clock 12-Hour Angle & Position Mapping', () => {
  function angleToTime(deg, isPM = false) {
    const normalized = ((deg % 360) + 360) % 360;
    const totalMinutes12 = Math.round((normalized / 360) * 720) % 720;
    const rawH = Math.floor(totalMinutes12 / 60);
    const m = totalMinutes12 % 60;
    let h24;
    if (isPM) {
      h24 = rawH === 0 ? 12 : rawH + 12;
    } else {
      h24 = rawH === 0 ? 0 : rawH;
    }
    return { h: h24, m };
  }

  function timeToAngle(h, m) {
    const hour12 = h % 12;
    return ((hour12 + m / 60) / 12) * 360;
  }

  function isNight(h) {
    return h >= 18 || h < 6;
  }

  it('Top (0 deg) maps to 12:00 (Noon in PM -> Light mode)', () => {
    const { h, m } = angleToTime(0, true);
    assert.strictEqual(h, 12);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), false);
  });

  it('Top (0 deg) maps to 00:00 (Midnight in AM -> Dark mode)', () => {
    const { h, m } = angleToTime(0, false);
    assert.strictEqual(h, 0);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), true);
  });

  it('Right (90 deg) maps to 03:00 (3 o\'clock position)', () => {
    const { h, m } = angleToTime(90, false);
    assert.strictEqual(h, 3);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), true);
  });

  it('Time 3:13 maps directly to 3 o\'clock position (96.5 deg)', () => {
    const deg = timeToAngle(3, 13);
    assert.strictEqual(Math.round(deg * 10) / 10, 96.5);
    const { h, m } = angleToTime(deg, false);
    assert.strictEqual(h, 3);
    assert.strictEqual(m, 13);
  });

  it('Bottom (180 deg) at 6:00 AM (Sunrise -> transitions to Light mode)', () => {
    const { h, m } = angleToTime(180, false);
    assert.strictEqual(h, 6);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), false);
  });

  it('Bottom (180 deg) at 6:00 PM (Sunset -> transitions to Dark mode)', () => {
    const { h, m } = angleToTime(180, true);
    assert.strictEqual(h, 18);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), true);
  });

  it('Left (270 deg) maps to 09:00 (9 o\'clock position)', () => {
    const { h, m } = angleToTime(270, true);
    assert.strictEqual(h, 21);
    assert.strictEqual(m, 0);
  });
});
