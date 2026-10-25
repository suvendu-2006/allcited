import { test, describe } from "node:test";
import assert from "node:assert";

describe("Web Reveal Theme Transition Geometry Assertions (§6.5)", () => {
  test("Max radius with 1.1 factor guarantees complete corner coverage", () => {
    const W = 1920;
    const H = 1080;
    const testPoints = [
      { x: 1800, y: 40 }, // top right toggle
      { x: 0, y: 0 },       // top left corner
      { x: W / 2, y: H / 2 }, // center
      { x: W, y: H },       // bottom right
    ];

    for (const { x, y } of testPoints) {
      const maxDistX = Math.max(x, W - x);
      const maxDistY = Math.max(y, H - y);
      const hypot = Math.hypot(maxDistX, maxDistY);
      const maxRadius = hypot * 1.1;

      // Ensure every corner of the viewport is strictly within maxRadius
      const corners = [
        [0, 0],
        [W, 0],
        [0, H],
        [W, H],
      ];
      for (const [cx, cy] of corners) {
        const distToCorner = Math.hypot(cx - x, cy - y);
        assert.ok(
          maxRadius >= distToCorner,
          `maxRadius ${maxRadius} should cover corner (${cx}, ${cy}) at dist ${distToCorner}`
        );
      }
    }
  });

  test("Web mesh geometry: 10 radial spokes and 8 concentric polygon rings", () => {
    const spokeCount = 10;
    const ringCount = 8;
    const x = 500;
    const y = 300;
    const maxRadius = 1000;

    const spokes = [];
    for (let i = 0; i < spokeCount; i++) {
      const angle = (i * 2 * Math.PI) / spokeCount;
      const endX = x + maxRadius * Math.cos(angle);
      const endY = y + maxRadius * Math.sin(angle);
      spokes.push({ endX, endY, angle });
    }
    assert.strictEqual(spokes.length, 10);

    const rings = [];
    for (let r = 1; r <= ringCount; r++) {
      const ringRadius = (maxRadius * r) / ringCount;
      const vertices = [];
      for (let i = 0; i < spokeCount; i++) {
        const angle = (i * 2 * Math.PI) / spokeCount;
        const px = x + ringRadius * Math.cos(angle);
        const py = y + ringRadius * Math.sin(angle);
        vertices.push({ px, py });
      }
      rings.push({ ringRadius, vertices });
    }

    assert.strictEqual(rings.length, 8);
    for (const ring of rings) {
      assert.strictEqual(ring.vertices.length, 10);
      assert.ok(ring.ringRadius > 0 && ring.ringRadius <= maxRadius);
    }
  });
});
