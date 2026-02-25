import { describe, it, expect, vi, beforeEach } from "vitest";
import { fetchPrinters } from "./api";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

describe("fetchPrinters", () => {
  it("returns printers from the API", async () => {
    const printers = [
      { id: "usb:1", name: "DYMO LabelWriter", vendorProductId: "0922:1002" },
      { id: "virtual:Office", name: "Office (Virtual)", vendorProductId: "virtual" },
    ];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ printers }),
    });

    const result = await fetchPrinters();
    expect(result).toEqual(printers);
    expect(mockFetch).toHaveBeenCalledWith("/api/printers");
  });

  it("returns empty array when no printers available", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ printers: [] }),
    });

    const result = await fetchPrinters();
    expect(result).toEqual([]);
  });

  it("throws on fetch error", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({ message: "Internal error" }),
    });

    await expect(fetchPrinters()).rejects.toThrow("Failed to fetch printers");
  });

  it("throws on network failure", async () => {
    mockFetch.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    await expect(fetchPrinters()).rejects.toThrow("Failed to fetch");
  });
});
