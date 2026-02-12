import { spawn } from "child_process";

const LABELLE_PATH = process.env.LABELLE_PATH || "labelle";

export interface RunResult {
  exitCode: number;
  stdout: string;
  stderr: string;
}

/**
 * Spawn the labelle CLI with the given arguments and optional stdin data.
 * Returns a promise that resolves with exit code, stdout, and stderr.
 */
export function runLabelle(
  args: string[],
  stdin?: string,
): Promise<RunResult> {
  return new Promise((resolve, reject) => {
    const proc = spawn(LABELLE_PATH, args);

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data: Buffer) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data: Buffer) => {
      stderr += data.toString();
    });

    proc.on("error", (err) => {
      reject(new Error(`Failed to start labelle: ${err.message}`));
    });

    proc.on("close", (code) => {
      resolve({ exitCode: code ?? 1, stdout, stderr });
    });

    if (stdin) {
      proc.stdin.write(stdin);
      proc.stdin.end();
    } else {
      proc.stdin.end();
    }
  });
}
