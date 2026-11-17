// Annotation + masking overlay for the osb-app-ai-documentation skill.
//
// Drop this whole file into Playwright MCP's `browser_evaluate` once per page
// load (idempotent — safe to re-run). A full navigation or reload removes it, so
// re-inject after every page change. It provides:
//
//   osbFind(text, opts)         -> Element   exact-text lookup of a UI control
//   osbAnnotate(target, opts)   -> rect      red box (+ arrow + label + letter badge)
//   osbAnnotateClear()                       remove annotations only
//   osbMask(target, opts)       -> rect      opaque cover over sensitive content
//   osbMaskMatching(regex, opts)-> count     cover every text node match (emails, IDs)
//   osbMaskClear()                           remove masks
//
// Convention (mask FIRST, annotated SECOND, clean THIRD — masks stay on for both):
//   1. evaluate(this file)
//   2. evaluate(() => { osbMaskMatching(/[\w.+-]+@[\w-]+\.[\w.-]+/); osbMask('img[src*="company_logo"]', { all: true }) })
//   3. evaluate(() => osbAnnotate(osbFind('Add activity'), { arrow: 'auto', label: 'Add activity', mark: 'A' }))
//   4. browser_take_screenshot  -> annotated-<...>.png
//   5. evaluate(() => osbAnnotateClear())
//   6. browser_take_screenshot  -> <...>.png        (clean sidecar, still masked)
//   7. act (click) and continue; re-apply masks if the DOM re-rendered
//
// Style is hard-coded red (#e01e28) to match the NeoDash guides and
// documentation_portal/docs/public/images/user_guides/neodash_elements_overview.png.
// Badges are LETTERS (A, B, C) — digits mean ordered steps in the guides.
//
// Positions are measured in document coordinates (viewport rect + scroll offset).
// Prefer VIEWPORT screenshots when a Vuetify dialog/menu is open: dialogs are
// position:fixed, so a fullPage capture can shift them relative to the overlay.

