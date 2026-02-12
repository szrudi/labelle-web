import { Router } from "express";
import { buildBatchInput } from "../lib/batchBuilder.js";
import { buildArgs } from "../lib/argBuilder.js";
import { runLabelle } from "../lib/labelleRunner.js";
import fs from "fs";
import path from "path";
import os from "os";

export const previewRouter = Router();

previewRouter.post("/", async (req, res) => {
  const { widgets, settings } = req.body;

  if (!widgets || !Array.isArray(widgets) || widgets.length === 0) {
    res.status(400).json({ status: "error", message: "No widgets provided" });
    return;
  }

  // Create a temp directory for the PNG output
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "labelle-preview-"));
  const outputPath = path.join(tmpDir, "output.png");

  try {
    const batchInput = buildBatchInput(widgets);
    const firstText = widgets.find(
      (w: { type: string }) => w.type === "text",
    );
    const args = buildArgs(settings ?? {}, firstText ?? null, "png");

    // labelle --output png writes to ./output.png in cwd
    const result = await runLabelle(args, batchInput);

    if (result.exitCode !== 0) {
      res.status(500).json({
        status: "error",
        message: `Preview failed (exit ${result.exitCode}): ${result.stderr}`,
      });
      return;
    }

    // The labelle CLI writes output.png to cwd; try both cwd and tmpDir
    const possiblePaths = [
      outputPath,
      path.join(process.cwd(), "output.png"),
    ];
    const pngPath = possiblePaths.find((p) => fs.existsSync(p));

    if (!pngPath) {
      res.status(500).json({
        status: "error",
        message: "Preview PNG not found after rendering",
      });
      return;
    }

    const png = fs.readFileSync(pngPath);
    fs.unlinkSync(pngPath);
    res.setHeader("Content-Type", "image/png");
    res.send(png);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(500).json({ status: "error", message: msg });
  } finally {
    // Clean up temp dir
    try {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    } catch {
      // ignore cleanup errors
    }
  }
});
