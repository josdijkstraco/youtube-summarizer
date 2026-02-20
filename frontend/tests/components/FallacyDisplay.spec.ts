import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import FallacyDisplay from "@/components/FallacyDisplay.vue";
import type { Fallacy } from "@/types";

const makeFallacy = (overrides: Partial<Fallacy> = {}): Fallacy => ({
  timestamp: null,
  quote: "You can't trust him",
  fallacy_name: "Ad Hominem",
  category: "Relevance",
  severity: "high",
  explanation: "Attacks the person rather than the argument.",
  clear_example: {
    scenario: "Dismissing a mechanic",
    why_wrong: "Expertise comes from experience",
  },
  ...overrides,
});

describe("FallacyDisplay", () => {
  it("renders fallacy cards with all fields", () => {
    const fallacy = makeFallacy();
    const wrapper = mount(FallacyDisplay, {
      props: { fallacies: [fallacy] },
    });

    expect(wrapper.find(".fallacy-card__quote").text()).toBe(fallacy.quote);
    expect(wrapper.find(".fallacy-card__name").text()).toBe(fallacy.fallacy_name);
    expect(wrapper.find(".fallacy-card__category").text()).toBe(fallacy.category);
    expect(wrapper.find(".fallacy-card__severity").text()).toBe("High");
    expect(wrapper.find(".fallacy-card__explanation").text()).toBe(
      fallacy.explanation,
    );
    expect(wrapper.find(".fallacy-card__example-scenario").text()).toBe(
      fallacy.clear_example.scenario,
    );
    expect(wrapper.find(".fallacy-card__example-why").text()).toBe(
      fallacy.clear_example.why_wrong,
    );
  });

  it("high-severity fallacy has CSS class fallacy-card--high", () => {
    const wrapper = mount(FallacyDisplay, {
      props: { fallacies: [makeFallacy({ severity: "high" })] },
    });

    expect(wrapper.find(".fallacy-card--high").exists()).toBe(true);
  });

  it("medium-severity fallacy has CSS class fallacy-card--medium", () => {
    const wrapper = mount(FallacyDisplay, {
      props: { fallacies: [makeFallacy({ severity: "medium" })] },
    });

    expect(wrapper.find(".fallacy-card--medium").exists()).toBe(true);
  });

  it("low-severity fallacy has CSS class fallacy-card--low", () => {
    const wrapper = mount(FallacyDisplay, {
      props: { fallacies: [makeFallacy({ severity: "low" })] },
    });

    expect(wrapper.find(".fallacy-card--low").exists()).toBe(true);
  });

  it('shows "No fallacies found" message when fallacies array is empty', () => {
    const wrapper = mount(FallacyDisplay, {
      props: { fallacies: [] },
    });

    expect(wrapper.find(".fallacy-display__empty").text()).toContain(
      "No fallacies found",
    );
    expect(wrapper.find(".fallacy-card").exists()).toBe(false);
  });

  it("renders multiple fallacies", () => {
    const fallacies = [
      makeFallacy({ severity: "high", fallacy_name: "Ad Hominem" }),
      makeFallacy({ severity: "medium", fallacy_name: "Straw Man" }),
      makeFallacy({ severity: "low", fallacy_name: "Slippery Slope" }),
    ];
    const wrapper = mount(FallacyDisplay, {
      props: { fallacies },
    });

    const cards = wrapper.findAll(".fallacy-card");
    expect(cards).toHaveLength(3);
    expect(wrapper.find(".fallacy-card--high").exists()).toBe(true);
    expect(wrapper.find(".fallacy-card--medium").exists()).toBe(true);
    expect(wrapper.find(".fallacy-card--low").exists()).toBe(true);
  });
});