(() => {
  const NS = "http://www.w3.org/2000/svg";
  const ANN_ID = "osb-annotate-root";
  const MASK_ID = "osb-mask-root";
  const RED = "#e01e28";

  function docSize() {
    const d = document.documentElement;
    const b = document.body;
    return {
      w: Math.max(d.scrollWidth, b ? b.scrollWidth : 0, d.clientWidth),
      h: Math.max(d.scrollHeight, b ? b.scrollHeight : 0, d.clientHeight),
    };
  }

  function ensureRoot(id, withArrowhead) {
    let svg = document.getElementById(id);
    if (svg) return svg;
    const { w, h } = docSize();
    svg = document.createElementNS(NS, "svg");
    svg.id = id;
    svg.setAttribute("width", w);
    svg.setAttribute("height", h);
    Object.assign(svg.style, {
      position: "absolute",
      left: "0",
      top: "0",
      width: w + "px",
      height: h + "px",
      pointerEvents: "none",
      // masks sit below annotations so a call-out is never hidden by a cover
      zIndex: id === MASK_ID ? "2147483646" : "2147483647",
      overflow: "visible",
    });
    if (withArrowhead) {
      const defs = document.createElementNS(NS, "defs");
      const marker = document.createElementNS(NS, "marker");
      marker.setAttribute("id", "osb-arrowhead");
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
    }
    document.body.appendChild(svg);
    return svg;
  }

  function absRect(r) {
    const sx = window.scrollX || window.pageXOffset;
    const sy = window.scrollY || window.pageYOffset;
    return { left: r.left + sx, top: r.top + sy, width: r.width, height: r.height };
  }

  function resolve(target, who) {
    const el = typeof target === "string" ? document.querySelector(target) : target;
    if (!el || !(el instanceof Element)) {
      throw new Error(who + ": target not found: " + target);
    }
    return el;
  }

  function visible(el) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== "hidden" && cs.display !== "none";
  }

  // Public: osbFind(text, { within, selector, nth })
  //   Exact (trimmed, whitespace-collapsed, case-sensitive) match on the visible
  //   text, aria-label or title of a control. NEVER a substring match: the UI has
  //   siblings such as "Activities" / "Activity Instances" / "Activity Requests".
  //   Throws if nothing matches, or if several match and opts.nth is not given —
  //   an ambiguous box is a wrong box (see references/fail-loud.md).
  window.osbFind = function osbFind(text, opts = {}) {
    const scope = opts.within
      ? resolve(opts.within, "osbFind(within)")
      : document;
    const sel =
      opts.selector ||
      'button, a, [role="button"], [role="tab"], [role="menuitem"], [role="option"], label, th, .v-btn, .v-tab, .v-list-item, .v-label, .v-field__input, input, textarea, h1, h2, h3, h4';
    const norm = (s) => (s || "").replace(/\s+/g, " ").trim();
    const hits = [...scope.querySelectorAll(sel)].filter((el) => {
      if (!visible(el)) return false;
      return (
        norm(el.innerText || el.textContent) === text ||
        norm(el.getAttribute("aria-label")) === text ||
        norm(el.getAttribute("title")) === text ||
        norm(el.getAttribute("placeholder")) === text
      );
    });
    // an outer wrapper and its inner button both match; keep the innermost
    const inner = hits.filter((el) => !hits.some((o) => o !== el && el.contains(o)));
    if (inner.length === 0) throw new Error("osbFind: no visible control with exact text: " + text);
    if (opts.nth != null) return inner[opts.nth];
    if (inner.length > 1) {
      throw new Error("osbFind: " + inner.length + " controls match exactly '" + text + "' — pass { nth } or { within }");
    }
    return inner[0];
  }

  // Public: osbAnnotate(target, opts)
  //   target     : CSS selector string or a live Element (use osbFind for labels)
  //   opts.arrow : "auto" | {x, y}   arrow origin (document coordinates)
  //   opts.label : string            red callout text at the arrow origin
  //   opts.mark  : "A"               small letter badge on the box's top-left corner
  window.osbAnnotate = function osbAnnotate(target, opts = {}) {
    const svg = ensureRoot(ANN_ID, true);
    const el = resolve(target, "osbAnnotate");
    const b = absRect(el.getBoundingClientRect());

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

    if (opts.arrow) {
      let ox, oy;
      if (opts.arrow === "auto" || opts.arrow === true) {
        ox = Math.max(12, b.left - 140);
        oy = Math.max(12, b.top - 60);
      } else {
        ox = opts.arrow.x;
        oy = opts.arrow.y;
      }
      const line = document.createElementNS(NS, "line");
      line.setAttribute("x1", ox);
      line.setAttribute("y1", oy);
      line.setAttribute("x2", b.left);
      line.setAttribute("y2", b.top);
      line.setAttribute("stroke", RED);
      line.setAttribute("stroke-width", "3");
      line.setAttribute("marker-end", "url(#osb-arrowhead)");
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

    if (opts.mark != null) {
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
      t.textContent = String(opts.mark);
      svg.appendChild(t);
    }

    return b;
  };

  window.osbAnnotateClear = function osbAnnotateClear() {
    const svg = document.getElementById(ANN_ID);
    if (svg) svg.remove();
  };

  // Colour behind `el`: first ancestor with a non-transparent background, else white.
  function bgColor(el) {
    for (let e = el; e; e = e.parentElement) {
      const c = getComputedStyle(e).backgroundColor;
      const m = c.match(/rgba?\(([^)]+)\)/);
      if (m) {
        const p = m[1].split(",").map((x) => parseFloat(x));
        if (p.length < 4 || p[3] > 0.05) return "rgb(" + p[0] + "," + p[1] + "," + p[2] + ")";
      }
    }
    return "#ffffff";
  }

  function fillFor(el, fill) {
    return !fill || fill === "auto" ? bgColor(el) : fill;
  }

  function drawMask(svg, r, fill, pad) {
    const b = absRect(r);
    const rect = document.createElementNS(NS, "rect");
    rect.setAttribute("x", b.left - pad);
    rect.setAttribute("y", b.top - pad);
    rect.setAttribute("width", b.width + pad * 2);
    rect.setAttribute("height", b.height + pad * 2);
    rect.setAttribute("fill", fill);
    svg.appendChild(rect);
    return b;
  }

  // Public: osbMask(target, { fill, pad, all })
  //   Opaque cover over a sensitive element, painted in the colour of the background
  //   behind it so it blends in (fill: "auto", the default; pass a CSS colour to
  //   override): employee
  //   names/emails, sponsor (company) logo, study numbers, drug names. With { all: true } and
  //   a selector string, every matching element is covered.
  window.osbMask = function osbMask(target, opts = {}) {
    const svg = ensureRoot(MASK_ID, false);
    const pad = opts.pad != null ? opts.pad : 2;
    if (opts.all && typeof target === "string") {
      const els = [...document.querySelectorAll(target)].filter(visible);
      els.forEach((el) => drawMask(svg, el.getBoundingClientRect(), fillFor(el, opts.fill), pad));
      return els.length;
    }
    const el = resolve(target, "osbMask");
    return drawMask(svg, el.getBoundingClientRect(), fillFor(el, opts.fill), pad);
  };

  // Public: osbMaskMatching(regex, { within, fill, pad })
  //   Covers the exact text range of every visible text node matching `regex`
  //   (e.g. /[\w.+-]+@[\w-]+\.[\w.]+/ for emails, /\bSTUDY-\d+\b/ for study IDs).
  //   Returns the number of ranges covered — log it, 0 means the pattern missed.
  //   Does not see <input> values or text inside canvas/images: use osbMask().
  window.osbMaskMatching = function osbMaskMatching(regex, opts = {}) {
    const svg = ensureRoot(MASK_ID, false);
    const pad = opts.pad != null ? opts.pad : 2;
    const root = opts.within ? resolve(opts.within, "osbMaskMatching(within)") : document.body;
    const re = new RegExp(regex.source, regex.flags.includes("g") ? regex.flags : regex.flags + "g");
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let count = 0;
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.parentElement || !visible(n.parentElement)) continue;
      if (n.parentElement.closest("#" + MASK_ID + ", #" + ANN_ID)) continue;
      re.lastIndex = 0;
      let m;
      while ((m = re.exec(n.nodeValue))) {
        const range = document.createRange();
        range.setStart(n, m.index);
        range.setEnd(n, m.index + m[0].length);
        for (const r of range.getClientRects()) {
          if (r.width > 0 && r.height > 0) {
            drawMask(svg, r, fillFor(n.parentElement, opts.fill), pad);
            count++;
          }
        }
        if (m[0].length === 0) re.lastIndex++;
      }
    }
    return count;
  };

  window.osbMaskClear = function osbMaskClear() {
    const svg = document.getElementById(MASK_ID);
    if (svg) svg.remove();
  };
})();
