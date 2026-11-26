// The Phaser drawer shared by the hosted page (main.js) and the online page
// (online.js), moved out of main.js unchanged (T13). It blits a payload's draw
// list: pooled Phaser objects, one per draw entry, depth = list order. No
// game logic. Loaded as window.SMDraw.
/* global Phaser */
(function (root) {
  "use strict";

  function makeDrawer(scene, panelW, gap) {
    const pools = { img: [], rect: [], line: [] };
    const used = { img: 0, rect: 0, line: 0 };

    function take(kind, create) {
      let obj = pools[kind][used[kind]];
      if (obj === undefined) {
        obj = create();
        pools[kind].push(obj);
      }
      used[kind] += 1;
      obj.setVisible(true);
      return obj;
    }

    function frameKey(sheet, src) {
      const key = src.join(",");
      const tex = scene.textures.get(sheet);
      if (!tex.has(key)) {
        tex.add(key, 0, src[0], src[1], src[2], src[3]);
      }
      return key;
    }

    function colour(hex) {
      return parseInt(hex.slice(1), 16);
    }

    function draw(list, dx, depth0) {
      list.forEach(function (d, i) {
        const depth = depth0 + i;
        if (d.img !== undefined) {
          const im = take("img", function () { return scene.add.image(0, 0, d.img); });
          im.setTexture(d.img, frameKey(d.img, d.src));
          im.setFlipX(d.flip);
          im.setDisplaySize(d.w, d.h);
          im.setOrigin(d.ox / d.w, d.oy / d.h);
          im.setPosition(dx + d.x + d.ox, d.y + d.oy);
          im.setAngle(d.rot);
          if (d.tint) { im.setTint(colour(d.tint)); } else { im.clearTint(); }
          im.setDepth(depth);
        } else if (d.rect !== undefined) {
          const r = take("rect", function () { return scene.add.rectangle(0, 0, 1, 1, 0).setOrigin(0, 0); });
          r.setPosition(dx + d.rect[0], d.rect[1]);
          r.setSize(d.rect[2], d.rect[3]);
          r.setFillStyle(colour(d.color));
          r.setDepth(depth);
        } else if (d.line !== undefined) {
          const l = take("line", function () { return scene.add.line(0, 0, 0, 0, 1, 1, 0).setOrigin(0, 0).setLineWidth(1); });
          l.setPosition(dx + 0.5, 0.5);
          l.setTo(d.line[0], d.line[1], d.line[2], d.line[3]);
          l.setStrokeStyle(1, colour(d.color));
          l.setDepth(depth);
        }
      });
      return depth0 + list.length;
    }

    return {
      frame: function (panels) {
        used.img = 0; used.rect = 0; used.line = 0;
        let depth = 0;
        panels.forEach(function (p, k) {
          depth = draw(p.draw, k * (panelW + gap), depth);
        });
        ["img", "rect", "line"].forEach(function (kind) {
          for (let i = used[kind]; i < pools[kind].length; i += 1) {
            pools[kind][i].setVisible(false);
          }
        });
      },
    };
  }

  root.SMDraw = Object.freeze({ makeDrawer: makeDrawer });
})(typeof self !== "undefined" ? self : this);
