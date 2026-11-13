import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { minify } from "terser";

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
const vexflowSource = join("node_modules", "vexflow", "build", "cjs", "vexflow.js");
copyFileSync(vexflowSource, join(vendorDirectory, "vexflow-4.2.5.js"));
const minifiedVexflow = await minify(readFileSync(vexflowSource, "utf8"), {
  compress: true,
  mangle: true,
  format: { comments: /^!/ },
});
if (!minifiedVexflow.code) throw new Error("Terser did not produce the VexFlow bundle.");
writeFileSync(
  join(vendorDirectory, "vexflow-4.2.5.min.js"),
  `${minifiedVexflow.code}\n`,
);
