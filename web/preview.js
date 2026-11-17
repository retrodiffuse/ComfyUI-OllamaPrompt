import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NODE = "OllamaPromptPreview";
// ponytail: reuse the frontend's own PreviewAny widget; plain textarea if it ever moves
const core = () => window.comfyAPI?.textPreviewWidgets;

function addBox(node) {
  const c = core();
  if (c) return c.addTextPreviewWidgets(node);
  const w = ComfyWidgets.STRING(node, "text", ["STRING", { multiline: true }], app).widget;
  w.serialize = false;
  w.options.serialize = false;
}

function setText(node, message) {
  const c = core();
  if (c) return c.updateTextPreviewWidgets(node, message ?? {});
  const w = node.widgets?.find((w) => w.name === "text");
  if (w) w.value = [message?.text ?? ""].flat().join("\n\n");
}

app.registerExtension({
  name: "OllamaPrompt.Preview",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== NODE) return;
    const created = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      created?.apply(this, []);
      addBox(this);
    };
    const executed = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (message) {
      executed?.apply(this, [message]);
      setText(this, message);
    };
  },
  // keeps the text after a cached run or a workflow reload
  nodeOutputsUpdated(outputs) {
    for (const [id, output] of Object.entries(outputs ?? {})) {
      const node = app.graph?.getNodeById(Number(String(id).split(":").pop()));
      if (node?.type === NODE) setText(node, output);
    }
  },
});
console.log("[OllamaPrompt] preview extension loaded");
