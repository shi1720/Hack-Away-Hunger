// Include finalized, non-sensitive presentation assets when they are available.
// Local development builds remain usable before the submission media is created.
import { copyFile, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const root = new URL("./", import.meta.url);
for (const name of [
  "Pantry-Relay-Demo.mp4",
  "Pantry-Relay-Pitch.pdf",
  "Pantry-Relay-Brief.pdf",
  "Pantry-Relay-Captions.srt",
]) {
  const source = new URL(`../output/${name}`, root);
  try {
    await access(source);
  } catch {
    continue;
  }
  await copyFile(source, new URL(`dist/${name}`, root));
  console.log(`Published asset: ${fileURLToPath(source).split("/").pop()}`);
}
