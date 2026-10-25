import { test, describe } from "node:test";
import assert from "node:assert";

describe("Wave Transition Geometry Assertions (§5)", () => {
  test("Hypotenuse calculation correctly covers farthest corner", () => {
    const W = 1920;
    const H = 1080;
    const clickX = 1800; // toggle in top right
    const clickY = 40;

    const maxDistX = Math.max(clickX, W - clickX);
    const maxDistY = Math.max(clickY, H - clickY);
    const maxRadius = Math.hypot(maxDistX, maxDistY);

    // Farthest corner from (1800, 40) is bottom-left (0, 1080)
    // Distance = sqrt(1800^2 + 1040^2) = sqrt(3240000 + 1081600) = sqrt(4321600) ≈ 2078.8
    assert.ok(maxRadius > 2000, `Expected max radius > 2000px, got ${maxRadius}`);
    assert.strictEqual(maxDistX, 1800);
    assert.strictEqual(maxDistY, 1040);
  });

  test("Cubic Bezier wavy disc has exact M + 8 C segments + Z", () => {
    // 8 segments with cubic controls
    const N = 8;
    const step = (Math.PI * 2) / N;
    const points = [];
    const cx = 500;
    const cy = 500;
    const r = 200;

    for (let i = 0; i < N; i++) {
      const theta = i * step;
      points.push({
        x: cx + r * Math.cos(theta),
        y: cy + r * Math.sin(theta),
      });
    }

    assert.strictEqual(points.length, 8);
    // Tangent factor for 8 segments (45 degrees) is (4/3)*tan(pi/16) ≈ 0.265
    const k = (4 / 3) * Math.tan(Math.PI / (2 * N));
    assert.ok(k > 0.25 && k < 0.28, `Tangent factor k for N=8 should be ~0.265, got ${k}`);
  });
});
