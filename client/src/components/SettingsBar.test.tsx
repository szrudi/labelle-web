import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SettingsBar } from "./SettingsBar";
import { useLabelStore } from "../state/useLabelStore";
import type { PrinterInfo } from "../types/label";

const twoPrinters: PrinterInfo[] = [
  { id: "usb:1", name: "DYMO LabelWriter 450", vendorProductId: "0922:1002" },
  { id: "virtual:Office", name: "Office (Virtual)", vendorProductId: "virtual" },
];

afterEach(() => {
  cleanup();
});

beforeEach(() => {
  // Reset store to defaults
  useLabelStore.setState({
    availablePrinters: [],
    settings: {
      tapeSizeMm: 12,
      marginPx: 56,
      minLengthMm: 0,
      justify: "center",
      foregroundColor: "black",
      backgroundColor: "white",
      showMargins: false,
    },
  });
});

describe("SettingsBar printer selector", () => {
  it("shows printer selector when multiple printers available", () => {
    useLabelStore.setState({ availablePrinters: twoPrinters });
    render(<SettingsBar />);

    // Open the details
    screen.getByText("Settings").click();

    expect(screen.getByText("Printer")).toBeInTheDocument();
    expect(screen.getByText("Auto-select")).toBeInTheDocument();
  });

  it("hides printer selector when 0 printers", () => {
    useLabelStore.setState({ availablePrinters: [] });
    render(<SettingsBar />);

    screen.getByText("Settings").click();

    expect(screen.queryByText("Printer")).not.toBeInTheDocument();
  });

  it("hides printer selector when only 1 printer", () => {
    useLabelStore.setState({ availablePrinters: [twoPrinters[0]!] });
    render(<SettingsBar />);

    screen.getByText("Settings").click();

    expect(screen.queryByText("Printer")).not.toBeInTheDocument();
  });

  it("lists all printers plus Auto-select", () => {
    useLabelStore.setState({ availablePrinters: twoPrinters });
    render(<SettingsBar />);

    screen.getByText("Settings").click();

    const select = screen.getByDisplayValue("Auto-select");
    const options = select.querySelectorAll("option");

    // Auto-select + 2 printers = 3 options
    expect(options).toHaveLength(3);
    expect(options[0]!.textContent).toBe("Auto-select");
    expect(options[1]!.textContent).toBe("DYMO LabelWriter 450");
    expect(options[2]!.textContent).toBe("Office (Virtual)");
  });

  it("selecting a printer updates the store", async () => {
    useLabelStore.setState({ availablePrinters: twoPrinters });
    render(<SettingsBar />);

    screen.getByText("Settings").click();

    const select = screen.getByDisplayValue("Auto-select");
    await userEvent.selectOptions(select, "virtual:Office");

    expect(useLabelStore.getState().settings.printerId).toBe("virtual:Office");
  });

  it("selecting Auto-select clears printerId", async () => {
    useLabelStore.setState({
      availablePrinters: twoPrinters,
      settings: {
        ...useLabelStore.getState().settings,
        printerId: "usb:1",
      },
    });
    render(<SettingsBar />);

    screen.getByText("Settings").click();

    const select = screen.getByDisplayValue("DYMO LabelWriter 450");
    await userEvent.selectOptions(select, "");

    expect(useLabelStore.getState().settings.printerId).toBeUndefined();
  });
});
