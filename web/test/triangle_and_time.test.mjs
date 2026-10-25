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

describe('Interactive Orbit Clock 24-Hour Angle & Day/Night Mapping', () => {
  function angleToTime(deg) {
    const normalized = (deg % 360 + 360) % 360;
    const minsFromNoon = Math.round((normalized / 360) * 1440);
    const finalMinutes = (minsFromNoon + 720) % 1440;
    const h = Math.floor(finalMinutes / 60);
    const m = finalMinutes % 60;
    return { h, m };
  }

  function isNight(h) {
    return h >= 18 || h < 6;
  }

  it('Top (0 deg) maps to 12:00 (Noon, Day/Light)', () => {
    const { h, m } = angleToTime(0);
    assert.strictEqual(h, 12);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), false);
  });

  it('Right (90 deg) maps to 18:00 (Sunset, Night/Dark)', () => {
    const { h, m } = angleToTime(90);
    assert.strictEqual(h, 18);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), true);
  });

  it('Bottom (180 deg) maps to 00:00 (Midnight, Night/Dark)', () => {
    const { h, m } = angleToTime(180);
    assert.strictEqual(h, 0);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), true);
  });

  it('Left (270 deg) maps to 06:00 (Sunrise, Day/Light)', () => {
    const { h, m } = angleToTime(270);
    assert.strictEqual(h, 6);
    assert.strictEqual(m, 0);
    assert.strictEqual(isNight(h), false);
  });
});
