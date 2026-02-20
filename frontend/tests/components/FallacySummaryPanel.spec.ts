import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import FallacySummaryPanel from "@/components/FallacySummaryPanel.vue";
import type { FallacySummary } from "@/types";

const makeSummary = (overrides: Partial<FallacySummary> = {}): FallacySummary => ({
  total_fallacies: 5,
  high_severity: 2,
  medium_severity: 2,
  low_severity: 1,
  primary_tactics: ["Ad Hominem", "Straw Man"],
  ...overrides,
});

describe("FallacySummaryPanel", () => {
  it("renders total fallacy count", () => {
    const wrapper = mount(FallacySummaryPanel, {
      props: { summary: makeSummary() },
    });

    expect(wrapper.text()).toContain("5");
  });

  it("renders high/medium/low severity counts", () => {
    const wrapper = mount(FallacySummaryPanel, {
      props: { summary: makeSummary() },
    });

    const text = wrapper.text();
    expect(text).toContain("2"); // high and medium
    expect(text).toContain("1"); // low
  });

  it("renders primary tactics as comma-separated list", () => {
    const wrapper = mount(FallacySummaryPanel, {
      props: { summary: makeSummary() },
    });

    expect(wrapper.text()).toContain("Ad Hominem");
    expect(wrapper.text()).toContain("Straw Man");
  });

  it("renders zero-state correctly", () => {
    const wrapper = mount(FallacySummaryPanel, {
      props: {
        summary: makeSummary({
          total_fallacies: 0,
          high_severity: 0,
          medium_severity: 0,
          low_severity: 0,
          primary_tactics: [],
        }),
      },
    });

    expect(wrapper.text()).toContain("0");
  });

  it("does not render when summary is null", () => {
    const wrapper = mount(FallacySummaryPanel, {
      props: { summary: null },
    });

    expect(wrapper.find(".fallacy-summary-panel").exists()).toBe(false);
  });
});
