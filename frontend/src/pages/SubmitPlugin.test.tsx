import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import SubmitPlugin from "./SubmitPlugin";
import * as api from "../api/client";

describe("SubmitPlugin page", () => {
  beforeEach(() => {
    vi.spyOn(api, "createSubmission").mockResolvedValue({
      id: 1,
      plugin_id: null,
      submitter_name: "Test User",
      submitter_email: "test@example.com",
      source_url: "https://github.com/test/plugin",
      proposed_category: "lsp",
      proposed_config: {},
      status: "pending",
      reviewer_notes: null,
      reviewed_at: null,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders submission form with all fields", () => {
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    expect(screen.getByLabelText("Your Name")).toBeDefined();
    expect(screen.getByLabelText("Your Email")).toBeDefined();
    expect(screen.getByLabelText("Plugin Source URL")).toBeDefined();
    expect(screen.getByLabelText("Category")).toBeDefined();
    expect(screen.getByLabelText("Plugin Configuration (JSON, optional)")).toBeDefined();
    expect(screen.getByRole("button", { name: "Submit for Review" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDefined();
  });

  it("shows validation error for missing required fields", async () => {
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole("button", { name: "Submit for Review" }));

    await waitFor(() => {
      expect(screen.getByText("Name is required")).toBeDefined();
    });
  });

  it("shows validation error for invalid email", async () => {
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText("Your Name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Your Email"), { target: { value: "invalid-email" } });
    fireEvent.change(screen.getByLabelText("Plugin Source URL"), { target: { value: "https://github.com/test/plugin" } });

    fireEvent.click(screen.getByRole("button", { name: "Submit for Review" }));

    await waitFor(() => {
      expect(screen.getByText("Invalid email format")).toBeDefined();
    });
  });

  it("shows validation error for invalid URL", async () => {
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText("Your Name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Your Email"), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText("Plugin Source URL"), { target: { value: "not-a-url" } });

    fireEvent.click(screen.getByRole("button", { name: "Submit for Review" }));

    await waitFor(() => {
      expect(screen.getByText("Source URL must be a valid URL")).toBeDefined();
    });
  });

  it("shows validation error for invalid JSON config", async () => {
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText("Your Name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Your Email"), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText("Plugin Source URL"), { target: { value: "https://github.com/test/plugin" } });
    fireEvent.change(screen.getByLabelText("Plugin Configuration (JSON, optional)"), { target: { value: "{ invalid json" } });

    fireEvent.click(screen.getByRole("button", { name: "Submit for Review" }));

    await waitFor(() => {
      expect(screen.getByText("Plugin configuration must be valid JSON")).toBeDefined();
    });
  });

  it("submits form successfully and shows success state", async () => {
    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText("Your Name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Your Email"), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText("Plugin Source URL"), { target: { value: "https://github.com/test/plugin" } });

    fireEvent.click(screen.getByRole("button", { name: "Submit for Review" }));

    await waitFor(() => {
      expect(screen.getByText("Submission Received")).toBeDefined();
    });

    expect(screen.getByText(/plugin submission has been received and is pending review/i)).toBeDefined();
    expect(api.createSubmission).toHaveBeenCalledWith(
      expect.objectContaining({
        submitter_name: "Test User",
        submitter_email: "test@example.com",
        source_url: "https://github.com/test/plugin",
        proposed_category: "lsp",
      })
    );
  });

  it("shows API error when submission fails", async () => {
    vi.spyOn(api, "createSubmission").mockRejectedValue(new Error("HTTP 409: A plugin with this source URL already exists"));

    render(
      <MemoryRouter initialEntries={["/submit"]}>
        <SubmitPlugin />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText("Your Name"), { target: { value: "Test User" } });
    fireEvent.change(screen.getByLabelText("Your Email"), { target: { value: "test@example.com" } });
    fireEvent.change(screen.getByLabelText("Plugin Source URL"), { target: { value: "https://github.com/test/plugin" } });

    fireEvent.click(screen.getByRole("button", { name: "Submit for Review" }));

    await waitFor(() => {
      expect(screen.getByText("HTTP 409: A plugin with this source URL already exists")).toBeDefined();
    });
  });
});