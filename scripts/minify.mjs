import { readFile, readdir, writeFile } from "node:fs/promises";
import { extname, join } from "node:path";
import { transform } from "esbuild";
import { minify } from "html-minifier-terser";
import { optimize } from "svgo";

const root = process.argv[2];
const loaders = new Map([[".css", "css"], [".js", "js"], [".mjs", "js"]]);
let count = 0;
let savedBytes = 0;

for (const entry of await readdir(root, { recursive: true, withFileTypes: true })) {
  if (!entry.isFile()) continue;
  const extension = extname(entry.name);
  const loader = loaders.get(extension);
  if (!loader && extension !== ".html" && extension !== ".svg") continue;

  const path = join(entry.parentPath, entry.name);
  const source = await readFile(path, "utf8");
  let output;
  try {
    if (extension === ".html") {
      output = await minify(source, {
        collapseBooleanAttributes: true,
        collapseWhitespace: true,
        conservativeCollapse: true,
        minifyCSS: true,
        minifyJS: true,
        removeAttributeQuotes: true,
        removeComments: true,
      });
    } else if (extension === ".svg") {
      output = optimize(source, { path, floatPrecision: 6 }).data;
    } else {
      output = (await transform(source, {
        loader,
        sourcefile: path,
        legalComments: "inline",
        ...(loader === "css" ? { minifyWhitespace: true } : { minify: true }),
      })).code.trimEnd();
    }
  } catch (error) {
    throw new Error(`Could not minify ${path}`, { cause: error });
  }
  await writeFile(path, output);
  count++;
  savedBytes += Buffer.byteLength(source) - Buffer.byteLength(output);
}

console.log(`Minified ${count} HTML, CSS, JavaScript, and SVG files (${savedBytes} bytes saved)`);
