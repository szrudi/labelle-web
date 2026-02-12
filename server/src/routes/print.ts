import { Router } from "express";
import { buildBatchInput } from "../lib/batchBuilder.js";
import { buildArgs } from "../lib/argBuilder.js";
import { runLabelle } from "../lib/labelleRunner.js";

export const printRouter = Router();

printRouter.post("/", async (req, res) => {
  const { widgets, settings } = req.body;

  if (!widgets || !Array.isArray(widgets) || widgets.length === 0) {
    res.status(400).json({ status: "error", message: "No widgets provided" });
    return;
  }

  const batchInput = buildBatchInput(widgets);
  const firstText = widgets.find(
    (w: { type: string }) => w.type === "text",
  );
  const args = buildArgs(settings ?? {}, firstText ?? null);

  console.log(`[print] args: labelle ${args.join(" ")}`);
  console.log(`[print] stdin:\n${batchInput}`);

  try {
    const result = await runLabelle(args, batchInput);
    if (result.exitCode === 0) {
      res.json({ status: "success", message: "Label sent to printer." });
    } else {
      console.error(`[print] failed: ${result.stderr}`);
      res.status(500).json({
        status: "error",
        message: `Print failed (exit ${result.exitCode}): ${result.stderr}`,
      });
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[print] error: ${msg}`);
    res.status(500).json({ status: "error", message: msg });
  }
});
