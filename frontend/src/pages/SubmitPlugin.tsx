import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createSubmission } from "../api/client";
import type { PluginCategory, PluginSubmissionCreate } from "../types";

const CATEGORIES: { value: PluginCategory; label: string }[] = [
  { value: "lsp", label: "LSP (Language Server)" },
  { value: "mcp", label: "MCP (Model Context Protocol)" },
  { value: "tool", label: "Tool" },
  { value: "utility", label: "Utility" },
  { value: "other", label: "Other" },
];

export default function SubmitPlugin() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState<PluginSubmissionCreate>({
    submitter_name: "",
    submitter_email: "",
    source_url: "",
    proposed_category: "lsp",
    proposed_config: {},
  });
  const [configJson, setConfigJson] = useState("");

  const handleChange = (field: keyof PluginSubmissionCreate, value: string | PluginCategory | Record<string, unknown>) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleConfigChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setConfigJson(e.target.value);
    try {
      const parsed = e.target.value ? JSON.parse(e.target.value) : {};
      handleChange("proposed_config", parsed);
    } catch {
      // Invalid JSON, will show error on submit
    }
  };

  const validateForm = (): string | null => {
    if (!formData.submitter_name.trim()) return "Name is required";
    if (!formData.submitter_email.trim()) return "Email is required";
    if (!/^[^@]+@[^@]+\.[^@]+$/.test(formData.submitter_email)) return "Invalid email format";
    if (!formData.source_url.trim()) return "Source URL is required";
    try {
      new URL(formData.source_url);
    } catch {
      return "Source URL must be a valid URL";
    }
    if (configJson.trim()) {
      try {
        JSON.parse(configJson);
      } catch {
        return "Plugin configuration must be valid JSON";
      }
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await createSubmission(formData);
      setSuccess(true);
      setFormData({
        submitter_name: "",
        submitter_email: "",
        source_url: "",
        proposed_category: "lsp",
        proposed_config: {},
      });
      setConfigJson("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="card max-w-2xl mx-auto">
        <div className="p-6 text-center">
          <svg className="mx-auto h-12 w-12 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <h2 className="mt-4 text-xl font-semibold">Submission Received</h2>
          <p className="mt-2 text-muted">
            Thank you! Your plugin submission has been received and is pending review.
            You will be notified via email once the review is complete.
          </p>
          <button
            onClick={() => navigate("/")}
            className="btn mt-6"
          >
            Back to Marketplace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card max-w-2xl mx-auto">
      <h1 className="p-6 border-b">Submit a Plugin</h1>

      <form onSubmit={handleSubmit} className="p-6 space-y-6" noValidate>
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="submitter-name" className="label">Your Name</label>
          <input
            id="submitter-name"
            type="text"
            value={formData.submitter_name}
            onChange={(e) => handleChange("submitter_name", e.target.value)}
            className="input mt-1"
            placeholder="Your name"
            required
          />
        </div>

        <div>
          <label htmlFor="submitter-email" className="label">Your Email</label>
          <input
            id="submitter-email"
            type="email"
            value={formData.submitter_email}
            onChange={(e) => handleChange("submitter_email", e.target.value)}
            className="input mt-1"
            placeholder="you@example.com"
            required
          />
        </div>

        <div>
          <label htmlFor="source-url" className="label">Plugin Source URL</label>
          <input
            id="source-url"
            type="url"
            value={formData.source_url}
            onChange={(e) => handleChange("source_url", e.target.value)}
            className="input mt-1"
            placeholder="https://github.com/owner/repo"
            required
          />
          <p className="text-sm text-muted mt-1">
            The GitHub repository URL for the plugin. Must not already exist in the marketplace.
          </p>
        </div>

        <div>
          <label htmlFor="proposed-category" className="label">Category</label>
          <select
            id="proposed-category"
            value={formData.proposed_category}
            onChange={(e) => handleChange("proposed_category", e.target.value as PluginCategory)}
            className="input mt-1"
            required
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="config-json" className="label">Plugin Configuration (JSON, optional)</label>
          <textarea
            id="config-json"
            value={configJson}
            onChange={handleConfigChange}
            className="input mt-1 font-mono text-sm"
            rows={10}
            placeholder={JSON.stringify({
              name: "My Plugin",
              slug: "my-plugin",
              description: "A brief description",
              version: "1.0.0",
              author: "Your Name",
              tags: ["tag1", "tag2"],
              lspServers: {
                mylang: {
                  command: "my-language-server",
                  args: ["--stdio"],
                  extensionToLanguage: { ".ml": "mylang" },
                },
              },
            }, null, 2)}
          />
          <p className="text-sm text-muted mt-1">
            Optional <code>plugin.json</code> configuration. Include <code>lspServers</code> for LSP plugins.
            See <a href="/docs/plugin-config" className="underline" target="_blank" rel="noopener">documentation</a> for schema.
          </p>
        </div>

        <div className="flex gap-4 pt-4">
          <button type="submit" className="btn flex-1" disabled={loading}>
            {loading ? "Submitting..." : "Submit for Review"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="btn btn-outline flex-1"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}