import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Badge } from "./Badge";

describe("Badge", () => {
    it("renders its children", () => {
        render(<Badge variant="gain">base</Badge>);
        expect(screen.getByText("base")).toBeInTheDocument();
    });
});