import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import { printRouter } from "./routes/print.js";
import { previewRouter } from "./routes/preview.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = Number(process.env.PORT) || 5000;

app.use(cors());
app.use(express.json());

app.use("/api/print", printRouter);
app.use("/api/preview", previewRouter);

// Serve static client build in production
const clientDist = path.resolve(__dirname, "../dist-client");
app.use(express.static(clientDist));
app.get("*", (_req, res) => {
  res.sendFile(path.join(clientDist, "index.html"));
});

app.listen(PORT, () => {
  console.log(`Labelle server running at http://0.0.0.0:${PORT}`);
});
