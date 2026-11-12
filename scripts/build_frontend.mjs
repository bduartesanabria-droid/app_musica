import { copyFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const vendorDirectory = join("app", "static", "vendor");
mkdirSync(vendorDirectory, { recursive: true });

copyFileSync(
  join("node_modules", "alpinejs", "dist", "cdn.min.js"),
  join(vendorDirectory, "alpine-3.14.9.min.js"),
);
copyFileSync(
  join("node_modules", "chart.js", "dist", "chart.umd.js"),
  join(vendorDirectory, "chart-4.4.9.umd.js"),
);
// VexFlow 4.2.5 (build UMD): expone el global `Vex` al cargarse con <script>.
// Se usa para el renderizado de partituras (app/static/js/score_renderer.js).
copyFileSync(
  join("node_modules", "vexflow", "build", "cjs", "vexflow.js"),
  join(vendorDirectory, "vexflow-4.2.5.js"),
);
