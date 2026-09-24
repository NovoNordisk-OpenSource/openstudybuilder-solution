// Annotation overlay for the neodash-ai-documentation skill.
//
// Drop this whole file into Playwright MCP's `browser_evaluate` once per page
// (it is idempotent — safe to re-run). It draws a red box on a target element
// and, optionally, a red arrow + label callout pointing at it — matching the
// style of docs/public/images/user_guides/neodash_elements_overview.png.
//
// Convention (annotated FIRST, clean SECOND — the target can move after a click):
//   1. evaluate(this file)                         // inject helpers
//   2. evaluate(() => neodashAnnotate('<selector>', { arrow: 'auto', label: 'Select study' }))
//   3. browser_take_screenshot  -> annotated-<...>.png   // referenced in the draft
//   4. evaluate(() => neodashAnnotateClear())
//   5. browser_take_screenshot  -> <...>.png             // clean sidecar
//   6. click the element and continue
//
// Multiple neodashAnnotate() calls before one screenshot stack on the same
// overlay (use when one screenshot has several call-outs; pass { number: N }).
//
// Color is hard-coded red (#e01e28) to stay consistent across guides.

(() => {
  const NS = "http://www.w3.org/2000/svg";
  const ROOT_ID = "neodash-annotate-root";
  const RED = "#e01e28";

  function docSize() {
    const d = document.documentElement;
    const b = document.body;
    return {
      w: Math.max(d.scrollWidth, b ? b.scrollWidth : 0, d.clientWidth),
      h: Math.max(d.scrollHeight, b ? b.scrollHeight : 0, d.clientHeight),
    };
  }

  function ensureRoot() {
    let svg = document.getElementById(ROOT_ID);
    if (svg) return svg;
    const { w, h } = docSize();
    svg = document.createElementNS(NS, "svg");
    svg.id = ROOT_ID;
    svg.setAttribute("width", w);
    svg.setAttribute("height", h);
    Object.assign(svg.style, {
      position: "absolute",
      left: "0",
      top: "0",
      width: w + "px",
      height: h + "px",
      pointerEvents: "none",
      zIndex: "2147483647",
      overflow: "visible",
    });
    // arrowhead marker
    const defs = document.createElementNS(NS, "defs");
    const marker = document.createElementNS(NS, "marker");
    marker.setAttribute("id", "neodash-arrowhead");
    marker.setAttribute("markerWidth", "10");
    marker.setAttribute("markerHeight", "10");
    marker.setAttribute("refX", "8");
    marker.setAttribute("refY", "3");
    marker.setAttribute("orient", "auto");
    const tip = document.createElementNS(NS, "path");
    tip.setAttribute("d", "M0,0 L8,3 L0,6 Z");
    tip.setAttribute("fill", RED);
    marker.appendChild(tip);
    defs.appendChild(marker);
    svg.appendChild(defs);
    document.body.appendChild(svg);
    return svg;
  }

  function absRect(el) {
    const r = el.getBoundingClientRect();
    const sx = window.scrollX || window.pageXOffset;
    const sy = window.scrollY || window.pageYOffset;
    return { left: r.left + sx, top: r.top + sy, width: r.width, height: r.height };
  }

  // Public: neodashAnnotate(target, opts)
  //   target : CSS selector string or a live Element
  //   opts.arrow  : "auto" | {x, y}   draw an arrow pointing at the box
  //   opts.label  : string            red callout text at the arrow origin
  //   opts.mark   : "A"               small badge at the box top-left. Use LETTERS
  //                                   (A, B, C, …) so the prose can refer to (A),
  //                                   (B) — see references/annotation-conventions.md.
  //   opts.number : deprecated alias for opts.mark (kept for older call sites)
  window.neodashAnnotate = function neodashAnnotate(target, opts = {}) {
    const svg = ensureRoot();
    let el = typeof target === "string" ? document.querySelector(target) : target;
    if (!el || !(el instanceof Element)) {
      throw new Error("neodashAnnotate: target not found: " + target);
    }
    const b = absRect(el);

    // red box
    const box = document.createElementNS(NS, "rect");
    box.setAttribute("x", b.left - 3);
    box.setAttribute("y", b.top - 3);
    box.setAttribute("width", b.width + 6);
    box.setAttribute("height", b.height + 6);
    box.setAttribute("rx", "3");
    box.setAttribute("fill", "none");
    box.setAttribute("stroke", RED);
    box.setAttribute("stroke-width", "3");
    svg.appendChild(box);

    // arrow + label callout
    if (opts.arrow) {
      // origin: explicit point, or auto (up-and-left of the box, clamped to doc)
      let ox, oy;
      if (opts.arrow === "auto" || opts.arrow === true) {
        ox = Math.max(12, b.left - 140);
        oy = Math.max(12, b.top - 60);
      } else {
        ox = opts.arrow.x;
        oy = opts.arrow.y;
      }
      const tx = b.left;            // aim at the box's top-left corner area
      const ty = b.top;
      const line = document.createElementNS(NS, "line");
      line.setAttribute("x1", ox);
      line.setAttribute("y1", oy);
      line.setAttribute("x2", tx);
      line.setAttribute("y2", ty);
      line.setAttribute("stroke", RED);
      line.setAttribute("stroke-width", "3");
      line.setAttribute("marker-end", "url(#neodash-arrowhead)");
      svg.appendChild(line);

      if (opts.label) {
        const padX = 8, fs = 15;
        const w = opts.label.length * (fs * 0.62) + padX * 2;
        const h = fs + 12;
        const lx = Math.max(2, ox - w);
        const ly = Math.max(2, oy - h / 2);
        const rect = document.createElementNS(NS, "rect");
        rect.setAttribute("x", lx);
        rect.setAttribute("y", ly);
        rect.setAttribute("width", w);
        rect.setAttribute("height", h);
        rect.setAttribute("rx", "4");
        rect.setAttribute("fill", "#ffffff");
        rect.setAttribute("stroke", RED);
        rect.setAttribute("stroke-width", "2");
        svg.appendChild(rect);
        const text = document.createElementNS(NS, "text");
        text.setAttribute("x", lx + padX);
        text.setAttribute("y", ly + h / 2 + fs * 0.35);
        text.setAttribute("fill", RED);
        text.setAttribute("font-family", "Arial, Helvetica, sans-serif");
        text.setAttribute("font-size", fs);
        text.setAttribute("font-weight", "700");
        text.textContent = opts.label;
        svg.appendChild(text);
      }
    }

    // letter badge (opts.mark; opts.number kept as a deprecated alias)
    const mark = opts.mark != null ? opts.mark : opts.number;
    if (mark != null) {
      const cx = b.left - 3, cy = b.top - 3, r = 13;
      const circle = document.createElementNS(NS, "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", r);
      circle.setAttribute("fill", RED);
      svg.appendChild(circle);
      const t = document.createElementNS(NS, "text");
      t.setAttribute("x", cx);
      t.setAttribute("y", cy + 5);
      t.setAttribute("fill", "#ffffff");
      t.setAttribute("text-anchor", "middle");
      t.setAttribute("font-family", "Arial, Helvetica, sans-serif");
      t.setAttribute("font-size", "14");
      t.setAttribute("font-weight", "700");
      t.textContent = String(mark);
      svg.appendChild(t);
    }

    return b;
  };

  // Public: remove all annotations
  window.neodashAnnotateClear = function neodashAnnotateClear() {
    const svg = document.getElementById(ROOT_ID);
    if (svg) svg.remove();
  };
})();
